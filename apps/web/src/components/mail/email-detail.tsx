"use client";

import { Mail, Paperclip, Reply } from "lucide-react";
import { useState } from "react";

import { AIOverviewCard } from "@/components/ai/ai-overview-card";
import { CalendarDraftCard } from "@/components/calendar/calendar-draft-card";
import { ReplyDraftDrawer } from "@/components/mail/reply-draft-drawer";
import { ActionItemList } from "@/components/ai/action-item-list";
import { TranslationPanel } from "@/components/ai/translation-panel";
import { Button } from "@/components/ui/button";
import type { EmailDetailData } from "@/types/email";

function formatDate(value: string) {
  return new Intl.DateTimeFormat("zh-CN", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export function EmailDetail({ email }: { email: EmailDetailData }) {
  const [replyOpen, setReplyOpen] = useState(false);

  return (
    <>
      <article className="overflow-hidden rounded-2xl border border-stone-200 bg-white shadow-sm">
        <header className="border-b border-stone-100 p-5 md:p-6">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="min-w-0">
              <div className="flex flex-wrap gap-2">
                {email.labels.map((label) => (
                  <span
                    key={label}
                    className="rounded-md bg-stone-100 px-2 py-1 text-[11px] font-medium text-stone-600"
                  >
                    {label}
                  </span>
                ))}
              </div>
              <h2 className="mt-3 text-xl font-semibold tracking-tight md:text-2xl">
                {email.subject}
              </h2>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setReplyOpen(true)}
            >
              <Reply data-icon="inline-start" aria-hidden="true" />
              回复
            </Button>
          </div>

          <div className="mt-5 flex items-start gap-3">
            <div className="flex size-10 shrink-0 items-center justify-center rounded-full bg-stone-900 text-sm font-semibold text-white">
              {email.sender.name.slice(0, 1).toUpperCase()}
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-semibold">
                {email.sender.name}
              </p>
              <p className="truncate text-xs text-stone-500">
                {email.sender.email} · 至{" "}
                {email.recipients.map((item) => item.name).join("、")}
              </p>
            </div>
            <time
              dateTime={email.receivedAt}
              className="shrink-0 text-xs text-stone-400"
            >
              {formatDate(email.receivedAt)}
            </time>
          </div>
        </header>

        <div className="grid gap-5 p-5 md:p-6 xl:grid-cols-[minmax(0,1fr)_320px]">
          <section aria-labelledby="message-content-heading">
            <div className="flex items-center gap-2 text-xs font-medium text-stone-500">
              <Mail className="size-3.5" aria-hidden="true" />
              <h3 id="message-content-heading">邮件原文</h3>
            </div>
            <div className="mt-4 text-sm leading-7 whitespace-pre-line text-stone-700">
              {email.bodyText}
            </div>
            <Button variant="ghost" size="sm" className="mt-6">
              <Paperclip data-icon="inline-start" aria-hidden="true" />
              暂无附件
            </Button>
          </section>

          <div className="space-y-4">
            <AIOverviewCard overview={email.aiOverview} />
            <ActionItemList items={email.actionItems} />
            {email.calendarDraft ? (
              <CalendarDraftCard draft={email.calendarDraft} />
            ) : null}
            <TranslationPanel translation={email.translation} />
          </div>
        </div>
      </article>
      <ReplyDraftDrawer
        draft={email.replyDraft}
        open={replyOpen}
        onClose={() => setReplyOpen(false)}
      />
    </>
  );
}
