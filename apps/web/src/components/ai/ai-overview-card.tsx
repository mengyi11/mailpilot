"use client";

import {
  AlertCircle,
  Languages,
  LoaderCircle,
  RefreshCw,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { useState } from "react";

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

export function AIOverviewCard({
  overview,
  isAnalyzing,
  hasAnalysis,
  totalTokens,
  error,
  onAnalyze,
}: AIOverviewCardProps) {
  const [summaryLanguage, setSummaryLanguage] = useState<"en" | "zh">(
    overview.summaryEn ? "en" : "zh",
  );
  const hasBilingualSummary = Boolean(overview.summaryEn && overview.summaryZh);
  const displayedSummary =
    summaryLanguage === "zh"
      ? (overview.summaryZh ?? overview.summary)
      : (overview.summaryEn ?? overview.summary);
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
        <div className="border-primary/10 bg-primary/[0.045] min-h-0 flex-1 overflow-hidden rounded-xl border px-3.5 py-3">
          <p className="text-foreground/85 h-full overflow-y-auto pr-1 text-[13px] leading-6">
            {displayedSummary}
          </p>
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
          <Button
            variant="ghost"
            size="xs"
            className="ml-auto rounded-full"
            disabled={!hasBilingualSummary}
            onClick={() =>
              setSummaryLanguage((language) =>
                language === "en" ? "zh" : "en",
              )
            }
            title={
              hasBilingualSummary
                ? "切换AI摘要语言"
                : "重新分析后可使用中英文摘要"
            }
          >
            <Languages data-icon="inline-start" aria-hidden="true" />
            {summaryLanguage === "en" ? "中文" : "EN"}
          </Button>
        </div>
      </div>
    </section>
  );
}
