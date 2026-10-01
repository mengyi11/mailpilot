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
        className="absolute inset-0 bg-stone-950/30 backdrop-blur-[2px]"
        onClick={onClose}
        aria-label="关闭回复草稿"
      />
      <aside className="absolute inset-y-0 right-0 flex w-full max-w-xl flex-col bg-white shadow-2xl">
        <header className="flex items-center justify-between border-b border-stone-200 px-5 py-4">
          <div className="flex items-center gap-2">
            <Sparkles className="size-4 text-amber-600" aria-hidden="true" />
            <div>
              <h2 className="text-sm font-semibold">AI回复草稿</h2>
              <p className="text-[11px] text-stone-500">
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
            className="text-xs font-medium text-stone-500"
            htmlFor="reply-subject"
          >
            主题
          </label>
          <input
            id="reply-subject"
            defaultValue={draft.subject}
            className="mt-2 w-full rounded-xl border border-stone-200 bg-stone-50 px-3 py-2.5 text-sm outline-none focus:border-stone-400"
          />
          <label
            className="mt-5 block text-xs font-medium text-stone-500"
            htmlFor="reply-body"
          >
            正文
          </label>
          <textarea
            id="reply-body"
            defaultValue={draft.body}
            rows={14}
            className="mt-2 w-full resize-none rounded-xl border border-stone-200 bg-stone-50 px-3 py-3 text-sm leading-6 outline-none focus:border-stone-400"
          />
        </div>

        <footer className="border-t border-stone-200 p-5">
          <Button className="w-full" disabled>
            <Send data-icon="inline-start" aria-hidden="true" />
            发送功能尚未接入
          </Button>
          <p className="mt-2 text-center text-[10px] text-stone-400">
            草稿不会自动发送，后续需要Human Approval和邮件Tool。
          </p>
        </footer>
      </aside>
    </div>
  );
}
