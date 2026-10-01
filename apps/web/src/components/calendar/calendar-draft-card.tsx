"use client";

import { CalendarCheck, Check, Clock3, X } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import type { CalendarDraft } from "@/types/email";

function formatDate(value: string) {
  return new Intl.DateTimeFormat("zh-CN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

type DraftStatus = "pending" | "approved" | "rejected";

export function CalendarDraftCard({ drafts }: { drafts: CalendarDraft[] }) {
  const [statuses, setStatuses] = useState<Record<string, DraftStatus>>({});

  function updateStatus(id: string, status: DraftStatus) {
    setStatuses((current) => ({ ...current, [id]: status }));
  }

  return (
    <section className="border-border bg-card text-card-foreground flex h-80 min-h-0 flex-col overflow-hidden rounded-2xl border p-4 xl:h-auto xl:flex-1">
      <div className="flex h-8 shrink-0 items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <CalendarCheck
            className="text-muted-foreground size-4"
            aria-hidden="true"
          />
          <h3 className="text-sm font-semibold">日历候选</h3>
        </div>
        <span className="bg-muted text-muted-foreground rounded-full px-2 py-1 text-[10px] font-medium">
          {drafts.length} 项
        </span>
      </div>

      {drafts.length ? (
        <div className="mt-2 min-h-0 flex-1 space-y-2 overflow-y-auto pr-1">
          {drafts.map((draft) => {
            const status = statuses[draft.id] ?? "pending";

            return (
              <article
                key={draft.id}
                className="bg-muted/50 flex h-16 items-center rounded-xl px-2.5"
              >
                <div className="flex min-w-0 flex-1 items-center gap-1.5">
                  <div className="min-w-0 flex-1">
                    <div className="flex min-w-0 items-center gap-1.5">
                      <p className="truncate text-xs font-semibold">
                        {draft.title}
                      </p>
                      <span className="text-primary shrink-0 text-[9px]">
                        {status === "pending"
                          ? "待确认"
                          : status === "approved"
                            ? "已确认"
                            : "已忽略"}
                      </span>
                    </div>
                    <p className="text-muted-foreground mt-1 flex items-center gap-1.5 truncate text-[10px]">
                      <Clock3 className="size-3 shrink-0" aria-hidden="true" />
                      {formatDate(draft.startsAt)}
                      {draft.location ? ` · ${draft.location}` : ""}
                    </p>
                  </div>
                  <div className="flex shrink-0 gap-0.5">
                    {status === "pending" ? (
                      <>
                        <Button
                          variant="ghost"
                          size="icon-xs"
                          onClick={() => updateStatus(draft.id, "rejected")}
                          aria-label={`忽略${draft.title}`}
                        >
                          <X aria-hidden="true" />
                        </Button>
                        <Button
                          size="icon-xs"
                          onClick={() => updateStatus(draft.id, "approved")}
                          aria-label={`确认${draft.title}`}
                        >
                          <Check aria-hidden="true" />
                        </Button>
                      </>
                    ) : (
                      <Button
                        variant="ghost"
                        size="xs"
                        onClick={() => updateStatus(draft.id, "pending")}
                      >
                        撤销
                      </Button>
                    )}
                  </div>
                </div>
              </article>
            );
          })}
        </div>
      ) : (
        <div className="text-muted-foreground flex min-h-0 flex-1 items-center justify-center text-center text-xs leading-5">
          这封邮件没有提取到日历候选。
        </div>
      )}

      <p className="text-muted-foreground mt-2 h-4 shrink-0 truncate text-[10px]">
        确认后才会写入日历。
      </p>
    </section>
  );
}
