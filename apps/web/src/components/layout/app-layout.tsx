"use client";

import type { ReactNode } from "react";
import { useState } from "react";

import { MobileNavigation } from "@/components/layout/mobile-navigation";
import { Sidebar, type NavigationId } from "@/components/layout/sidebar";
import { TopNavigation } from "@/components/layout/top-navigation";
import { Button } from "@/components/ui/button";
import { GlobalSearchProvider } from "@/components/search/global-search-context";
import { AiSearchPage } from "@/components/search/ai-search-page";
import { MemorySettingsPage } from "@/components/settings/memory-settings-page";
import { CalendarPage } from "@/components/calendar/calendar-page";

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
    <GlobalSearchProvider>
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
            {activePage === "inbox" ? children : null}
            {activePage === "ai" ? <AiSearchPage /> : null}
            {activePage === "calendar" ? <CalendarPage /> : null}
            {activePage === "settings" ? <MemorySettingsPage /> : null}
          </main>
        </div>
        <MobileNavigation activePage={activePage} onNavigate={setActivePage} />
      </div>
    </GlobalSearchProvider>
  );
}
