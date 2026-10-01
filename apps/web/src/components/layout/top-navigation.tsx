import { Search, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/layout/theme-toggle";

export function TopNavigation() {
  return (
    <header className="border-border/80 bg-background/90 sticky top-0 z-30 border-b px-4 py-3 backdrop-blur md:px-8 md:py-4">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4">
        <div>
          <p className="text-muted-foreground hidden text-xs font-medium tracking-[0.18em] uppercase sm:block">
            MailPilot Workspace
          </p>
          <h1 className="text-lg font-semibold tracking-tight sm:mt-1 sm:text-xl">
            早上好，Mengyi
          </h1>
        </div>
        <div className="flex items-center gap-2">
          <ThemeToggle />
          <Button variant="outline" size="icon" aria-label="搜索邮件">
            <Search aria-hidden="true" />
          </Button>
          <Button className="hidden sm:inline-flex">
            <Sparkles data-icon="inline-start" aria-hidden="true" />
            分析邮件
          </Button>
        </div>
      </div>
    </header>
  );
}
