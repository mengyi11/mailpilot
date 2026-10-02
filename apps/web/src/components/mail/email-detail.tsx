"use client";

import { Languages, Mail, Paperclip, Reply } from "lucide-react";
import { useState } from "react";

import { AIOverviewCard } from "@/components/ai/ai-overview-card";
import { CalendarDraftCard } from "@/components/calendar/calendar-draft-card";
import { ReplyDraftDrawer } from "@/components/mail/reply-draft-drawer";
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
  const [showTranslation, setShowTranslation] = useState(false);

  return (
    <>
      <article className="bg-card text-card-foreground flex h-full min-h-0 flex-col overflow-hidden">
        <header className="border-border shrink-0 border-b p-4 md:px-5 md:py-4">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="min-w-0">
              <div className="flex flex-wrap gap-2">
                {email.labels.map((label) => (
                  <span
                    key={label}
                    className="bg-muted text-muted-foreground rounded-md px-2 py-1 text-[11px] font-medium"
                  >
                    {label}
                  </span>
                ))}
              </div>
              <h2 className="mt-2 line-clamp-1 text-lg font-semibold tracking-tight md:text-xl">
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

          <div className="mt-3 flex items-start gap-3">
            <div className="bg-primary text-primary-foreground flex size-9 shrink-0 items-center justify-center rounded-full text-sm font-semibold">
              {email.sender.name.slice(0, 1).toUpperCase()}
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-semibold">
                {email.sender.name}
              </p>
              <p className="text-muted-foreground truncate text-xs">
                {email.sender.email} · 至{" "}
                {email.recipients.map((item) => item.name).join("、")}
              </p>
            </div>
            <time
              dateTime={email.receivedAt}
              className="text-muted-foreground shrink-0 text-xs"
            >
              {formatDate(email.receivedAt)}
            </time>
          </div>
        </header>

        <div className="grid min-h-0 flex-1 gap-4 overflow-y-auto p-4 xl:grid-cols-[minmax(360px,1fr)_300px] xl:overflow-hidden 2xl:grid-cols-[minmax(420px,1fr)_310px]">
          <div className="flex min-h-[620px] flex-col xl:min-h-0">
            <section
              className="border-border flex min-h-0 flex-1 flex-col rounded-2xl border p-4"
              aria-labelledby="message-content-heading"
            >
              <div className="text-muted-foreground flex shrink-0 items-center justify-between gap-2 text-xs font-medium">
                <span className="flex items-center gap-2">
                  <Mail className="size-3.5" aria-hidden="true" />
                  <h3 id="message-content-heading">
                    {showTranslation ? "邮件译文" : "邮件原文"}
                  </h3>
                  {showTranslation ? (
                    <span className="bg-primary/10 text-primary rounded-full px-2 py-0.5 text-[10px]">
                      {email.translation.targetLanguage}
                    </span>
                  ) : null}
                </span>
                <div className="flex items-center gap-1">
                  <Button
                    variant={showTranslation ? "secondary" : "ghost"}
                    size="xs"
                    onClick={() => setShowTranslation((value) => !value)}
                  >
                    <Languages data-icon="inline-start" aria-hidden="true" />
                    {showTranslation ? "查看原文" : "翻译"}
                  </Button>
                  <Button variant="ghost" size="xs">
                    <Paperclip data-icon="inline-start" aria-hidden="true" />
                    暂无附件
                  </Button>
                </div>
              </div>
              <div className="text-foreground/80 mt-3 min-h-0 flex-1 overflow-y-auto pr-2 text-sm leading-7 whitespace-pre-line">
                {showTranslation
                  ? email.translation.translatedBody
                  : email.bodyText}
              </div>
              {showTranslation ? (
                <p className="text-muted-foreground mt-3 shrink-0 border-t pt-3 text-[11px]">
                  AI译文仅供参考，执行操作前请核对邮件原文。
                </p>
              ) : null}
            </section>
          </div>

          <aside
            className="flex min-h-[520px] flex-col gap-3 overflow-hidden xl:min-h-0 xl:pr-1"
            aria-label="AI邮件信息"
          >
            <AIOverviewCard overview={email.aiOverview} />
            <CalendarDraftCard drafts={email.calendarDrafts} />
          </aside>
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
