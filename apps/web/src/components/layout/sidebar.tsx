import { CalendarDays, Inbox, Mail, Settings, Sparkles } from "lucide-react";

const navigation = [
  { label: "收件箱", icon: Inbox, active: true },
  { label: "AI 处理", icon: Sparkles, active: false },
  { label: "日历候选", icon: CalendarDays, active: false },
  { label: "设置", icon: Settings, active: false },
];

export function Sidebar() {
  return (
    <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-stone-200 bg-white p-5 lg:block">
      <div className="flex items-center gap-3 px-2 py-3">
        <div className="flex size-10 items-center justify-center rounded-xl bg-stone-950 text-white">
          <Mail className="size-5" aria-hidden="true" />
        </div>
        <div>
          <p className="font-semibold tracking-tight">MailPilot</p>
          <p className="text-xs text-stone-500">邮站</p>
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
                ? "bg-stone-950 text-white"
                : "text-stone-600 hover:bg-stone-100 hover:text-stone-950"
            }`}
          >
            <Icon className="size-4" aria-hidden="true" />
            {label}
          </a>
        ))}
      </nav>

      <div className="absolute right-5 bottom-5 left-5 rounded-2xl bg-amber-50 p-4">
        <p className="text-sm font-medium text-amber-950">AI功能准备中</p>
        <p className="mt-1 text-xs leading-5 text-amber-800">
          当前页面使用演示数据，后续将连接FastAPI与Dify。
        </p>
      </div>
    </aside>
  );
}
