"use client";

import {
  CalendarDays,
  Archive,
  Inbox,
  LogOut,
  Pencil,
  Settings,
  Sparkles,
  Trash2,
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
  onNavigate: (page: NavigationId) => void;
  onLogout: () => void;
};

export function Sidebar({
  collapsed,
  activePage,
  onNavigate,
  onLogout,
}: SidebarProps) {
  return (
    <aside
      className={cn(
        "border-sidebar-border bg-sidebar text-sidebar-foreground fixed top-16 bottom-0 left-0 z-40 hidden border-r px-3 py-4 transition-[width] duration-200 lg:flex lg:flex-col",
        collapsed ? "w-16" : "w-56",
      )}
    >
      <Button
        className={cn("mb-5", collapsed ? "w-10 px-0" : "w-full justify-start")}
        title={collapsed ? "新建邮件" : undefined}
      >
        <Pencil aria-hidden="true" />
        <span className={collapsed ? "sr-only" : undefined}>新建邮件</span>
      </Button>

      {!collapsed ? (
        <p className="text-sidebar-foreground/50 mb-2 px-3 text-[10px] font-semibold tracking-[0.14em] uppercase">
          邮箱
        </p>
      ) : null}

      <nav className="space-y-1" aria-label="主导航">
        {navigation.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            type="button"
            title={collapsed ? label : undefined}
            aria-current={activePage === id ? "page" : undefined}
            onClick={() => onNavigate(id)}
            className={cn(
              "flex w-full items-center rounded-lg py-2 text-sm font-medium transition-colors",
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

      <div className="border-sidebar-border mt-4 space-y-1 border-t pt-4">
        {[
          { label: "归档", icon: Archive },
          { label: "已删除", icon: Trash2 },
        ].map(({ label, icon: Icon }) => (
          <button
            key={label}
            type="button"
            title={collapsed ? label : undefined}
            className={cn(
              "text-sidebar-foreground/65 hover:bg-sidebar-accent flex w-full items-center rounded-lg py-2 text-sm transition-colors",
              collapsed ? "justify-center px-2" : "gap-3 px-3",
            )}
          >
            <Icon className="size-4" aria-hidden="true" />
            <span className={collapsed ? "sr-only" : undefined}>{label}</span>
          </button>
        ))}
      </div>

      <div className="mt-auto space-y-3">
        {!collapsed ? (
          <div className="bg-sidebar-accent rounded-2xl p-4">
            <p className="text-sidebar-accent-foreground text-sm font-medium">
              Gmail Workspace
            </p>
            <p className="text-sidebar-foreground/65 mt-1 text-xs leading-5">
              已连接真实 Gmail，显示最近同步的 15 封邮件。
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
