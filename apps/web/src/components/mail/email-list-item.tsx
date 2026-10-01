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
        "w-full border-b border-stone-100 px-4 py-4 text-left transition-colors last:border-b-0",
        selected ? "bg-amber-50" : "bg-white hover:bg-stone-50",
      )}
    >
      <div className="flex items-start gap-3">
        <span
          className={cn(
            "mt-2 size-2 shrink-0 rounded-full",
            email.isRead ? "bg-transparent" : "bg-amber-500",
          )}
          aria-label={email.isRead ? "已读" : "未读"}
        />
        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between gap-3">
            <p
              className={cn(
                "truncate text-sm",
                email.isRead ? "font-medium text-stone-700" : "font-semibold",
              )}
            >
              {email.sender.name}
            </p>
            <time
              dateTime={email.receivedAt}
              className="shrink-0 text-[11px] text-stone-400"
            >
              {formatReceivedAt(email.receivedAt)}
            </time>
          </div>
          <div className="mt-1 flex items-center gap-2">
            <p className="truncate text-sm font-medium">{email.subject}</p>
            {email.isStarred ? (
              <Star
                className="size-3.5 shrink-0 fill-amber-400 text-amber-500"
                aria-label="已加星标"
              />
            ) : null}
          </div>
          <p className="mt-1 line-clamp-2 text-xs leading-5 text-stone-500">
            {email.preview}
          </p>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {email.labels.map((label) => (
              <span
                key={label}
                className="rounded-md bg-stone-100 px-2 py-0.5 text-[10px] font-medium text-stone-600"
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
