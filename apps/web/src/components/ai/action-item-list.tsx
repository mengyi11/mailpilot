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
    <section className="rounded-2xl border border-stone-200 bg-white p-5">
      <div className="flex items-center gap-2">
        <ListChecks className="size-4 text-stone-500" aria-hidden="true" />
        <h3 className="text-sm font-semibold">行动项</h3>
        <span className="ml-auto rounded-full bg-stone-100 px-2 py-0.5 text-[11px] text-stone-500">
          {items.length}
        </span>
      </div>

      {items.length ? (
        <ul className="mt-4 space-y-3">
          {items.map((item) => (
            <li key={item.id} className="rounded-xl bg-stone-50 p-3.5">
              <div className="flex items-start gap-2.5">
                <CheckCircle2
                  className="mt-0.5 size-4 shrink-0 text-stone-400"
                  aria-hidden="true"
                />
                <div className="min-w-0">
                  <p className="text-sm font-medium">{item.title}</p>
                  {item.dueAt ? (
                    <p className="mt-1 flex items-center gap-1 text-[11px] text-amber-700">
                      <CalendarClock className="size-3" aria-hidden="true" />
                      {formatDueAt(item.dueAt)}
                    </p>
                  ) : null}
                  <p className="mt-2 flex items-start gap-1.5 text-[11px] leading-4 text-stone-500">
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
        <p className="mt-4 text-xs leading-5 text-stone-500">
          这封邮件没有需要执行的行动项。
        </p>
      )}
    </section>
  );
}
