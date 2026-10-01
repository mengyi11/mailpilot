import type { ReactNode } from "react";

import { Sidebar } from "@/components/layout/sidebar";
import { MobileNavigation } from "@/components/layout/mobile-navigation";
import { TopNavigation } from "@/components/layout/top-navigation";

export function AppLayout({ children }: { children: ReactNode }) {
  return (
    <div className="bg-background text-foreground min-h-screen">
      <Sidebar />
      <div className="pb-16 lg:pb-0 lg:pl-64">
        <TopNavigation />
        <main>{children}</main>
      </div>
      <MobileNavigation />
    </div>
  );
}
