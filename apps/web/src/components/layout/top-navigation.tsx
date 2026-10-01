import { Search, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";

export function TopNavigation() {
  return (
    <header className="sticky top-0 z-10 border-b border-stone-200/80 bg-stone-50/90 px-5 py-4 backdrop-blur md:px-8">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4">
        <div>
          <p className="text-xs font-medium tracking-[0.18em] text-stone-500 uppercase">
            MailPilot Workspace
          </p>
          <h1 className="mt-1 text-xl font-semibold tracking-tight">
            早上好，Mengyi
          </h1>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="icon" aria-label="搜索邮件">
            <Search aria-hidden="true" />
          </Button>
          <Button>
            <Sparkles data-icon="inline-start" aria-hidden="true" />
            分析邮件
          </Button>
        </div>
      </div>
    </header>
  );
}
