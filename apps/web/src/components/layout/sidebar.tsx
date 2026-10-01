import { CalendarDays, Inbox, Mail, Settings, Sparkles } from "lucide-react";

const navigation = [
  { label: "收件箱", icon: Inbox, active: true },
  { label: "AI 处理", icon: Sparkles, active: false },
  { label: "日历候选", icon: CalendarDays, active: false },
  { label: "设置", icon: Settings, active: false },
];

export function Sidebar() {
  return (
    <aside className="border-sidebar-border bg-sidebar text-sidebar-foreground fixed inset-y-0 left-0 hidden w-64 border-r p-5 lg:block">
      <div className="flex items-center gap-3 px-2 py-3">
        <div className="bg-sidebar-primary text-sidebar-primary-foreground flex size-10 items-center justify-center rounded-xl">
          <Mail className="size-5" aria-hidden="true" />
        </div>
        <div>
          <p className="font-semibold tracking-tight">MailPilot</p>
          <p className="text-muted-foreground text-xs">邮站</p>
        </div>
      </div>

      <nav className="mt-8 space-y-1" aria-label="主导航">
        {navigation.map(({ label, icon: Icon, active }) => (
          <a
            key={label}
            href="#"
            aria-current={active ? "page" : undefined}
            className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors ${
              active
                ? "bg-sidebar-primary text-sidebar-primary-foreground"
                : "text-sidebar-foreground/65 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
            }`}
          >
            <Icon className="size-4" aria-hidden="true" />
            {label}
          </a>
        ))}
      </nav>

      <div className="bg-primary/10 absolute right-5 bottom-5 left-5 rounded-2xl p-4">
        <p className="text-foreground text-sm font-medium">AI功能准备中</p>
        <p className="text-muted-foreground mt-1 text-xs leading-5">
          当前页面使用演示数据，后续将连接FastAPI与Dify。
        </p>
      </div>
    </aside>
  );
}
