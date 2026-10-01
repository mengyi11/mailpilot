import { ShieldCheck, Sparkles } from "lucide-react";

import type { AIOverview } from "@/types/email";

const priorityLabels: Record<AIOverview["priority"], string> = {
  high: "高优先级",
  normal: "普通",
  low: "低优先级",
};

export function AIOverviewCard({ overview }: { overview: AIOverview }) {
  return (
    <section className="rounded-2xl border border-amber-200 bg-amber-50/70 p-5">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <div className="flex size-8 items-center justify-center rounded-lg bg-amber-100 text-amber-800">
            <Sparkles className="size-4" aria-hidden="true" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-amber-950">AI速览</h3>
            <p className="text-[11px] text-amber-700">结构化分析结果</p>
          </div>
        </div>
        <span className="rounded-full bg-white px-2.5 py-1 text-[11px] font-medium text-amber-800 shadow-sm">
          {priorityLabels[overview.priority]}
        </span>
      </div>

      <p className="mt-4 text-sm leading-6 text-amber-950">
        {overview.summary}
      </p>

      <div className="mt-4 flex flex-wrap items-center gap-2 text-[11px] text-amber-800">
        <span className="rounded-md bg-white/80 px-2 py-1">
          {overview.category}
        </span>
        <span className="inline-flex items-center gap-1 rounded-md bg-white/80 px-2 py-1">
          <ShieldCheck className="size-3" aria-hidden="true" />
          置信度 {Math.round(overview.confidence * 100)}%
        </span>
      </div>
    </section>
  );
}
