import { ListFilter, RefreshCw } from "lucide-react";

import { EmailListItem } from "@/components/mail/email-list-item";
import type { EmailSummary } from "@/types/email";

type EmailListProps = {
  emails: EmailSummary[];
  selectedEmailId: string | null;
  onSelectEmail: (emailId: string) => void;
  onSync: () => void;
  isSyncing: boolean;
  syncMessage: string | null;
};

export function EmailList({
  emails,
  selectedEmailId,
  onSelectEmail,
  onSync,
  isSyncing,
  syncMessage,
}: EmailListProps) {
  return (
    <section className="border-border bg-card text-card-foreground flex h-full min-h-0 flex-col overflow-hidden border-r">
      <div className="border-border flex h-16 shrink-0 items-center justify-between border-b px-4">
        <div>
          <h2 className="font-semibold tracking-tight">收件箱</h2>
          <p className="text-muted-foreground mt-0.5 max-w-52 truncate text-[11px]">
            {syncMessage ?? `${emails.length} 封邮件`}
          </p>
        </div>
        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={onSync}
            disabled={isSyncing}
            className="text-muted-foreground hover:bg-muted flex size-8 items-center justify-center rounded-lg disabled:opacity-50"
            aria-label="同步 Gmail"
            title="同步 Gmail"
          >
            <RefreshCw
              className={`size-4 ${isSyncing ? "animate-spin" : ""}`}
              aria-hidden="true"
            />
          </button>
          <button
            type="button"
            className="text-muted-foreground hover:bg-muted flex size-8 items-center justify-center rounded-lg"
            aria-label="筛选邮件"
          >
            <ListFilter className="size-4" aria-hidden="true" />
          </button>
        </div>
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain">
        {emails.map((email) => (
          <EmailListItem
            key={email.id}
            email={email}
            selected={email.id === selectedEmailId}
            onSelect={onSelectEmail}
          />
        ))}
      </div>
    </section>
  );
}
