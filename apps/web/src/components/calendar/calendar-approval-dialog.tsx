"use client";

import { CalendarCheck, Clock3, Globe2, MapPin, Users, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import type { CalendarEvent } from "@/lib/calendar-schema";

export function CalendarApprovalDialog({
  event,
  busy,
  error,
  onClose,
  onConfirm,
}: {
  event: CalendarEvent;
  busy: boolean;
  error?: string;
  onClose: () => void;
  onConfirm: () => void;
}) {
  const expires = event.approvalExpiresAt
    ? new Intl.DateTimeFormat("zh-CN", {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      }).format(new Date(event.approvalExpiresAt))
    : null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/45 p-4 backdrop-blur-sm">
      <section className="border-border bg-card w-full max-w-lg rounded-2xl border p-6 shadow-2xl">
        <header className="flex items-start justify-between gap-4">
          <div>
            <p className="text-primary text-[10px] font-semibold tracking-[0.16em] uppercase">
              Human approval
            </p>
            <h2 className="mt-1 text-lg font-semibold">
              确认写入 Google Calendar
            </h2>
            <p className="text-muted-foreground mt-1 text-xs leading-5">
              确认后系统才会执行真实写入，并回读验证结果。
            </p>
          </div>
          <Button
            variant="ghost"
            size="icon-sm"
            onClick={onClose}
            disabled={busy}
          >
            <X />
          </Button>
        </header>
        <div className="bg-muted/45 mt-5 rounded-xl p-4">
          <h3 className="font-semibold">{event.title}</h3>
          <div className="text-muted-foreground mt-3 grid gap-2 text-xs sm:grid-cols-2">
            <p className="flex items-center gap-2">
              <Clock3 className="size-4" />
              {new Date(event.startsAt).toLocaleString("zh-CN")}
              {event.endsAt
                ? ` – ${new Date(event.endsAt).toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" })}`
                : ""}
            </p>
            <p className="flex items-center gap-2">
              <Globe2 className="size-4" />
              {event.timezone}
            </p>
            <p className="flex items-center gap-2">
              <MapPin className="size-4" />
              {event.location || "未设置地点"}
            </p>
            <p className="flex items-center gap-2">
              <Users className="size-4" />
              {event.attendees.length ? event.attendees.join("、") : "无参与人"}
            </p>
          </div>
          {event.evidence ? (
            <blockquote className="border-primary/30 text-muted-foreground mt-4 border-l-2 pl-3 text-xs italic">
              “{event.evidence}”
            </blockquote>
          ) : null}
        </div>
        <div className="mt-4 rounded-lg border border-amber-500/25 bg-amber-500/8 px-3 py-2 text-[11px] text-amber-800 dark:text-amber-300">
          此审批只对当前参数有效{expires ? `，将在 ${expires} 过期` : ""}
          。参数变化后必须重新确认，重复点击不会创建重复事件。
        </div>
        {error ? (
          <p className="text-destructive mt-3 text-xs">{error}</p>
        ) : null}
        <footer className="mt-6 flex justify-end gap-2">
          <Button variant="outline" onClick={onClose} disabled={busy}>
            取消
          </Button>
          <Button
            onClick={onConfirm}
            disabled={busy || !event.approvalId || !event.approvalPayloadHash}
          >
            <CalendarCheck />
            {busy ? "正在创建并验证…" : "确认并创建事件"}
          </Button>
        </footer>
      </section>
    </div>
  );
}
