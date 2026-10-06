"use client";

import {
  GripVertical,
  Languages,
  Mail,
  Maximize2,
  Minimize2,
  Paperclip,
  Reply,
  RotateCcw,
} from "lucide-react";
import {
  type CSSProperties,
  type PointerEvent as ReactPointerEvent,
  useRef,
  useState,
} from "react";

import { AIOverviewCard } from "@/components/ai/ai-overview-card";
import { CalendarDraftCard } from "@/components/calendar/calendar-draft-card";
import { HtmlEmailBody } from "@/components/mail/html-email-body";
import { ReplyDraftDrawer } from "@/components/mail/reply-draft-drawer";
import { RichEmailBody } from "@/components/mail/rich-email-body";
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
  const [messagePanePercent, setMessagePanePercent] = useState(62);
  const detailGridRef = useRef<HTMLDivElement>(null);

  function resizeMessagePane(nextPercent: number) {
    setMessagePanePercent(Math.min(72, Math.max(48, nextPercent)));
  }

  function startPaneResize(event: ReactPointerEvent<HTMLButtonElement>) {
    const grid = detailGridRef.current;

    if (!grid) return;

    event.preventDefault();
    event.currentTarget.setPointerCapture(event.pointerId);

    const handlePointerMove = (moveEvent: PointerEvent) => {
      const bounds = grid.getBoundingClientRect();
      const nextPercent =
        ((moveEvent.clientX - bounds.left) / bounds.width) * 100;
      resizeMessagePane(nextPercent);
    };

    const stopResize = () => {
      window.removeEventListener("pointermove", handlePointerMove);
      window.removeEventListener("pointerup", stopResize);
    };

    window.addEventListener("pointermove", handlePointerMove);
    window.addEventListener("pointerup", stopResize);
  }

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

        <div
          ref={detailGridRef}
          className="grid min-h-0 flex-1 gap-4 overflow-y-auto p-4 xl:grid-cols-[minmax(300px,var(--message-pane))_12px_minmax(300px,var(--ai-pane))] xl:gap-0 xl:overflow-hidden"
          style={
            {
              "--message-pane": `${messagePanePercent}fr`,
              "--ai-pane": `${100 - messagePanePercent}fr`,
            } as CSSProperties
          }
        >
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
                  <div className="border-border mr-1 hidden items-center rounded-lg border xl:flex">
                    <Button
                      variant="ghost"
                      size="icon-xs"
                      onClick={() => resizeMessagePane(messagePanePercent - 5)}
                      aria-label="缩小邮件原文区域"
                      title="缩小邮件原文区域"
                    >
                      <Minimize2 aria-hidden="true" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon-xs"
                      onClick={() => resizeMessagePane(62)}
                      aria-label="恢复默认宽度"
                      title="恢复默认宽度"
                    >
                      <RotateCcw aria-hidden="true" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon-xs"
                      onClick={() => resizeMessagePane(messagePanePercent + 5)}
                      aria-label="放大邮件原文区域"
                      title="放大邮件原文区域"
                    >
                      <Maximize2 aria-hidden="true" />
                    </Button>
                  </div>
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
              <div className="text-foreground/80 mt-3 min-h-0 flex-1 overflow-y-auto">
                {!showTranslation && email.bodyHtml ? (
                  <HtmlEmailBody html={email.bodyHtml} title={email.subject} />
                ) : showTranslation && email.translation.translatedHtml ? (
                  <HtmlEmailBody
                    html={email.translation.translatedHtml}
                    title={`${email.subject}（译文）`}
                  />
                ) : showTranslation &&
                  email.translation.status !== "completed" ? (
                  <div className="flex min-h-[360px] items-center justify-center px-6 text-center">
                    <div>
                      <p className="text-foreground text-sm font-medium">
                        尚未生成保留排版的译文
                      </p>
                      <p className="text-muted-foreground mt-2 max-w-sm text-xs leading-6">
                        翻译 Agent 接入后会保留 HTML
                        标签和样式，并对图片文字执行 OCR。
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="pr-3">
                    <RichEmailBody
                      content={
                        showTranslation
                          ? email.translation.translatedBody
                          : email.bodyText
                      }
                    />
                  </div>
                )}
              </div>
              {showTranslation ? (
                <div className="text-muted-foreground mt-3 shrink-0 border-t pt-3 text-[11px]">
                  <p>AI译文和OCR结果仅供参考，执行操作前请核对邮件原文。</p>
                  {email.translation.ocrBlocks.length > 0 ? (
                    <details className="mt-2">
                      <summary className="text-foreground cursor-pointer font-medium">
                        查看图片文字翻译（{email.translation.ocrBlocks.length}）
                      </summary>
                      <div className="mt-2 max-h-32 space-y-2 overflow-y-auto">
                        {email.translation.ocrBlocks.map((block) => (
                          <div
                            key={`${block.imageIndex}-${block.sourceText}`}
                            className="bg-muted rounded-lg p-2"
                          >
                            <p>{block.translatedText}</p>
                            <p className="mt-1 opacity-60">
                              原文：{block.sourceText}
                            </p>
                          </div>
                        ))}
                      </div>
                    </details>
                  ) : null}
                </div>
              ) : null}
            </section>
          </div>

          <button
            type="button"
            onPointerDown={startPaneResize}
            className="group hidden h-full cursor-col-resize touch-none items-center justify-center xl:flex"
            aria-label="拖动调整邮件原文和AI信息区域宽度"
            title="拖动调整左右区域宽度"
          >
            <span className="bg-border group-hover:bg-primary/60 group-focus-visible:bg-primary/60 flex h-12 w-1 items-center justify-center rounded-full transition-colors">
              <GripVertical
                className="text-muted-foreground size-3.5 max-w-none"
                aria-hidden="true"
              />
            </span>
          </button>

          <aside
            className="flex min-h-[520px] flex-col gap-3 overflow-hidden xl:min-h-0 xl:pl-1"
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
