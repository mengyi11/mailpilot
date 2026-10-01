import { Inbox, RefreshCw, TriangleAlert } from "lucide-react";

import { Button } from "@/components/ui/button";

export function InboxLoadingState() {
  return (
    <div
      className="grid min-h-[680px] animate-pulse gap-5 lg:grid-cols-[360px_minmax(0,1fr)]"
      aria-label="正在读取邮件"
      aria-busy="true"
    >
      <section className="border-border bg-card overflow-hidden rounded-2xl border shadow-sm">
        <div className="border-border border-b p-4">
          <div className="bg-muted h-5 w-24 rounded" />
          <div className="bg-muted mt-2 h-3 w-16 rounded" />
        </div>
        {[0, 1, 2].map((item) => (
          <div key={item} className="border-border border-b p-4 last:border-0">
            <div className="bg-muted h-4 w-2/3 rounded" />
            <div className="bg-muted mt-3 h-3 w-full rounded" />
            <div className="bg-muted mt-2 h-3 w-4/5 rounded" />
          </div>
        ))}
      </section>
      <section className="border-border bg-card rounded-2xl border p-6 shadow-sm">
        <div className="bg-muted h-7 w-1/2 rounded" />
        <div className="bg-muted mt-5 h-16 rounded-xl" />
        <div className="bg-muted mt-5 h-40 rounded-xl" />
        <div className="mt-5 grid gap-4 md:grid-cols-2">
          <div className="bg-muted h-32 rounded-xl" />
          <div className="bg-muted h-32 rounded-xl" />
        </div>
      </section>
    </div>
  );
}

export function InboxEmptyState() {
  return (
    <section className="border-border bg-card flex min-h-[520px] flex-col items-center justify-center rounded-2xl border px-6 text-center shadow-sm">
      <div className="bg-muted flex size-14 items-center justify-center rounded-2xl">
        <Inbox className="text-muted-foreground size-6" aria-hidden="true" />
      </div>
      <h3 className="mt-4 text-lg font-semibold">收件箱是空的</h3>
      <p className="text-muted-foreground mt-2 max-w-sm text-sm leading-6">
        当前没有可显示的邮件。连接邮箱或导入演示数据后，邮件会出现在这里。
      </p>
    </section>
  );
}

type InboxErrorStateProps = {
  onRetry: () => void;
  isRetrying: boolean;
};

export function InboxErrorState({ onRetry, isRetrying }: InboxErrorStateProps) {
  return (
    <section
      className="border-destructive/30 bg-card flex min-h-[520px] flex-col items-center justify-center rounded-2xl border px-6 text-center shadow-sm"
      role="alert"
    >
      <div className="bg-destructive/10 flex size-14 items-center justify-center rounded-2xl">
        <TriangleAlert className="text-destructive size-6" aria-hidden="true" />
      </div>
      <h3 className="mt-4 text-lg font-semibold">邮件加载失败</h3>
      <p className="text-muted-foreground mt-2 max-w-sm text-sm leading-6">
        请确认 FastAPI 已在 localhost:8000 运行，然后再次尝试。
      </p>
      <Button className="mt-5" onClick={onRetry} disabled={isRetrying}>
        <RefreshCw
          className={isRetrying ? "animate-spin" : undefined}
          aria-hidden="true"
        />
        {isRetrying ? "正在重试" : "重新加载"}
      </Button>
    </section>
  );
}
