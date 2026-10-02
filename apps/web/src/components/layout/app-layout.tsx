"use client";

import { CalendarDays, Settings, Sparkles } from "lucide-react";
import type { ReactNode } from "react";
import { useState } from "react";

import { MobileNavigation } from "@/components/layout/mobile-navigation";
import { Sidebar, type NavigationId } from "@/components/layout/sidebar";
import { TopNavigation } from "@/components/layout/top-navigation";
import { Button } from "@/components/ui/button";

const pageContent = {
  ai: {
    title: "AI 处理",
    description: "集中查看等待分析、处理中和已完成的邮件。",
    icon: Sparkles,
  },
  calendar: {
    title: "日历候选",
    description: "统一审核AI从邮件中提取的日期和事件。",
    icon: CalendarDays,
  },
  settings: {
    title: "设置",
    description: "管理邮箱连接、AI偏好、语言和审批规则。",
    icon: Settings,
  },
} as const;

function EmptyProductPage({ page }: { page: Exclude<NavigationId, "inbox"> }) {
  const item = pageContent[page];
  const Icon = item.icon;

  return (
    <div className="mx-auto max-w-7xl px-5 py-8 md:px-8">
      <section className="border-border bg-card flex min-h-[560px] flex-col items-center justify-center rounded-2xl border px-6 text-center shadow-sm">
        <div className="bg-primary/10 text-primary flex size-14 items-center justify-center rounded-2xl">
          <Icon className="size-6" aria-hidden="true" />
        </div>
        <h2 className="mt-4 text-xl font-semibold">{item.title}</h2>
        <p className="text-muted-foreground mt-2 max-w-md text-sm leading-6">
          {item.description}
        </p>
        <span className="bg-muted text-muted-foreground mt-5 rounded-full px-3 py-1 text-xs">
          页面框架已建立，业务功能将在下一阶段接入
        </span>
      </section>
    </div>
  );
}

function LoggedOutPage({ onSignIn }: { onSignIn: () => void }) {
  return (
    <main className="bg-background flex min-h-screen items-center justify-center px-6">
      <section className="border-border bg-card w-full max-w-md rounded-2xl border p-8 text-center shadow-sm">
        <p className="text-muted-foreground text-xs font-medium tracking-[0.18em] uppercase">
          MailPilot 邮站
        </p>
        <h1 className="mt-3 text-2xl font-semibold">你已退出演示账户</h1>
        <p className="text-muted-foreground mt-3 text-sm leading-6">
          当前只清除了页面会话。接入真实OAuth后，这里还会撤销服务端Session。
        </p>
        <Button className="mt-6 w-full" onClick={onSignIn}>
          返回演示工作台
        </Button>
      </section>
    </main>
  );
}

export function AppLayout({ children }: { children: ReactNode }) {
  const [collapsed, setCollapsed] = useState(false);
  const [activePage, setActivePage] = useState<NavigationId>("inbox");
  const [signedIn, setSignedIn] = useState(true);

  if (!signedIn) {
    return <LoggedOutPage onSignIn={() => setSignedIn(true)} />;
  }

  return (
    <div className="bg-background text-foreground min-h-screen">
      <TopNavigation
        activePage={activePage}
        collapsed={collapsed}
        onToggleSidebar={() => setCollapsed((value) => !value)}
      />
      <Sidebar
        collapsed={collapsed}
        activePage={activePage}
        onNavigate={setActivePage}
        onLogout={() => setSignedIn(false)}
      />
      <div
        className={`pt-16 pb-16 transition-[padding] duration-200 lg:pb-0 ${
          collapsed ? "lg:pl-16" : "lg:pl-56"
        }`}
      >
        <main>
          {activePage === "inbox" ? (
            children
          ) : (
            <EmptyProductPage page={activePage} />
          )}
        </main>
      </div>
      <MobileNavigation activePage={activePage} onNavigate={setActivePage} />
    </div>
  );
}
