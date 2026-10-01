"use client";

import { Send, Sparkles, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import type { ReplyDraft } from "@/types/email";

type ReplyDraftDrawerProps = {
  draft: ReplyDraft;
  open: boolean;
  onClose: () => void;
};

export function ReplyDraftDrawer({
  draft,
  open,
  onClose,
}: ReplyDraftDrawerProps) {
  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50"
      role="dialog"
      aria-modal="true"
      aria-label="AI回复草稿"
    >
      <button
        type="button"
        className="absolute inset-0 bg-black/40 backdrop-blur-[2px]"
        onClick={onClose}
        aria-label="关闭回复草稿"
      />
      <aside className="bg-card text-card-foreground absolute inset-y-0 right-0 flex w-full max-w-xl flex-col shadow-2xl">
        <header className="border-border flex items-center justify-between border-b px-5 py-4">
          <div className="flex items-center gap-2">
            <Sparkles className="text-primary size-4" aria-hidden="true" />
            <div>
              <h2 className="text-sm font-semibold">AI回复草稿</h2>
              <p className="text-muted-foreground text-[11px]">
                {draft.tone} · {draft.language}
              </p>
            </div>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={onClose}
            aria-label="关闭"
          >
            <X aria-hidden="true" />
          </Button>
        </header>

        <div className="flex-1 overflow-y-auto p-5">
          <label
            className="text-muted-foreground text-xs font-medium"
            htmlFor="reply-subject"
          >
            主题
          </label>
          <input
            id="reply-subject"
            defaultValue={draft.subject}
            className="border-input bg-background focus:border-ring mt-2 w-full rounded-xl border px-3 py-2.5 text-sm outline-none"
          />
          <label
            className="text-muted-foreground mt-5 block text-xs font-medium"
            htmlFor="reply-body"
          >
            正文
          </label>
          <textarea
            id="reply-body"
            defaultValue={draft.body}
            rows={14}
            className="border-input bg-background focus:border-ring mt-2 w-full resize-none rounded-xl border px-3 py-3 text-sm leading-6 outline-none"
          />
        </div>

        <footer className="border-border border-t p-5">
          <Button className="w-full" disabled>
            <Send data-icon="inline-start" aria-hidden="true" />
            发送功能尚未接入
          </Button>
          <p className="text-muted-foreground mt-2 text-center text-[10px]">
            草稿不会自动发送，后续需要Human Approval和邮件Tool。
          </p>
        </footer>
      </aside>
    </div>
  );
}
