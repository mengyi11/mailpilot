import io
import re
import zipfile
from dataclasses import dataclass, field
from datetime import datetime
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from typing import BinaryIO
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import bleach
from bleach.css_sanitizer import CSSSanitizer
from docx import Document
from pypdf import PdfReader


ALLOWED_ATTACHMENT_TYPES = {
    "text/plain",
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}

ALLOWED_HTML_TAGS = {
    "a", "b", "blockquote", "br", "code", "div", "em", "h1", "h2", "h3",
    "h4", "h5", "h6", "hr", "i", "img", "li", "ol", "p", "pre", "span",
    "strong", "style", "table", "tbody", "td", "th", "thead", "tr", "u", "ul",
}
ALLOWED_HTML_ATTRIBUTES = {
    "*": ["align", "class", "dir", "height", "lang", "style", "title", "width"],
    "a": ["href", "title"],
    "img": ["alt", "src", "title", "width", "height"],
    "td": ["colspan", "rowspan"],
    "th": ["colspan", "rowspan"],
}
CSS_SANITIZER = CSSSanitizer(
    allowed_css_properties={
        *CSSSanitizer().allowed_css_properties,
        "background-color", "border", "border-bottom", "border-collapse",
        "border-color", "border-left", "border-radius", "border-right",
        "border-spacing", "border-style", "border-top", "border-width",
        "box-sizing", "display", "font-family", "font-size", "font-style",
        "font-weight", "height", "letter-spacing", "line-height", "margin",
        "margin-bottom", "margin-left", "margin-right", "margin-top", "max-width",
        "min-width", "padding", "padding-bottom", "padding-left", "padding-right",
        "padding-top", "text-align", "text-decoration", "vertical-align", "white-space",
        "width", "word-break", "word-spacing", "word-wrap",
    }
)

_QUOTED_REPLY_PATTERNS = (
    re.compile(r"^On .+wrote:\s*$", re.IGNORECASE),
    re.compile(r"^-{2,}\s*Original Message\s*-{2,}$", re.IGNORECASE),
    re.compile(r"^From:\s+.+$", re.IGNORECASE),
    re.compile(r"^在.+写道[：:]\s*$"),
)
_SIGNATURE_MARKERS = (
    re.compile(r"^--\s*$"),
    re.compile(r"^(kind|best|warm) regards[,]?\s*$", re.IGNORECASE),
    re.compile(r"^(thanks|thank you)[,!]?\s*$", re.IGNORECASE),
    re.compile(r"^sent from my .+$", re.IGNORECASE),
)
_DISCLAIMER_MARKERS = (
    re.compile(r"^confidentiality:\s*", re.IGNORECASE),
    re.compile(r"^this (email|message) (and any attachments )?is intended", re.IGNORECASE),
    re.compile(r"^免责声明[：:]?"),
)


class _ReadableHTMLParser(HTMLParser):
    BLOCK_TAGS = {
        "blockquote", "br", "div", "h1", "h2", "h3", "h4", "h5", "h6",
        "hr", "li", "ol", "p", "pre", "table", "tr", "ul",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._ignored_depth = 0
        self._link_stack: list[str | None] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lowered = tag.lower()
        if lowered in {"head", "script", "style", "title"}:
            self._ignored_depth += 1
        elif lowered in self.BLOCK_TAGS and not self._ignored_depth:
            self.parts.append("\n")
        elif lowered == "a" and not self._ignored_depth:
            href = dict(attrs).get("href")
            self._link_stack.append(href)

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.lower()
        if lowered in {"head", "script", "style", "title"}:
            self._ignored_depth = max(0, self._ignored_depth - 1)
        elif lowered in self.BLOCK_TAGS and not self._ignored_depth:
            self.parts.append("\n")
        elif lowered == "a" and not self._ignored_depth:
            href = self._link_stack.pop() if self._link_stack else None
            if href:
                self.parts.append(f" ({href})")

    def handle_data(self, data: str) -> None:
        if not self._ignored_depth:
            self.parts.append(data)

    def text(self) -> str:
        return normalize_whitespace(unescape("".join(self.parts)))


@dataclass(frozen=True)
class ProcessedEmailContent:
    safe_html: str | None
    plain_text: str
    cleaned_text: str
    reference_date: str
    original_timezone: str
    user_timezone: str
    removed_sections: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class AttachmentExtraction:
    status: str
    extracted_text: str | None = None
    error: str | None = None


def normalize_whitespace(value: str) -> str:
    value = value.replace("\r\n", "\n").replace("\r", "\n").replace("\u00a0", " ")
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r" *\n *", "\n", value)
    return re.sub(r"\n{3,}", "\n\n", value).strip()


def html_to_text(value: str) -> str:
    parser = _ReadableHTMLParser()
    parser.feed(value)
    return parser.text()


def _remove_tracking_image(match: re.Match[str]) -> str:
    tag = match.group(0)
    width_match = re.search(r"\bwidth=[\"']?(\d+)", tag, flags=re.IGNORECASE)
    height_match = re.search(r"\bheight=[\"']?(\d+)", tag, flags=re.IGNORECASE)
    style_match = re.search(r"\bstyle=[\"']([^\"']*)", tag, flags=re.IGNORECASE)
    width = int(width_match.group(1)) if width_match else None
    height = int(height_match.group(1)) if height_match else None
    style = style_match.group(1).replace(" ", "").lower() if style_match else ""

    is_tiny = (
        width is not None
        and height is not None
        and width <= 2
        and height <= 2
    )
    is_hidden = "display:none" in style or "visibility:hidden" in style
    return "" if is_tiny or is_hidden else tag


def sanitize_email_html(value: str) -> str:
    # Remote images can be tracking pixels. cid: images stay usable for a future
    # authenticated attachment renderer; http(s) image sources are removed.
    value = re.sub(
        r"url\(\s*[\"']?https?://[^)]+\)", "none", value, flags=re.IGNORECASE
    )
    value = re.sub(
        r"<img\b[^>]*>", _remove_tracking_image, value, flags=re.IGNORECASE
    )
    cleaned = bleach.clean(
        value,
        tags=ALLOWED_HTML_TAGS,
        attributes=ALLOWED_HTML_ATTRIBUTES,
        protocols={"http", "https", "mailto", "cid"},
        css_sanitizer=CSS_SANITIZER,
        strip=True,
        strip_comments=True,
    )
    return cleaned.strip()


def remove_quoted_history_and_noise(value: str) -> tuple[str, list[str]]:
    lines = normalize_whitespace(value).splitlines()
    kept: list[str] = []
    removed: list[str] = []
    cut_reason: str | None = None

    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith(">"):
            cut_reason = "quoted_history"
        elif any(pattern.match(stripped) for pattern in _QUOTED_REPLY_PATTERNS):
            cut_reason = "quoted_history"
        elif any(pattern.match(stripped) for pattern in _DISCLAIMER_MARKERS):
            cut_reason = "disclaimer"
        elif any(pattern.match(stripped) for pattern in _SIGNATURE_MARKERS):
            # Only treat a marker in the latter part as a signature. This avoids
            # deleting a short message that begins with “Thanks”.
            if index >= max(1, len(lines) // 3):
                cut_reason = "signature"

        if cut_reason:
            removed.append(cut_reason)
            break
        kept.append(line)

    result = normalize_whitespace("\n".join(kept))
    return (result or normalize_whitespace(value), list(dict.fromkeys(removed)))


def _timezone_name(value: datetime) -> str:
    zone = value.tzinfo
    return getattr(zone, "key", None) or value.tzname() or "UTC"


def process_email_content(
    *,
    body_html: str | None,
    body_text: str | None,
    sent_at: datetime,
    user_timezone: str,
) -> ProcessedEmailContent:
    try:
        target_zone = ZoneInfo(user_timezone)
    except ZoneInfoNotFoundError:
        target_zone = ZoneInfo("UTC")
        user_timezone = "UTC"

    safe_html = sanitize_email_html(body_html) if body_html else None
    plain_text = normalize_whitespace(body_text or "")
    if not plain_text and body_html:
        plain_text = html_to_text(body_html)
    cleaned_text, removed = remove_quoted_history_and_noise(plain_text)
    localized = sent_at.astimezone(target_zone)

    return ProcessedEmailContent(
        safe_html=safe_html,
        plain_text=plain_text,
        cleaned_text=cleaned_text,
        reference_date=localized.date().isoformat(),
        original_timezone=_timezone_name(sent_at),
        user_timezone=user_timezone,
        removed_sections=removed,
    )


def _read_pdf(stream: BinaryIO) -> str:
    reader = PdfReader(stream)
    return "\n\n".join(page.extract_text() or "" for page in reader.pages)


def _read_docx(stream: BinaryIO) -> str:
    document = Document(stream)
    paragraphs = [paragraph.text for paragraph in document.paragraphs]
    for table in document.tables:
        for row in table.rows:
            paragraphs.append("\t".join(cell.text for cell in row.cells))
    return "\n".join(paragraphs)


def extract_attachment_text(
    *,
    content: bytes,
    filename: str,
    mime_type: str | None,
    max_size_bytes: int,
) -> AttachmentExtraction:
    if len(content) > max_size_bytes:
        return AttachmentExtraction(status="too_large", error="attachment_size_limit")
    if mime_type not in ALLOWED_ATTACHMENT_TYPES:
        return AttachmentExtraction(status="unsupported", error="attachment_type_not_allowed")

    if mime_type == "application/pdf" and not content.lstrip().startswith(b"%PDF-"):
        return AttachmentExtraction(status="failed", error="attachment_content_mismatch")
    if mime_type == "text/plain" and b"\x00" in content[:4096]:
        return AttachmentExtraction(status="failed", error="attachment_content_mismatch")
    if mime_type and mime_type.endswith("wordprocessingml.document"):
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                names = set(archive.namelist())
            if "[Content_Types].xml" not in names or "word/document.xml" not in names:
                raise zipfile.BadZipFile
        except zipfile.BadZipFile:
            return AttachmentExtraction(
                status="failed", error="attachment_content_mismatch"
            )

    try:
        stream = io.BytesIO(content)
        if mime_type == "text/plain":
            text = content.decode("utf-8", errors="replace")
        elif mime_type == "application/pdf":
            text = _read_pdf(stream)
        else:
            text = _read_docx(stream)
        return AttachmentExtraction(
            status="extracted",
            extracted_text=normalize_whitespace(text),
        )
    except Exception as exc:  # damaged documents must not abort Gmail sync
        return AttachmentExtraction(
            status="failed",
            error=f"{Path(filename).suffix.lower() or 'file'}_parse_failed:{type(exc).__name__}",
        )


def build_ai_input(
    *,
    subject: str,
    sender: dict[str, str],
    recipients: dict[str, list[dict[str, str]]],
    cleaned_text: str,
    sent_at: datetime,
    reference_date: str,
    user_timezone: str,
    attachments: list[dict[str, str | None]],
) -> dict[str, object]:
    """Build the only email payload that should cross into Dify/LLM prompts."""
    return {
        "subject": subject,
        "sender": sender,
        "recipients": recipients,
        "content": cleaned_text,
        "sent_at": sent_at.isoformat(),
        "reference_date": reference_date,
        "user_timezone": user_timezone,
        "attachments": [
            {
                "filename": item["filename"],
                "mime_type": item["mime_type"],
                "content": item["extracted_text"],
            }
            for item in attachments
            if item.get("extraction_status") == "extracted"
            and item.get("extracted_text")
        ],
    }
