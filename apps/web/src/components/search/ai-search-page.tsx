"use client";

import { useQuery } from "@tanstack/react-query";
import { History, Search, SearchX, ShieldCheck, Sparkles } from "lucide-react";
import { useState } from "react";

import { HistorySearchCard } from "@/components/mail/history-search-card";
import { useGlobalSearch } from "@/components/search/global-search-context";
import { apiRequest } from "@/lib/api-client";
import { emailsSchema } from "@/lib/email-schema";

function getEmails() {
  return apiRequest("/gmail/emails?limit=15", { schema: emailsSchema });
}

type SearchHistoryItem = {
  query: string;
  searchedAt: string;
};

function loadSearchHistory(): SearchHistoryItem[] {
  if (typeof window === "undefined") return [];
  try {
    const value = window.localStorage.getItem("mailpilot-ai-search-history");
    return value ? (JSON.parse(value) as SearchHistoryItem[]) : [];
  } catch {
    return [];
  }
}

export function AiSearchPage() {
  const globalSearch = useGlobalSearch();
  const [activeView, setActiveView] = useState<"search" | "history">("search");
  const [searchHistory, setSearchHistory] =
    useState<SearchHistoryItem[]>(loadSearchHistory);
  const { data: emails = [], isPending, isError } = useQuery({
    queryKey: ["gmail-emails"],
    queryFn: getEmails,
  });

  if (isPending) {
    return (
      <div className="text-muted-foreground flex min-h-[560px] items-center justify-center text-sm">
        正在准备 AI 邮件搜索…
      </div>
    );
  }

  if (isError || emails.length === 0) {
    return (
      <div className="flex min-h-[560px] flex-col items-center justify-center text-center">
        <SearchX className="text-muted-foreground size-8" aria-hidden="true" />
        <p className="mt-3 text-sm font-semibold">暂时无法使用 AI 搜索</p>
        <p className="text-muted-foreground mt-1 text-xs">
          请先同步至少一封邮件，然后重新进入此页面。
        </p>
      </div>
    );
  }

  function rememberSearch(query: string) {
    const normalized = query.trim();
    if (!normalized) return;
    setSearchHistory((current) => {
      const next = [
        { query: normalized, searchedAt: new Date().toISOString() },
        ...current.filter((item) => item.query !== normalized),
      ].slice(0, 10);
      window.localStorage.setItem(
        "mailpilot-ai-search-history",
        JSON.stringify(next),
      );
      return next;
    });
  }

  function runSearch(query: string) {
    setActiveView("search");
    rememberSearch(query);
    globalSearch.searchAi(query);
  }

  return (
    <div className="grid h-[calc(100vh-4rem)] min-h-[620px] w-full overflow-hidden lg:grid-cols-[230px_minmax(0,1fr)]">
      <aside className="border-border bg-secondary/35 hidden min-h-0 flex-col border-r p-4 lg:flex">
        <div className="flex items-center gap-2 px-2 py-2">
          <span className="bg-primary text-primary-foreground flex size-9 items-center justify-center rounded-xl">
            <Sparkles className="size-4" aria-hidden="true" />
          </span>
          <div>
            <p className="text-sm font-semibold">AI 工作区</p>
            <p className="text-muted-foreground text-[10px]">邮件知识检索</p>
          </div>
        </div>

        <nav className="mt-5 space-y-1" aria-label="AI工具">
          <button
            type="button"
            onClick={() => setActiveView("search")}
            className={`flex w-full items-center gap-2 rounded-xl px-3 py-2.5 text-sm font-semibold ${
              activeView === "search"
                ? "bg-sidebar-accent text-sidebar-accent-foreground shadow-[inset_3px_0_0_var(--primary)]"
                : "text-muted-foreground hover:bg-muted hover:text-foreground"
            }`}
          >
            <Search className="size-4" aria-hidden="true" />
            智能搜索
          </button>
          <button
            type="button"
            onClick={() => setActiveView("history")}
            className={`flex w-full items-center gap-2 rounded-xl px-3 py-2.5 text-sm font-semibold ${
              activeView === "history"
                ? "bg-sidebar-accent text-sidebar-accent-foreground shadow-[inset_3px_0_0_var(--primary)]"
                : "text-muted-foreground hover:bg-muted hover:text-foreground"
            }`}
          >
            <History className="size-4" aria-hidden="true" />
            搜索记录
            {searchHistory.length > 0 ? (
              <span className="bg-muted ml-auto rounded-full px-2 py-0.5 text-[9px]">
                {searchHistory.length}
              </span>
            ) : null}
          </button>
        </nav>

        <div className="border-border mt-5 border-t pt-5">
          <p className="text-muted-foreground px-2 text-[10px] font-semibold tracking-[0.14em] uppercase">
            快捷提问
          </p>
          <div className="mt-2 space-y-1.5">
            {[
              "最近有哪些重要邮件？",
              "找出包含明确日期的邮件",
              "有哪些 AI 实习机会？",
            ].map((question) => (
              <button
                key={question}
                type="button"
                onClick={() => runSearch(question)}
                className="text-muted-foreground hover:bg-muted hover:text-foreground w-full rounded-lg px-2.5 py-2 text-left text-[11px] leading-4"
              >
                {question}
              </button>
            ))}
          </div>
        </div>

        <div className="border-border bg-card/70 mt-auto rounded-2xl border p-3">
          <div className="flex items-center gap-2 text-xs font-semibold">
            <ShieldCheck className="text-primary size-4" aria-hidden="true" />
            隐私保护
          </div>
          <p className="text-muted-foreground mt-1.5 text-[10px] leading-4">
            仅检索当前账户邮件，并为答案提供可核对的来源。
          </p>
        </div>
      </aside>

      <main className="min-w-0 overflow-hidden [&>section]:border-0 [&>section]:shadow-none">
        {activeView === "search" ? (
          <HistorySearchCard
            key={globalSearch.requestId}
            emailId={emails[0].id}
            initialQuery={globalSearch.aiQuery}
            requestId={globalSearch.requestId}
            onSearch={rememberSearch}
          />
        ) : (
          <section className="h-full overflow-y-auto px-7 py-6 md:px-10 md:py-8">
            <div className="max-w-4xl">
              <p className="text-primary text-xs font-semibold tracking-[0.14em] uppercase">
                Search history
              </p>
              <div className="mt-2 flex items-end justify-between gap-4">
                <div>
                  <h2 className="text-2xl font-semibold tracking-tight">搜索记录</h2>
                  <p className="text-muted-foreground mt-1 text-sm">
                    重新打开近期问题，继续检索你的邮件知识库。
                  </p>
                </div>
                {searchHistory.length > 0 ? (
                  <button
                    type="button"
                    onClick={() => {
                      setSearchHistory([]);
                      window.localStorage.removeItem(
                        "mailpilot-ai-search-history",
                      );
                    }}
                    className="text-muted-foreground hover:text-destructive text-xs"
                  >
                    清空记录
                  </button>
                ) : null}
              </div>

              {searchHistory.length > 0 ? (
                <div className="border-border mt-7 overflow-hidden rounded-2xl border bg-card">
                  {searchHistory.map((item, index) => (
                    <button
                      key={`${item.query}-${item.searchedAt}`}
                      type="button"
                      onClick={() => runSearch(item.query)}
                      className="border-border hover:bg-muted/60 flex w-full items-center gap-4 border-b px-5 py-4 text-left last:border-b-0"
                    >
                      <span className="bg-primary/12 text-primary flex size-9 shrink-0 items-center justify-center rounded-xl">
                        <Search className="size-4" aria-hidden="true" />
                      </span>
                      <span className="min-w-0 flex-1">
                        <span className="block truncate text-sm font-semibold">
                          {item.query}
                        </span>
                        <span className="text-muted-foreground mt-1 block text-[11px]">
                          {new Intl.DateTimeFormat("zh-CN", {
                            month: "short",
                            day: "numeric",
                            hour: "2-digit",
                            minute: "2-digit",
                          }).format(new Date(item.searchedAt))}
                        </span>
                      </span>
                      <span className="text-muted-foreground text-xs">
                        再次搜索
                      </span>
                      <span className="sr-only">记录 {index + 1}</span>
                    </button>
                  ))}
                </div>
              ) : (
                <div className="border-border bg-muted/25 mt-7 rounded-2xl border border-dashed px-6 py-14 text-center">
                  <History className="text-muted-foreground mx-auto size-7" aria-hidden="true" />
                  <p className="mt-3 text-sm font-semibold">还没有搜索记录</p>
                  <p className="text-muted-foreground mt-1 text-xs">
                    完成一次 AI 邮件搜索后，问题会保存在这里。
                  </p>
                </div>
              )}
            </div>
          </section>
        )}
      </main>
    </div>
  );
}
