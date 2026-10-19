"use client";

import { useMutation } from "@tanstack/react-query";
import {
  ArrowUpRight,
  Bot,
  FileText,
  History,
  LoaderCircle,
  Search,
  ShieldCheck,
  Sparkles,
  X,
} from "lucide-react";
import { type FormEvent, type ReactNode, useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { apiRequest } from "@/lib/api-client";
import {
  ragSearchResponseSchema,
  type RagSearchResponse,
} from "@/lib/email-schema";

type SearchScope = "semantic" | "current_thread" | "same_sender";

const scopeLabels: Record<SearchScope, string> = {
  semantic: "全部历史邮件",
  current_thread: "当前会话",
  same_sender: "同一发件人",
};

const suggestedQueries = [
  "最近有哪些需要关注的邮件？",
  "找出包含明确日期的邮件",
  "新加坡有哪些 AI 实习机会？",
];

type HistorySearchCardProps = {
  emailId: string;
  onOpenEmail?: (emailId: string) => void;
  onClose?: () => void;
  onSearch?: (query: string) => void;
  initialQuery?: string;
  requestId?: number;
};

async function searchHistory(
  emailId: string,
  query: string,
  scope: SearchScope,
): Promise<RagSearchResponse> {
  return apiRequest(`/rag/emails/${emailId}/search`, {
    method: "POST",
    body: JSON.stringify({ query, scope, top_k: 4 }),
    schema: ragSearchResponseSchema,
  });
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("zh-CN", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(value));
}

function formatEvidenceExcerpt(value: string) {
  const normalized = value
    .replace(/https?:\/\/\S+/gi, " ")
    .replace(/\b\S*(?:[?&][a-z0-9_.%-]+=[^\s]*)+\S*/gi, " ")
    .replace(/\b[a-z0-9_-]{42,}\b/gi, " ")
    .replace(/\/\*[\s\S]*?\*\//g, " ")
    .replace(/[^\s{}]+\s*\{[^{}]*\}/g, " ")
    .replace(/\s+/g, " ")
    .trim();

  const stillLooksTechnical = [
    "!important",
    "font-size:",
    "width:",
    "&tk=",
    "&alid=",
    "&bb=",
    "DpdM&",
  ].some((marker) => normalized.includes(marker));

  if (stillLooksTechnical || normalized.length < 24) {
    return "已找到相关邮件。请根据上方主题、发件人和日期核对原文。";
  }

  return normalized.length > 260
    ? `${normalized.slice(0, 257)}…`
    : normalized;
}

function formatInlineText(value: string): ReactNode[] {
  return value
    .split(/(\[C\d+\]|\*\*[^*]+\*\*|\*[^*]+\*)/g)
    .filter(Boolean)
    .map((part, index) => {
      if (/^\[C\d+\]$/.test(part)) {
        return (
          <strong
            key={`${part}-${index}`}
            className="bg-primary/15 text-primary mx-0.5 inline-flex rounded-md px-1.5 py-0.5 text-[11px] font-bold not-italic"
          >
            {part}
          </strong>
        );
      }
      if (part.startsWith("**") && part.endsWith("**")) {
        return <strong key={index}>{part.slice(2, -2)}</strong>;
      }
      if (part.startsWith("*") && part.endsWith("*")) {
        return <em key={index}>{part.slice(1, -1)}</em>;
      }
      return <span key={index}>{part}</span>;
    });
}

function FormattedAiAnswer({ answer }: { answer: string }) {
  const sectionTitles = new Set(["检索结论", "关键发现", "建议"]);
  const lines = answer.split("\n");

  return (
    <div className="relative mt-5 space-y-3">
      {lines.map((rawLine, index) => {
        const line = rawLine.trim();
        if (!line) return <div key={`space-${index}`} className="h-1" />;

        if (sectionTitles.has(line)) {
          return (
            <h4
              key={`${line}-${index}`}
              className="text-primary border-primary/25 border-l-2 pl-2.5 text-[13px] font-bold tracking-wide md:text-sm"
            >
              {line}
            </h4>
          );
        }

        if (/^[•-]\s*/.test(line)) {
          const content = line.replace(/^[•-]\s*/, "");
          const [mainText, senderText] = content.split(/\s+—\s+/, 2);
          return (
            <div
              key={`finding-${index}`}
              className="border-border/60 bg-background/65 flex items-start gap-3 rounded-xl border px-3.5 py-3"
            >
              <span className="bg-primary mt-2 size-1.5 shrink-0 rounded-full" />
              <p className="min-w-0 text-[13px] leading-6 md:text-sm">
                <span className="font-semibold">{formatInlineText(mainText)}</span>
                {senderText ? (
                  <em className="text-muted-foreground ml-1.5 text-xs font-normal">
                    — {senderText}
                  </em>
                ) : null}
              </p>
            </div>
          );
        }

        const currentSection = lines
          .slice(0, index)
          .reverse()
          .map((item) => item.trim())
          .find((item) => sectionTitles.has(item));

        return (
          <p
            key={`paragraph-${index}`}
            className={`max-w-5xl text-[13px] leading-6 md:text-[15px] md:leading-7 ${
              currentSection === "建议"
                ? "text-muted-foreground italic"
                : "text-foreground/85 font-medium"
            }`}
          >
            {formatInlineText(line)}
          </p>
        );
      })}
    </div>
  );
}

export function HistorySearchCard({
  emailId,
  onOpenEmail,
  onClose,
  onSearch,
  initialQuery = "",
  requestId = 0,
}: HistorySearchCardProps) {
  const [query, setQuery] = useState(initialQuery);
  const [scope, setScope] = useState<SearchScope>("semantic");
  const searchMutation = useMutation({
    mutationFn: ({
      submittedQuery,
      submittedScope,
    }: {
      submittedQuery: string;
      submittedScope: SearchScope;
    }) => searchHistory(emailId, submittedQuery, submittedScope),
  });

  useEffect(() => {
    const nextQuery = initialQuery.trim();
    if (nextQuery.length >= 2) {
      searchMutation.mutate({
        submittedQuery: nextQuery,
        submittedScope: "semantic",
      });
    }
    // requestId intentionally retriggers a repeated query from the top bar.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialQuery, requestId]);

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (query.trim().length >= 2) {
      onSearch?.(query.trim());
      searchMutation.mutate({
        submittedQuery: query.trim(),
        submittedScope: scope,
      });
    }
  }

  return (
    <section className="border-border/70 bg-card/98 flex h-full min-h-0 flex-col overflow-hidden border shadow-2xl">
      <div className="border-border/70 bg-card/95 flex shrink-0 items-center gap-3 border-b px-5 py-4 backdrop-blur-xl">
        <span className="bg-primary text-primary-foreground flex size-10 items-center justify-center rounded-2xl shadow-sm">
          <Sparkles className="size-4.5" aria-hidden="true" />
        </span>
        <div className="min-w-0 flex-1">
          <h3 className="text-base font-semibold tracking-tight">AI 邮件搜索</h3>
          <p className="text-muted-foreground mt-0.5 text-[11px]">
            查询整个邮箱，并用原邮件支持每个结论
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="border-border bg-background/80 text-muted-foreground hidden items-center gap-1 rounded-full border px-2.5 py-1 text-[10px] sm:flex">
            <ShieldCheck className="size-3" aria-hidden="true" />
            仅当前账户
          </span>
          {onClose ? (
            <Button
              type="button"
              variant="ghost"
              size="icon-sm"
              onClick={onClose}
              aria-label="关闭历史邮件搜索"
            >
              <X aria-hidden="true" />
            </Button>
          ) : null}
        </div>
      </div>

      <form
        onSubmit={submit}
        className="w-full max-w-4xl shrink-0 space-y-2.5 px-5 py-4 md:px-7"
      >
        <div className="border-input bg-background focus-within:border-primary/60 focus-within:ring-primary/12 flex items-center rounded-2xl border px-3 py-1 shadow-sm transition focus-within:ring-4">
          <Search className="text-muted-foreground size-4 shrink-0" aria-hidden="true" />
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="问邮件：客户最后选择了哪个方案？"
            aria-label="搜索历史邮件"
            className="placeholder:text-muted-foreground h-11 min-w-0 flex-1 bg-transparent px-2 text-sm outline-none"
          />
          <Button
            type="submit"
            size="sm"
            disabled={query.trim().length < 2 || searchMutation.isPending}
          >
            {searchMutation.isPending ? (
              <LoaderCircle className="animate-spin" aria-hidden="true" />
            ) : (
              "搜索"
            )}
          </Button>
        </div>
        <div className="flex items-center gap-1.5 overflow-x-auto" aria-label="搜索范围">
          <span className="text-muted-foreground mr-1 shrink-0 text-[10px] font-medium uppercase tracking-wider">
            范围
          </span>
          {(Object.keys(scopeLabels) as SearchScope[]).map((value) => (
            <button
              key={value}
              type="button"
              onClick={() => setScope(value)}
              aria-pressed={scope === value}
              className={`shrink-0 rounded-full px-2.5 py-1 text-[11px] font-medium transition ${
                scope === value
                  ? "bg-primary/15 text-primary ring-primary/20 ring-1"
                  : "bg-muted/70 text-muted-foreground hover:bg-muted hover:text-foreground"
              }`}
            >
              {scopeLabels[value]}
            </button>
          ))}
        </div>
      </form>

      {searchMutation.isError ? (
        <div className="text-destructive mx-4 mb-4 rounded-xl bg-destructive/8 p-3 text-xs">
          搜索失败：{searchMutation.error.message}
        </div>
      ) : null}

      {searchMutation.data ? (
        <div className="border-border/60 min-h-0 flex-1 overflow-y-auto border-t px-4 py-4 md:px-5">
          {searchMutation.data.no_results ? (
            <div className="py-5 text-center">
              <p className="text-sm font-medium">没有找到相关历史邮件</p>
              <p className="text-muted-foreground mt-1 text-xs leading-5">
                系统不会在没有证据时生成虚假引用。可以更换关键词或搜索范围。
              </p>
            </div>
          ) : (
            <div className="space-y-5">
              <article className="border-primary/20 from-primary/12 via-primary/6 relative overflow-hidden rounded-3xl border bg-gradient-to-br to-transparent p-5 md:p-6">
                <div className="bg-primary/15 absolute -top-16 -right-12 size-40 rounded-full blur-3xl" />
                <div className="mb-3 flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="bg-primary text-primary-foreground flex size-9 items-center justify-center rounded-xl shadow-sm">
                      <Bot className="size-4.5" aria-hidden="true" />
                    </span>
                    <div>
                      <p className="text-sm font-semibold">检索结果</p>
                      <p className="text-muted-foreground text-[10px]">
                        基于匹配邮件生成，所有结论均可追溯
                      </p>
                    </div>
                  </div>
                  {searchMutation.data.answer_mode === "local_mock" ? (
                    <span className="bg-background/80 text-muted-foreground rounded-full px-2 py-1 text-[10px]">
                      本地模拟 · 0 Token
                    </span>
                  ) : null}
                </div>
                <FormattedAiAnswer answer={searchMutation.data.answer} />
              </article>
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <FileText className="text-primary size-4" aria-hidden="true" />
                  <h4 className="text-sm font-semibold">邮件来源</h4>
                </div>
                <span className="bg-muted text-muted-foreground rounded-full px-2.5 py-1 text-[10px]">
                  {searchMutation.data.result_count} 封证据邮件
                </span>
              </div>
              {searchMutation.data.citations.map((citation) => (
                <article
                  key={citation.chunk_id}
                  className="border-border/70 bg-background hover:border-primary/30 hover:shadow-primary/5 rounded-2xl border p-4 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md"
                >
                  <div className="flex items-start gap-2">
                    <span className="bg-primary/15 text-primary mt-0.5 rounded-lg px-2 py-1 text-[10px] font-bold">
                      {citation.citation_id}
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="line-clamp-1 text-sm font-semibold">
                        {citation.subject}
                      </p>
                      <p className="text-muted-foreground mt-1 truncate text-[11px]">
                        {citation.sender} · {formatDate(citation.sent_at)}
                      </p>
                    </div>
                    <span className="text-primary text-[10px] font-medium">
                      {Math.round(citation.similarity * 100)}%
                    </span>
                  </div>
                  <p className="text-foreground/70 mt-3 line-clamp-2 text-xs leading-5">
                    {formatEvidenceExcerpt(citation.excerpt)}
                  </p>
                  {onOpenEmail ? (
                    <button
                      type="button"
                      onClick={() => onOpenEmail(citation.email_id)}
                      className="text-primary mt-3 inline-flex items-center gap-1 text-[11px] font-semibold hover:underline"
                    >
                      打开原邮件
                      <ArrowUpRight className="size-3" aria-hidden="true" />
                    </button>
                  ) : null}
                </article>
              ))}
            </div>
          )}
        </div>
      ) : (
        <div className="px-5 pb-5">
          <div className="border-border/70 bg-muted/35 rounded-2xl border border-dashed p-4">
            <div className="flex items-center gap-2 text-xs font-semibold">
              <History className="text-primary size-4" aria-hidden="true" />
              可以这样问
            </div>
            <div className="mt-3 flex flex-wrap gap-2">
              {suggestedQueries.map((suggestion) => (
                <button
                  key={suggestion}
                  type="button"
                  onClick={() => setQuery(suggestion)}
                  className="border-border bg-background text-muted-foreground hover:border-primary/35 hover:text-primary rounded-full border px-3 py-1.5 text-[11px] transition"
                >
                  {suggestion}
                </button>
              ))}
            </div>
            <p className="text-muted-foreground mt-3 text-[10px] leading-5">
              AI 只使用你的邮件生成回答，并显示可核对的来源。开发模式不会调用 Dify，不消耗 Token。
            </p>
          </div>
        </div>
      )}
    </section>
  );
}
