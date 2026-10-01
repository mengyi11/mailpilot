import { CalendarClock, CheckCircle2, ListChecks, Quote } from "lucide-react";

import type { ActionItem } from "@/types/email";

function formatDueAt(value: string) {
  return new Intl.DateTimeFormat("zh-CN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export function ActionItemList({ items }: { items: ActionItem[] }) {
  return (
    <section className="border-border bg-card text-card-foreground rounded-2xl border p-5">
      <div className="flex items-center gap-2">
        <ListChecks
          className="text-muted-foreground size-4"
          aria-hidden="true"
        />
        <h3 className="text-sm font-semibold">行动项</h3>
        <span className="bg-muted text-muted-foreground ml-auto rounded-full px-2 py-0.5 text-[11px]">
          {items.length}
        </span>
      </div>

      {items.length ? (
        <ul className="mt-4 space-y-3">
          {items.map((item) => (
            <li key={item.id} className="bg-muted/50 rounded-xl p-3.5">
              <div className="flex items-start gap-2.5">
                <CheckCircle2
                  className="text-muted-foreground mt-0.5 size-4 shrink-0"
                  aria-hidden="true"
                />
                <div className="min-w-0">
                  <p className="text-sm font-medium">{item.title}</p>
                  {item.dueAt ? (
                    <p className="text-primary mt-1 flex items-center gap-1 text-[11px]">
                      <CalendarClock className="size-3" aria-hidden="true" />
                      {formatDueAt(item.dueAt)}
                    </p>
                  ) : null}
                  <p className="text-muted-foreground mt-2 flex items-start gap-1.5 text-[11px] leading-4">
                    <Quote
                      className="mt-0.5 size-3 shrink-0"
                      aria-hidden="true"
                    />
                    <span>{item.evidence}</span>
                  </p>
                </div>
              </div>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-muted-foreground mt-4 text-xs leading-5">
          这封邮件没有需要执行的行动项。
        </p>
      )}
    </section>
  );
}
