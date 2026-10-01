import {
  ArrowUpRight,
  CheckCircle2,
  Languages,
  Mail,
  Sparkles,
} from "lucide-react";

import { AppLayout } from "@/components/layout/app-layout";
import { Button } from "@/components/ui/button";

const overview = [
  { label: "待处理邮件", value: "12", detail: "3封高优先级", icon: Mail },
  { label: "今日AI摘要", value: "8", detail: "平均2.1秒", icon: Sparkles },
  {
    label: "待确认事项",
    value: "3",
    detail: "需要你的批准",
    icon: CheckCircle2,
  },
];

export default function Home() {
  return (
    <AppLayout>
      <div className="mx-auto max-w-7xl px-5 py-8 md:px-8 md:py-10">
        <section aria-labelledby="overview-heading">
          <div className="flex items-end justify-between gap-4">
            <div>
              <h2
                id="overview-heading"
                className="text-lg font-semibold tracking-tight"
              >
                今日概览
              </h2>
              <p className="mt-1 text-sm text-stone-500">
                邮件中的重点、行动项和日期集中在这里。
              </p>
            </div>
            <p className="hidden text-sm text-stone-500 sm:block">
              最后同步：刚刚
            </p>
          </div>

          <div className="mt-5 grid gap-4 md:grid-cols-3">
            {overview.map(({ label, value, detail, icon: Icon }) => (
              <article
                key={label}
                className="rounded-2xl border border-stone-200 bg-white p-5 shadow-sm"
              >
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium text-stone-600">{label}</p>
                  <Icon className="size-4 text-stone-400" aria-hidden="true" />
                </div>
                <p className="mt-5 text-3xl font-semibold tracking-tight">
                  {value}
                </p>
                <p className="mt-1 text-xs text-stone-500">{detail}</p>
              </article>
            ))}
          </div>
        </section>

        <section
          className="mt-8 grid gap-6 lg:grid-cols-[1.6fr_1fr]"
          aria-label="邮件工作区"
        >
          <article className="overflow-hidden rounded-2xl border border-stone-200 bg-white shadow-sm">
            <div className="flex items-center justify-between border-b border-stone-100 px-5 py-4">
              <div>
                <h2 className="font-semibold tracking-tight">需要关注</h2>
                <p className="mt-0.5 text-xs text-stone-500">
                  AI识别出的高优先级邮件
                </p>
              </div>
              <Button variant="ghost" size="sm">
                查看全部
                <ArrowUpRight data-icon="inline-end" aria-hidden="true" />
              </Button>
            </div>
            <div className="divide-y divide-stone-100">
              <div className="p-5">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-sm font-semibold">
                      Project launch review
                    </p>
                    <p className="mt-1 text-xs text-stone-500">
                      Alex Chen · 10分钟前
                    </p>
                  </div>
                  <span className="rounded-full bg-red-50 px-2.5 py-1 text-xs font-medium text-red-700">
                    高优先级
                  </span>
                </div>
                <p className="mt-4 text-sm leading-6 text-stone-600">
                  请在周五17:00前确认发布清单，并回复仍然存在风险的项目。
                </p>
              </div>
              <div className="p-5">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-sm font-semibold">
                      Interview schedule update
                    </p>
                    <p className="mt-1 text-xs text-stone-500">
                      Talent Team · 1小时前
                    </p>
                  </div>
                  <span className="rounded-full bg-amber-50 px-2.5 py-1 text-xs font-medium text-amber-700">
                    需要回复
                  </span>
                </div>
                <p className="mt-4 text-sm leading-6 text-stone-600">
                  面试时间调整至下周二上午10:30，等待确认新的会议时间。
                </p>
              </div>
            </div>
          </article>

          <aside className="rounded-2xl bg-stone-950 p-6 text-white shadow-sm">
            <div className="flex size-10 items-center justify-center rounded-xl bg-white/10">
              <Languages className="size-5" aria-hidden="true" />
            </div>
            <h2 className="mt-5 text-lg font-semibold tracking-tight">
              从邮件到行动
            </h2>
            <p className="mt-2 text-sm leading-6 text-stone-300">
              MailPilot将自动完成摘要、翻译、分类和日期提取，并在任何写入操作前请求你的确认。
            </p>
            <div className="mt-6 space-y-3 text-sm text-stone-200">
              {[
                "读取并理解邮件内容",
                "返回可验证的结构化结果",
                "确认后添加到系统日历",
              ].map((item, index) => (
                <div key={item} className="flex items-center gap-3">
                  <span className="flex size-6 shrink-0 items-center justify-center rounded-full bg-white/10 text-xs">
                    {index + 1}
                  </span>
                  {item}
                </div>
              ))}
            </div>
          </aside>
        </section>
      </div>
    </AppLayout>
  );
}
