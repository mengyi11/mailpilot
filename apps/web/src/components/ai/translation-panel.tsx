import { ArrowRight, Languages } from "lucide-react";

import type { Translation } from "@/types/email";

export function TranslationPanel({
  translation,
}: {
  translation: Translation;
}) {
  return (
    <section className="rounded-2xl border border-stone-200 bg-stone-50 p-5">
      <div className="flex items-center gap-2">
        <Languages className="size-4 text-stone-500" aria-hidden="true" />
        <h3 className="text-sm font-semibold">邮件翻译</h3>
      </div>
      <div className="mt-3 flex items-center gap-2 text-[11px] font-medium text-stone-500">
        <span>{translation.sourceLanguage}</span>
        <ArrowRight className="size-3" aria-hidden="true" />
        <span>{translation.targetLanguage}</span>
      </div>
      <div className="mt-4 text-sm leading-6 whitespace-pre-line text-stone-700">
        {translation.translatedBody}
      </div>
      <p className="mt-4 text-[11px] leading-5 text-stone-400">
        AI译文仅供参考，执行操作前请核对邮件原文。
      </p>
    </section>
  );
}
