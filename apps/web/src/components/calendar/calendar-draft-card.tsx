"use client";

import { CalendarCheck, Check, Clock3, MapPin, Quote, X } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import type { CalendarDraft } from "@/types/email";

function formatDate(value: string) {
  return new Intl.DateTimeFormat("zh-CN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export function CalendarDraftCard({ draft }: { draft: CalendarDraft }) {
  const [status, setStatus] = useState<"pending" | "approved" | "rejected">(
    "pending",
  );

  return (
    <section className="rounded-2xl border border-stone-200 bg-white p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2">
          <CalendarCheck className="size-4 text-stone-500" aria-hidden="true" />
          <h3 className="text-sm font-semibold">日历候选</h3>
        </div>
        <span className="rounded-full bg-amber-50 px-2 py-1 text-[10px] font-medium text-amber-700">
          {status === "pending"
            ? "等待确认"
            : status === "approved"
              ? "已在本页确认"
              : "已在本页忽略"}
        </span>
      </div>

      <p className="mt-4 text-sm font-semibold">{draft.title}</p>
      <div className="mt-3 space-y-2 text-xs text-stone-600">
        <p className="flex items-start gap-2">
          <Clock3 className="mt-0.5 size-3.5 shrink-0" aria-hidden="true" />
          <span>
            {formatDate(draft.startsAt)}
            {draft.endsAt ? ` – ${formatDate(draft.endsAt)}` : ""}
            <br />
            {draft.timezone}
          </span>
        </p>
        {draft.location ? (
          <p className="flex items-center gap-2">
            <MapPin className="size-3.5" aria-hidden="true" />
            {draft.location}
          </p>
        ) : null}
        <p className="flex items-start gap-2 text-stone-500">
          <Quote className="mt-0.5 size-3.5 shrink-0" aria-hidden="true" />
          {draft.evidence}
        </p>
      </div>

      {status === "pending" ? (
        <div className="mt-4 grid grid-cols-2 gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setStatus("rejected")}
          >
            <X data-icon="inline-start" aria-hidden="true" />
            忽略
          </Button>
          <Button size="sm" onClick={() => setStatus("approved")}>
            <Check data-icon="inline-start" aria-hidden="true" />
            确认
          </Button>
        </div>
      ) : (
        <Button
          variant="ghost"
          size="sm"
          className="mt-3 w-full"
          onClick={() => setStatus("pending")}
        >
          撤销本页操作
        </Button>
      )}

      <p className="mt-3 text-[10px] leading-4 text-stone-400">
        当前仅更新页面状态，尚未连接真实日历Tool。
      </p>
    </section>
  );
}
