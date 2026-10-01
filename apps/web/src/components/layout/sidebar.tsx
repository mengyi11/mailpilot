"use client";

import {
  CalendarDays,
  ChevronLeft,
  ChevronRight,
  Inbox,
  LogOut,
  Mail,
  Settings,
  Sparkles,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export type NavigationId = "inbox" | "ai" | "calendar" | "settings";

const navigation = [
  { id: "inbox", label: "收件箱", icon: Inbox },
  { id: "ai", label: "AI 处理", icon: Sparkles },
  { id: "calendar", label: "日历候选", icon: CalendarDays },
  { id: "settings", label: "设置", icon: Settings },
] satisfies { id: NavigationId; label: string; icon: typeof Inbox }[];

type SidebarProps = {
  collapsed: boolean;
  activePage: NavigationId;
  onToggle: () => void;
  onNavigate: (page: NavigationId) => void;
  onLogout: () => void;
};

export function Sidebar({
  collapsed,
  activePage,
  onToggle,
  onNavigate,
  onLogout,
}: SidebarProps) {
  return (
    <aside
      className={cn(
        "border-sidebar-border bg-sidebar text-sidebar-foreground fixed inset-y-0 left-0 z-40 hidden border-r p-4 transition-[width] duration-200 lg:flex lg:flex-col",
        collapsed ? "w-20" : "w-64",
      )}
    >
      <div
        className={cn(
          "flex items-center py-3",
          collapsed ? "justify-center" : "gap-3 px-2",
        )}
      >
        <div className="bg-sidebar-primary text-sidebar-primary-foreground flex size-10 items-center justify-center rounded-xl">
          <Mail className="size-5" aria-hidden="true" />
        </div>
        <div className={collapsed ? "hidden" : undefined}>
          <p className="font-semibold tracking-tight">MailPilot</p>
          <p className="text-muted-foreground text-xs">邮站</p>
        </div>
      </div>

      <Button
        variant="outline"
        size="icon-sm"
        className="bg-sidebar absolute top-20 -right-3 rounded-full shadow-sm"
        onClick={onToggle}
        aria-label={collapsed ? "展开导航栏" : "折叠导航栏"}
      >
        {collapsed ? <ChevronRight /> : <ChevronLeft />}
      </Button>

      <nav className="mt-8 space-y-1" aria-label="主导航">
        {navigation.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            type="button"
            title={collapsed ? label : undefined}
            aria-current={activePage === id ? "page" : undefined}
            onClick={() => onNavigate(id)}
            className={cn(
              "flex w-full items-center rounded-xl py-2.5 text-sm font-medium transition-colors",
              collapsed ? "justify-center px-2" : "gap-3 px-3",
              activePage === id
                ? "bg-sidebar-primary text-sidebar-primary-foreground"
                : "text-sidebar-foreground/65 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
            )}
          >
            <Icon className="size-4" aria-hidden="true" />
            <span className={collapsed ? "sr-only" : undefined}>{label}</span>
          </button>
        ))}
      </nav>

      <div className="mt-auto space-y-3">
        {!collapsed ? (
          <div className="bg-primary/10 rounded-2xl p-4">
            <p className="text-foreground text-sm font-medium">
              Demo Workspace
            </p>
            <p className="text-muted-foreground mt-1 text-xs leading-5">
              当前使用安全演示邮件，尚未连接真实邮箱。
            </p>
          </div>
        ) : null}
        <button
          type="button"
          title={collapsed ? "退出登录" : undefined}
          onClick={onLogout}
          className={cn(
            "text-sidebar-foreground/65 hover:bg-destructive/10 hover:text-destructive flex w-full items-center rounded-xl py-2.5 text-sm font-medium transition-colors",
            collapsed ? "justify-center px-2" : "gap-3 px-3",
          )}
        >
          <LogOut className="size-4" aria-hidden="true" />
          <span className={collapsed ? "sr-only" : undefined}>退出登录</span>
        </button>
      </div>
    </aside>
  );
}
