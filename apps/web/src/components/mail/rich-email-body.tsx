import type { ReactNode } from "react";

const emphasisPattern =
  /(Gemini Enterprise|A Study on Group Dynamics|80 minutes|S\$3|S\$15|8-minute|企业数据保护|群体动力学研究|80分钟|3新元|15新元)/gi;

function renderInlineContent(text: string): ReactNode[] {
  const urlPattern = /(https?:\/\/[^\s]+)/g;

  return text.split(urlPattern).flatMap((part, partIndex) => {
    if (part.match(/^https?:\/\//)) {
      return (
        <a
          key={`link-${partIndex}`}
          href={part}
          target="_blank"
          rel="noreferrer"
          className="text-primary decoration-primary/35 hover:decoration-primary font-medium underline underline-offset-4"
        >
          {part}
        </a>
      );
    }

    return part.split(emphasisPattern).map((segment, segmentIndex) =>
      segment.match(emphasisPattern) ? (
        <strong
          key={`strong-${partIndex}-${segmentIndex}`}
          className="text-foreground font-semibold"
        >
          {segment}
        </strong>
      ) : (
        segment
      ),
    );
  });
}

function isSectionHeading(line: string) {
  const trimmed = line.trim();

  return (
    trimmed.length <= 72 &&
    (trimmed.endsWith(":") ||
      trimmed.endsWith("：") ||
      trimmed.endsWith("?") ||
      trimmed.endsWith("？") ||
      /^(Why Use|Want to Learn|Google AI Essentials|AI Boost Bites|Student Launchpad)/i.test(
        trimmed,
      ) ||
      /^\d{1,2}(st|nd|rd|th)\s.+:$/.test(trimmed) ||
      /^(更多学习资源|可选时间)/.test(trimmed))
  );
}

export function RichEmailBody({ content }: { content: string }) {
  const lines = content.split("\n");

  return (
    <div className="space-y-0 font-sans">
      {lines.map((rawLine, index) => {
        const line = rawLine.trim();

        if (!line) {
          return (
            <div key={`space-${index}`} className="h-4" aria-hidden="true" />
          );
        }

        const numberedItem = line.match(/^(\d+)\.\s+(.+)$/);

        if (numberedItem) {
          return (
            <div
              key={`list-${index}`}
              className="grid grid-cols-[1.5rem_1fr] gap-1.5 py-0.5 text-sm leading-6"
            >
              <span className="text-muted-foreground font-medium">
                {numberedItem[1]}.
              </span>
              <span>{renderInlineContent(numberedItem[2])}</span>
            </div>
          );
        }

        if (isSectionHeading(line)) {
          return (
            <h4
              key={`heading-${index}`}
              className="text-foreground pt-2 text-base leading-7 font-semibold"
            >
              {renderInlineContent(line)}
            </h4>
          );
        }

        if (line.startsWith("(") && line.endsWith(")")) {
          return (
            <p
              key={`note-${index}`}
              className="text-muted-foreground border-l-primary/40 border-l-2 pl-3 text-xs leading-6 italic"
            >
              {renderInlineContent(line)}
            </p>
          );
        }

        return (
          <p key={`paragraph-${index}`} className="text-sm leading-7">
            {renderInlineContent(line)}
          </p>
        );
      })}
    </div>
  );
}
