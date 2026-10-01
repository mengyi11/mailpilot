import { ArrowRight, Languages } from "lucide-react";

import type { Translation } from "@/types/email";

export function TranslationPanel({
  translation,
}: {
  translation: Translation;
}) {
  return (
    <section className="border-border bg-muted/50 rounded-2xl border p-5">
      <div className="flex items-center gap-2">
        <Languages
          className="text-muted-foreground size-4"
          aria-hidden="true"
        />
        <h3 className="text-sm font-semibold">邮件翻译</h3>
      </div>
      <div className="text-muted-foreground mt-3 flex items-center gap-2 text-[11px] font-medium">
        <span>{translation.sourceLanguage}</span>
        <ArrowRight className="size-3" aria-hidden="true" />
        <span>{translation.targetLanguage}</span>
      </div>
      <div className="text-foreground/80 mt-4 text-sm leading-6 whitespace-pre-line">
        {translation.translatedBody}
      </div>
      <p className="text-muted-foreground mt-4 text-[11px] leading-5">
        AI译文仅供参考，执行操作前请核对邮件原文。
      </p>
    </section>
  );
}
