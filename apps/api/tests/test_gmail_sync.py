import base64

from app.services.gmail_sync import parse_gmail_message


def _encoded(value: str) -> str:
    return base64.urlsafe_b64encode(value.encode()).decode().rstrip("=")


def test_parse_multipart_gmail_message_and_attachment_metadata() -> None:
    message = {
        "id": "message-1",
        "threadId": "thread-1",
        "internalDate": "1791200000000",
        "snippet": "Preview",
        "labelIds": ["INBOX", "UNREAD", "STARRED"],
        "historyId": "12345",
        "sizeEstimate": 900,
        "payload": {
            "mimeType": "multipart/mixed",
            "headers": [
                {"name": "From", "value": "Alice <alice@example.com>"},
                {"name": "To", "value": "Bob <bob@example.com>"},
                {"name": "Subject", "value": "Sync test"},
                {"name": "Message-ID", "value": "<message@example.com>"},
            ],
            "parts": [
                {
                    "mimeType": "text/plain",
                    "body": {"data": _encoded("Hello from Gmail")},
                },
                {
                    "mimeType": "text/html",
                    "body": {"data": _encoded("<p>Hello <b>from Gmail</b></p>")},
                },
                {
                    "mimeType": "application/pdf",
                    "filename": "brief.pdf",
                    "headers": [
                        {"name": "Content-Disposition", "value": "attachment"}
                    ],
                    "body": {"attachmentId": "attachment-1", "size": 42},
                },
            ],
        },
    }

    parsed = parse_gmail_message(message)

    assert parsed.provider_message_id == "message-1"
    assert parsed.provider_thread_id == "thread-1"
    assert parsed.sender == {"name": "Alice", "email": "alice@example.com"}
    assert parsed.recipients["to"][0]["email"] == "bob@example.com"
    assert parsed.body_text == "Hello from Gmail"
    assert parsed.body_html == "<p>Hello <b>from Gmail</b></p>"
    assert parsed.is_read is False
    assert parsed.is_starred is True
    assert parsed.attachments[0].provider_attachment_id == "attachment-1"
    assert parsed.attachments[0].filename == "brief.pdf"


def test_html_only_message_gets_safe_text_fallback() -> None:
    message = {
        "id": "message-2",
        "threadId": "thread-2",
        "internalDate": "1791200000000",
        "snippet": "Fallback",
        "labelIds": ["INBOX"],
        "payload": {
            "mimeType": "text/html",
            "headers": [
                {"name": "From", "value": "sender@example.com"},
                {"name": "Subject", "value": "HTML only"},
            ],
            "body": {"data": _encoded("<h1>Heading</h1><p>Body text</p>")},
        },
    }

    parsed = parse_gmail_message(message)

    assert "Heading" in parsed.body_text
    assert "Body text" in parsed.body_text


def test_html_text_fallback_ignores_css_and_script_content() -> None:
    message = {
        "id": "message-3",
        "threadId": "thread-3",
        "internalDate": "1791200000000",
        "snippet": "Fallback",
        "labelIds": ["INBOX"],
        "payload": {
            "mimeType": "text/html",
            "headers": [
                {"name": "From", "value": "sender@example.com"},
                {"name": "Subject", "value": "HTML with styles"},
            ],
            "body": {
                "data": _encoded(
                    "<html><head><style>body { margin: 0; }</style></head>"
                    "<body><script>alert('no')</script>"
                    "<h1>Visible title</h1><p>Visible body</p></body></html>"
                )
            },
        },
    }

    parsed = parse_gmail_message(message)

    assert "margin" not in parsed.body_text
    assert "alert" not in parsed.body_text
    assert parsed.body_text == "Visible title\nVisible body"
