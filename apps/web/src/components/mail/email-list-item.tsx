import { Star } from "lucide-react";

import { cn } from "@/lib/utils";
import type { EmailSummary } from "@/types/email";

type EmailListItemProps = {
  email: EmailSummary;
  selected: boolean;
  onSelect: (emailId: string) => void;
};

function formatReceivedAt(value: string) {
  return new Intl.DateTimeFormat("zh-CN", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

export function EmailListItem({
  email,
  selected,
  onSelect,
}: EmailListItemProps) {
  return (
    <button
      type="button"
      onClick={() => onSelect(email.id)}
      aria-pressed={selected}
      className={cn(
        "border-border w-full border-b px-3 py-2.5 text-left transition-colors last:border-b-0",
        selected ? "bg-primary/10" : "bg-card hover:bg-muted/60",
      )}
    >
      <div className="flex items-start gap-2.5">
        <span
          className={cn(
            "mt-1.5 size-1.5 shrink-0 rounded-full",
            email.isRead ? "bg-transparent" : "bg-amber-500",
          )}
          aria-label={email.isRead ? "已读" : "未读"}
        />
        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between gap-3">
            <p
              className={cn(
                "truncate text-xs",
                email.isRead
                  ? "text-foreground/75 font-medium"
                  : "font-semibold",
              )}
            >
              {email.sender.name}
            </p>
            <time
              dateTime={email.receivedAt}
              className="text-muted-foreground shrink-0 text-[10px]"
            >
              {formatReceivedAt(email.receivedAt)}
            </time>
          </div>
          <div className="mt-0.5 flex items-center gap-2">
            <p className="truncate text-xs font-medium">{email.subject}</p>
            {email.isStarred ? (
              <Star
                className="size-3.5 shrink-0 fill-amber-400 text-amber-500"
                aria-label="已加星标"
              />
            ) : null}
          </div>
          <p className="text-muted-foreground mt-0.5 truncate text-[11px] leading-4">
            {email.preview}
          </p>
          <div className="mt-1.5 flex min-h-4 gap-1 overflow-hidden">
            {email.labels.slice(0, 2).map((label) => (
              <span
                key={label}
                className="bg-muted text-muted-foreground shrink-0 rounded px-1.5 py-0.5 text-[9px] font-medium"
              >
                {label}
              </span>
            ))}
          </div>
        </div>
      </div>
    </button>
  );
}
