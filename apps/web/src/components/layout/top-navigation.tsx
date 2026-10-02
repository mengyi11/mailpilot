import { Bell, Mail, Menu, Search, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/layout/theme-toggle";
import type { NavigationId } from "@/components/layout/sidebar";

const pageTitles: Record<NavigationId, string> = {
  inbox: "早上好，Mengyi",
  ai: "AI 处理中心",
  calendar: "日历候选",
  settings: "工作区设置",
};

export function TopNavigation({
  activePage,
  collapsed,
  onToggleSidebar,
}: {
  activePage: NavigationId;
  collapsed: boolean;
  onToggleSidebar: () => void;
}) {
  return (
    <header className="border-border bg-card fixed inset-x-0 top-0 z-50 flex h-16 items-center border-b px-3 shadow-sm">
      <div className="flex min-w-0 flex-1 items-center gap-3">
        <Button
          variant="ghost"
          size="icon"
          onClick={onToggleSidebar}
          aria-label={collapsed ? "展开文件夹栏" : "折叠文件夹栏"}
          className="hidden lg:inline-flex"
        >
          <Menu aria-hidden="true" />
        </Button>
        <div className="flex w-44 shrink-0 items-center gap-2">
          <span className="bg-primary text-primary-foreground flex size-9 items-center justify-center rounded-lg">
            <Mail className="size-4" aria-hidden="true" />
          </span>
          <div className="leading-tight">
            <p className="text-sm font-semibold">MailPilot</p>
            <p className="text-muted-foreground text-[10px]">AI邮件工作台</p>
          </div>
        </div>

        <label className="bg-muted mx-auto hidden h-9 max-w-xl flex-1 items-center gap-2 rounded-lg px-3 md:flex">
          <Search className="text-muted-foreground size-4" aria-hidden="true" />
          <span className="sr-only">搜索邮件</span>
          <input
            type="search"
            placeholder="搜索邮件、联系人或主题"
            className="placeholder:text-muted-foreground w-full bg-transparent text-sm outline-none"
          />
        </label>

        <div className="ml-auto flex items-center gap-1.5">
          <span className="text-muted-foreground hidden text-xs xl:block">
            {pageTitles[activePage]}
          </span>
          <ThemeToggle />
          <Button variant="ghost" size="icon" aria-label="通知">
            <Bell aria-hidden="true" />
          </Button>
          <Button size="sm" className="hidden sm:inline-flex">
            <Sparkles data-icon="inline-start" aria-hidden="true" />
            分析邮件
          </Button>
        </div>
      </div>
    </header>
  );
}
