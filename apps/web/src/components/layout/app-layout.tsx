import type { ReactNode } from "react";

import { Sidebar } from "@/components/layout/sidebar";
import { TopNavigation } from "@/components/layout/top-navigation";

export function AppLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-stone-50">
      <Sidebar />
      <div className="lg:pl-64">
        <TopNavigation />
        <main>{children}</main>
      </div>
    </div>
  );
}
