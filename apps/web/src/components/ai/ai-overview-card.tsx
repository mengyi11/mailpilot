"use client";

import {
  AlertCircle,
  LoaderCircle,
  RefreshCw,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import type { ReactNode } from "react";

import { Button } from "@/components/ui/button";
import type { AIOverview } from "@/types/email";

const priorityLabels: Record<AIOverview["priority"], string> = {
  high: "高优先级",
  normal: "普通",
  low: "低优先级",
};

type AIOverviewCardProps = {
  overview: AIOverview;
  isAnalyzing: boolean;
  hasAnalysis: boolean;
  totalTokens: number | null;
  error: Error | null;
  onAnalyze: () => void;
};

const summaryTokenPattern =
  /(S\$\s?[\d,]+(?:\.\d+)?|[$¥￥€£]\s?[\d,]+(?:\.\d+)?|\b\d{1,2}(?::\d{2})?\s?(?:am|pm)\b|\b\d{1,2}\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{4}\b|\d{4}年\d{1,2}月\d{1,2}日|\d{1,2}月\d{1,2}日|\b\d+(?:\.\d+)?%|\b(?:urgent|required|deadline|must|register|apply|submit|confirm)\b|紧急|必须|截止(?:日期)?|报名|提交|确认|申请)/gi;

function highlightSummary(value: string): ReactNode[] {
  return value
    .split(summaryTokenPattern)
    .filter(Boolean)
    .map((part, index) => {
      const normalized = part.toLowerCase();
      const key = `${part}-${index}`;

      if (/^(s\$|[$¥￥€£])/.test(normalized)) {
        return (
          <strong
            key={key}
            className="rounded bg-emerald-500/10 px-1 font-bold text-emerald-700 dark:text-emerald-400"
          >
            {part}
          </strong>
        );
      }
      if (/^\d+(?:\.\d+)?%$/.test(normalized)) {
        return (
          <strong
            key={key}
            className="rounded bg-violet-500/10 px-1 font-bold text-violet-700 dark:text-violet-300"
          >
            {part}
          </strong>
        );
      }
      if (
        /(?:am|pm)$/.test(normalized) ||
        /\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)/.test(
          normalized,
        ) ||
        /年|月.*日/.test(part)
      ) {
        return (
          <strong
            key={key}
            className="rounded bg-sky-500/10 px-1 font-bold text-sky-700 dark:text-sky-300"
          >
            {part}
          </strong>
        );
      }
      if (/urgent|required|deadline|must|紧急|必须|截止/.test(normalized)) {
        return (
          <strong key={key} className="font-bold text-red-600 dark:text-red-400">
            {part}
          </strong>
        );
      }
      if (/register|apply|submit|confirm|报名|提交|确认|申请/.test(normalized)) {
        return (
          <strong key={key} className="text-primary font-bold">
            {part}
          </strong>
        );
      }
      return <span key={key}>{part}</span>;
    });
}

export function AIOverviewCard({
  overview,
  isAnalyzing,
  hasAnalysis,
  totalTokens,
  error,
  onAnalyze,
}: AIOverviewCardProps) {
  const zhMatch = overview.summary.match(
    /(?:^|\n)ZH:\s*([\s\S]*?)(?=\nEN:|$)/i,
  );
  const enMatch = overview.summary.match(/(?:^|\n)EN:\s*([\s\S]*?)$/i);
  const summaryZh = overview.summaryZh ?? zhMatch?.[1]?.trim() ?? null;
  const summaryEn = overview.summaryEn ?? enMatch?.[1]?.trim() ?? null;
  const statusText = isAnalyzing
    ? "正在提取摘要和日历候选…"
    : error
      ? "本次分析未完成"
      : hasAnalysis
        ? `分析完成${totalTokens == null ? "" : ` · ${totalTokens} tokens`}`
        : "尚未分析这封邮件";

  return (
    <section className="border-primary/20 bg-card flex min-h-0 flex-1 basis-0 flex-col overflow-hidden rounded-2xl border shadow-sm">
      <div className="border-primary/15 from-primary/12 via-primary/5 flex shrink-0 items-center justify-between gap-4 border-b bg-gradient-to-r to-transparent px-5 py-4">
        <div className="flex min-w-0 items-center gap-2.5">
          <div className="bg-primary/15 text-primary flex size-9 shrink-0 items-center justify-center rounded-xl">
            <Sparkles className="size-[18px]" aria-hidden="true" />
          </div>
          <div className="min-w-0">
            <h3 className="text-[15px] font-semibold">AI 速览</h3>
            <p className="text-muted-foreground mt-0.5 truncate text-[11px]">
              {statusText}
            </p>
          </div>
        </div>
        <Button
          variant={hasAnalysis ? "outline" : "default"}
          size="sm"
          onClick={onAnalyze}
          disabled={isAnalyzing}
        >
          {isAnalyzing ? (
            <LoaderCircle
              className="animate-spin"
              data-icon="inline-start"
              aria-hidden="true"
            />
          ) : hasAnalysis ? (
            <RefreshCw data-icon="inline-start" aria-hidden="true" />
          ) : (
            <Sparkles data-icon="inline-start" aria-hidden="true" />
          )}
          {isAnalyzing ? "分析中" : hasAnalysis ? "重新分析" : "开始分析"}
        </Button>
      </div>

      {error ? (
        <div
          role="alert"
          className="border-destructive/20 bg-destructive/5 text-destructive mx-4 mt-3 flex items-center gap-2 rounded-lg border px-3 py-2"
        >
          <AlertCircle className="size-3.5 shrink-0" aria-hidden="true" />
          <p className="line-clamp-1 min-w-0 flex-1 text-[11px]">
            {error.message || "AI分析失败，请稍后重试。"}
          </p>
        </div>
      ) : null}

      <div className="flex min-h-0 flex-1 flex-col gap-3 px-5 py-4">
        <div className="border-primary/10 bg-primary/[0.035] min-h-0 flex-1 overflow-y-auto rounded-xl border px-4 py-4">
          {hasAnalysis ? (
            <div>
              <h4 className="text-primary border-primary/25 border-l-2 pl-2.5 text-[12px] font-bold tracking-wide">
                摘要概览
              </h4>
              <ol className="mt-3 space-y-2.5">
                <li className="border-border/60 bg-background/70 flex items-start gap-3 rounded-xl border px-3.5 py-3">
                  <span className="bg-primary text-primary-foreground mt-0.5 flex size-6 shrink-0 items-center justify-center rounded-lg text-[11px] font-bold shadow-sm">
                    1
                  </span>
                  <div className="min-w-0">
                    <span className="text-primary text-[10px] font-bold tracking-[0.14em] uppercase">
                      中文摘要
                    </span>
                    <p className="text-foreground mt-1 text-[14px] leading-6 font-semibold">
                      {highlightSummary(summaryZh ?? overview.summary)}
                    </p>
                  </div>
                </li>
                <li className="border-border/60 bg-background/55 flex items-start gap-3 rounded-xl border px-3.5 py-3">
                  <span className="border-primary/30 bg-primary/10 text-primary mt-0.5 flex size-6 shrink-0 items-center justify-center rounded-lg border text-[11px] font-bold">
                    2
                  </span>
                  <div className="min-w-0">
                    <span className="text-muted-foreground text-[10px] font-bold tracking-[0.14em] uppercase">
                      English Summary
                    </span>
                    <p className="text-foreground/75 mt-1 text-[13px] leading-6 font-medium italic">
                      {highlightSummary(summaryEn ?? overview.summary)}
                    </p>
                  </div>
                </li>
              </ol>
            </div>
          ) : (
            <div>
              <h4 className="text-primary border-primary/25 border-l-2 pl-2.5 text-[12px] font-bold tracking-wide">
                等待分析
              </h4>
              <p className="text-muted-foreground mt-3 text-[13px] leading-6 italic">
                {overview.summary}
              </p>
            </div>
          )}
        </div>
        <div className="text-muted-foreground flex min-w-0 shrink-0 items-center gap-2 text-[10px]">
          <span className="bg-primary/10 text-primary max-w-[42%] truncate rounded-full px-2.5 py-1 font-medium">
            {overview.category}
          </span>
          <span className="border-border bg-background inline-flex items-center gap-1 rounded-full border px-2.5 py-1">
            {priorityLabels[overview.priority]}
          </span>
          <span className="border-border bg-background inline-flex items-center gap-1 rounded-full border px-2.5 py-1">
            <ShieldCheck
              className="size-3 text-emerald-600"
              aria-hidden="true"
            />
            {Math.round(overview.confidence * 100)}%
          </span>
        </div>
      </div>
    </section>
  );
}
