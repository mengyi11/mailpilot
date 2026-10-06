const EMAIL_CSP = [
  "default-src 'none'",
  "script-src 'none'",
  "style-src 'unsafe-inline' https:",
  "img-src https: http: data:",
  "font-src https: data:",
  "media-src https: http:",
  "connect-src 'none'",
  "frame-src 'none'",
  "object-src 'none'",
  "form-action 'none'",
  "base-uri 'none'",
].join("; ");

function createSafeEmailDocument(html: string) {
  return `<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta http-equiv="Content-Security-Policy" content="${EMAIL_CSP}" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <base target="_blank" />
    <style>
      :root { color-scheme: light; }
      html, body { min-height: 100%; }
      body { margin: 0; overflow-wrap: anywhere; }
      img { max-width: 100%; height: auto; }
      table { max-width: 100%; }
    </style>
  </head>
  <body>${html}</body>
</html>`;
}

export function HtmlEmailBody({
  html,
  title,
}: {
  html: string;
  title: string;
}) {
  return (
    <iframe
      title={`邮件原文：${title}`}
      srcDoc={createSafeEmailDocument(html)}
      sandbox="allow-popups allow-popups-to-escape-sandbox"
      referrerPolicy="no-referrer"
      className="h-full min-h-[560px] w-full border-0 bg-white"
    />
  );
}
