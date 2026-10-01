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
    <section className="overflow-hidden rounded-2xl border border-stone-200 bg-white shadow-sm">
      <div className="flex items-center justify-between border-b border-stone-100 px-4 py-4">
        <div>
          <h2 className="font-semibold tracking-tight">收件箱</h2>
          <p className="mt-0.5 text-xs text-stone-500">
            {emails.length} 封演示邮件
          </p>
        </div>
        <div className="flex size-9 items-center justify-center rounded-xl bg-stone-100">
          <Inbox className="size-4 text-stone-600" aria-hidden="true" />
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
