import { ShieldCheck, Sparkles } from "lucide-react";

import type { AIOverview } from "@/types/email";

const priorityLabels: Record<AIOverview["priority"], string> = {
  high: "高优先级",
  normal: "普通",
  low: "低优先级",
};

export function AIOverviewCard({ overview }: { overview: AIOverview }) {
  return (
    <section className="border-primary/25 bg-primary/10 rounded-2xl border p-5">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <div className="bg-primary/15 text-primary flex size-8 items-center justify-center rounded-lg">
            <Sparkles className="size-4" aria-hidden="true" />
          </div>
          <div>
            <h3 className="text-foreground text-sm font-semibold">AI速览</h3>
            <p className="text-primary text-[11px]">结构化分析结果</p>
          </div>
        </div>
        <span className="bg-card text-primary rounded-full px-2.5 py-1 text-[11px] font-medium shadow-sm">
          {priorityLabels[overview.priority]}
        </span>
      </div>

      <p className="text-foreground mt-4 text-sm leading-6">
        {overview.summary}
      </p>

      <div className="text-primary mt-4 flex flex-wrap items-center gap-2 text-[11px]">
        <span className="bg-card/80 rounded-md px-2 py-1">
          {overview.category}
        </span>
        <span className="bg-card/80 inline-flex items-center gap-1 rounded-md px-2 py-1">
          <ShieldCheck className="size-3" aria-hidden="true" />
          置信度 {Math.round(overview.confidence * 100)}%
        </span>
      </div>
    </section>
  );
}
