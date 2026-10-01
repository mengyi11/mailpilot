"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { EmailDetail } from "@/components/mail/email-detail";
import { EmailList } from "@/components/mail/email-list";
import {
  InboxEmptyState,
  InboxErrorState,
  InboxLoadingState,
} from "@/components/mail/inbox-states";
import { apiRequest } from "@/lib/api-client";
import { demoEmailsSchema } from "@/lib/email-schema";

function getDemoEmails() {
  return apiRequest("/demo/emails", { schema: demoEmailsSchema });
}

export function InboxPage() {
  const [selectedEmailId, setSelectedEmailId] = useState<string | null>(null);
  const {
    data: emails = [],
    isPending,
    isError,
    isFetching,
    refetch,
  } = useQuery({
    queryKey: ["demo-emails"],
    queryFn: getDemoEmails,
  });
  const selectedEmail =
    emails.find((email) => email.id === selectedEmailId) ?? emails[0];

  return (
    <div className="mx-auto max-w-[1600px] px-4 py-5 md:px-6 md:py-6">
      <div className="mb-5">
        <p className="text-muted-foreground text-xs font-medium tracking-[0.16em] uppercase">
          Inbox
        </p>
        <h2 className="mt-1 text-2xl font-semibold tracking-tight">
          智能收件箱
        </h2>
        <p className="text-muted-foreground mt-1 text-sm">
          选择邮件，查看原文和AI提取结果。
        </p>
      </div>

      {isPending ? (
        <InboxLoadingState />
      ) : isError ? (
        <InboxErrorState
          onRetry={() => void refetch()}
          isRetrying={isFetching}
        />
      ) : emails.length === 0 ? (
        <InboxEmptyState />
      ) : (
        <div className="grid gap-4 lg:grid-cols-[300px_minmax(0,1fr)] 2xl:grid-cols-[320px_minmax(0,1fr)]">
          <EmailList
            emails={emails}
            selectedEmailId={selectedEmailId}
            onSelectEmail={setSelectedEmailId}
          />
          {selectedEmail ? <EmailDetail email={selectedEmail} /> : null}
        </div>
      )}
    </div>
  );
}
