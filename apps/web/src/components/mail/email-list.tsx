import { Inbox } from "lucide-react";

import { EmailListItem } from "@/components/mail/email-list-item";
import type { EmailSummary } from "@/types/email";

type EmailListProps = {
  emails: EmailSummary[];
  selectedEmailId: string | null;
  onSelectEmail: (emailId: string) => void;
};

export function EmailList({
  emails,
  selectedEmailId,
  onSelectEmail,
}: EmailListProps) {
  return (
    <section className="border-border bg-card text-card-foreground overflow-hidden rounded-2xl border shadow-sm">
      <div className="border-border flex items-center justify-between border-b px-4 py-4">
        <div>
          <h2 className="font-semibold tracking-tight">收件箱</h2>
          <p className="text-muted-foreground mt-0.5 text-xs">
            {emails.length} 封演示邮件
          </p>
        </div>
        <div className="bg-muted flex size-9 items-center justify-center rounded-xl">
          <Inbox className="text-muted-foreground size-4" aria-hidden="true" />
        </div>
      </div>
      <div>
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
