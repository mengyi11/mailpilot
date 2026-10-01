import { CalendarDays, Inbox, Settings, Sparkles } from "lucide-react";

const items = [
  { label: "收件箱", icon: Inbox, active: true },
  { label: "AI处理", icon: Sparkles, active: false },
  { label: "日历", icon: CalendarDays, active: false },
  { label: "设置", icon: Settings, active: false },
];

export function MobileNavigation() {
  return (
    <nav
      aria-label="移动端主导航"
      className="border-sidebar-border bg-sidebar/95 fixed inset-x-0 bottom-0 z-40 grid grid-cols-4 border-t px-2 pb-[max(0.5rem,env(safe-area-inset-bottom))] backdrop-blur lg:hidden"
    >
      {items.map(({ label, icon: Icon, active }) => (
        <a
          key={label}
          href="#"
          aria-current={active ? "page" : undefined}
          className={`flex flex-col items-center gap-1 rounded-xl px-2 py-2 text-[10px] font-medium ${
            active ? "text-sidebar-primary" : "text-sidebar-foreground/60"
          }`}
        >
          <Icon className="size-4" aria-hidden="true" />
          {label}
        </a>
      ))}
    </nav>
  );
}
