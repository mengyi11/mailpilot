"use client";

import { CalendarCheck, Check, Clock3, MapPin, X } from "lucide-react";
import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { CalendarApprovalDialog } from "@/components/calendar/calendar-approval-dialog";
import { apiRequest, ApiError } from "@/lib/api-client";
import { calendarEventSchema, type CalendarEvent } from "@/lib/calendar-schema";
import type { CalendarDraft } from "@/types/email";

function formatDate(value: string) {
  return new Intl.DateTimeFormat("zh-CN", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

type DraftStatus = "pending" | "approved" | "rejected";

const statusLabels: Record<DraftStatus, string> = {
  pending: "待确认",
  approved: "已确认",
  rejected: "已忽略",
};

export function CalendarDraftCard({ drafts }: { drafts: CalendarDraft[] }) {
  const queryClient = useQueryClient();
  const [approvalCandidate, setApprovalCandidate] =
    useState<CalendarEvent | null>(null);
  const [statuses, setStatuses] = useState<Record<string, DraftStatus>>(() =>
    Object.fromEntries(
      drafts.map((draft) => [
        draft.id,
        draft.status === "confirmed"
          ? "approved"
          : draft.status === "rejected"
            ? "rejected"
            : "pending",
      ]),
    ),
  );
  const approve = useMutation({
    mutationFn: (event: CalendarEvent) =>
      apiRequest(`/calendar/candidates/${event.id}/approve`, {
        method: "POST",
        body: JSON.stringify({
          approvalId: event.approvalId,
          payloadHash: event.approvalPayloadHash,
        }),
        schema: calendarEventSchema,
      }),
    onSuccess: (_data, variables) => {
      setStatuses((current) => ({
        ...current,
        [variables.id]: "approved",
      }));
      setApprovalCandidate(null);
      queryClient.invalidateQueries({ queryKey: ["calendar-overview"] });
      queryClient.invalidateQueries({ queryKey: ["gmail-emails"] });
    },
  });
  const reject = useMutation({
    mutationFn: (id: string) =>
      apiRequest(`/calendar/candidates/${id}/reject`, {
        method: "POST",
        schema: calendarEventSchema,
      }),
    onSuccess: (_data, id) => {
      setStatuses((current) => ({ ...current, [id]: "rejected" }));
      queryClient.invalidateQueries({ queryKey: ["calendar-overview"] });
      queryClient.invalidateQueries({ queryKey: ["gmail-emails"] });
    },
  });
  const loadApproval = useMutation({
    mutationFn: (id: string) =>
      apiRequest(`/calendar/candidates/${id}`, {
        schema: calendarEventSchema,
      }),
    onSuccess: setApprovalCandidate,
  });

  function updateStatus(id: string, status: DraftStatus) {
    if (status === "pending") return;
    if (status === "approved") loadApproval.mutate(id);
    else reject.mutate(id);
  }

  return (
    <section className="border-border bg-card text-card-foreground flex min-h-0 flex-1 basis-0 flex-col overflow-hidden rounded-2xl border shadow-sm">
      <div className="border-primary/10 from-primary/8 flex shrink-0 items-center justify-between gap-3 border-b bg-gradient-to-r to-transparent px-4 py-3">
        <div className="flex min-w-0 items-center gap-2.5">
          <div className="bg-primary/10 text-primary flex size-8 shrink-0 items-center justify-center rounded-lg">
            <CalendarCheck className="size-4" aria-hidden="true" />
          </div>
          <div className="min-w-0">
            <h3 className="text-sm font-semibold">日历候选</h3>
            <p className="text-muted-foreground truncate text-[10px]">
              仅在你确认后写入日历
            </p>
          </div>
        </div>
        <span className="bg-muted text-muted-foreground rounded-full px-2.5 py-1 text-[10px] font-medium">
          {drafts.length} 项
        </span>
      </div>

      {drafts.length ? (
        <div className="min-h-0 flex-1 space-y-1.5 overflow-y-auto p-3">
          {drafts.map((draft) => {
            const status =
              statuses[draft.id] ??
              (draft.status === "confirmed"
                ? "approved"
                : draft.status === "rejected"
                  ? "rejected"
                  : "pending");

            return (
              <article
                key={draft.id}
                className="border-border/70 hover:bg-muted/30 flex min-h-14 items-center gap-2 rounded-xl border bg-transparent px-3 py-2 transition-colors"
              >
                <div className="min-w-0 flex-1">
                  <div className="flex min-w-0 items-center gap-2">
                    <p className="truncate text-xs font-semibold">
                      {draft.title}
                    </p>
                    <span
                      className={
                        status === "approved"
                          ? "shrink-0 rounded-full bg-emerald-500/10 px-1.5 py-0.5 text-[9px] font-medium text-emerald-700 dark:text-emerald-400"
                          : "bg-muted text-muted-foreground shrink-0 rounded-full px-1.5 py-0.5 text-[9px] font-medium"
                      }
                    >
                      {statusLabels[status]}
                    </span>
                  </div>
                  <div className="text-muted-foreground mt-1 flex min-w-0 items-center gap-2 text-[10px]">
                    <span className="inline-flex shrink-0 items-center gap-1">
                      <Clock3 className="size-3" aria-hidden="true" />
                      {formatDate(draft.startsAt)}
                    </span>
                    {draft.location ? (
                      <span className="inline-flex min-w-0 items-center gap-1 truncate">
                        <MapPin
                          className="size-3 shrink-0"
                          aria-hidden="true"
                        />
                        <span className="truncate">{draft.location}</span>
                      </span>
                    ) : null}
                  </div>
                </div>

                <div className="flex shrink-0 items-center gap-1">
                  {status === "pending" ? (
                    <>
                      <Button
                        variant="ghost"
                        size="icon-xs"
                        onClick={() => updateStatus(draft.id, "rejected")}
                        disabled={reject.isPending || loadApproval.isPending}
                        aria-label={`忽略${draft.title}`}
                        title="忽略"
                      >
                        <X aria-hidden="true" />
                      </Button>
                      <Button
                        variant="outline"
                        size="icon-xs"
                        className="text-primary hover:bg-primary/10 hover:text-primary"
                        onClick={() => updateStatus(draft.id, "approved")}
                        disabled={reject.isPending || loadApproval.isPending}
                        aria-label={`确认${draft.title}`}
                        title="确认"
                      >
                        <Check aria-hidden="true" />
                      </Button>
                    </>
                  ) : (
                    <span className="text-muted-foreground px-1 text-[9px]">
                      已处理
                    </span>
                  )}
                </div>
              </article>
            );
          })}
        </div>
      ) : (
        <div className="text-muted-foreground flex min-h-0 flex-1 flex-col items-center justify-center px-6 text-center">
          <CalendarCheck
            className="mb-2 size-6 opacity-35"
            aria-hidden="true"
          />
          <p className="text-xs font-medium">没有日历候选</p>
          <p className="mt-1 text-[10px]">这封邮件暂未提取到明确日期。</p>
        </div>
      )}
      {approvalCandidate ? (
        <CalendarApprovalDialog
          event={approvalCandidate}
          busy={approve.isPending}
          error={
            approve.error instanceof ApiError
              ? approve.error.message
              : approve.isError
                ? "创建失败，请稍后重试。"
                : undefined
          }
          onClose={() => {
            if (!approve.isPending) setApprovalCandidate(null);
          }}
          onConfirm={() => approve.mutate(approvalCandidate)}
        />
      ) : null}
    </section>
  );
}
