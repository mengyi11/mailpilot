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
    <div className="h-[calc(100vh-4rem)] min-h-[640px] overflow-hidden">
      {isPending ? (
        <div className="p-5">
          <InboxLoadingState />
        </div>
      ) : isError ? (
        <div className="p-5">
          <InboxErrorState
            onRetry={() => void refetch()}
            isRetrying={isFetching}
          />
        </div>
      ) : emails.length === 0 ? (
        <div className="p-5">
          <InboxEmptyState />
        </div>
      ) : (
        <div className="grid h-full lg:grid-cols-[340px_minmax(0,1fr)] 2xl:grid-cols-[370px_minmax(0,1fr)]">
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
