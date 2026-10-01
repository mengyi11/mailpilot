"use client";

import { CalendarDays, Inbox, Settings, Sparkles } from "lucide-react";

import type { NavigationId } from "@/components/layout/sidebar";

const items = [
  { id: "inbox", label: "收件箱", icon: Inbox },
  { id: "ai", label: "AI处理", icon: Sparkles },
  { id: "calendar", label: "日历", icon: CalendarDays },
  { id: "settings", label: "设置", icon: Settings },
] satisfies { id: NavigationId; label: string; icon: typeof Inbox }[];

export function MobileNavigation({
  activePage,
  onNavigate,
}: {
  activePage: NavigationId;
  onNavigate: (page: NavigationId) => void;
}) {
  return (
    <nav
      aria-label="移动端主导航"
      className="border-sidebar-border bg-sidebar/95 fixed inset-x-0 bottom-0 z-40 grid grid-cols-4 border-t px-2 pb-[max(0.5rem,env(safe-area-inset-bottom))] backdrop-blur lg:hidden"
    >
      {items.map(({ id, label, icon: Icon }) => (
        <button
          key={id}
          type="button"
          onClick={() => onNavigate(id)}
          aria-current={activePage === id ? "page" : undefined}
          className={`flex flex-col items-center gap-1 rounded-xl px-2 py-2 text-[10px] font-medium ${
            activePage === id
              ? "text-sidebar-primary"
              : "text-sidebar-foreground/60"
          }`}
        >
          <Icon className="size-4" aria-hidden="true" />
          {label}
        </button>
      ))}
    </nav>
  );
}
