"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { EmailDetail } from "@/components/mail/email-detail";
import { EmailList } from "@/components/mail/email-list";
import {
  InboxEmptyState,
  InboxErrorState,
  InboxLoadingState,
} from "@/components/mail/inbox-states";
import { apiRequest } from "@/lib/api-client";
import { emailsSchema, gmailSyncResultSchema } from "@/lib/email-schema";

function getEmails() {
  return apiRequest("/gmail/emails?limit=15", { schema: emailsSchema });
}

function syncGmail() {
  return apiRequest("/gmail/sync?limit=15", {
    method: "POST",
    schema: gmailSyncResultSchema,
  });
}

export function InboxPage() {
  const queryClient = useQueryClient();
  const [selectedEmailId, setSelectedEmailId] = useState<string | null>(null);
  const {
    data: emails = [],
    isPending,
    isError,
    isFetching,
    refetch,
  } = useQuery({
    queryKey: ["gmail-emails"],
    queryFn: getEmails,
  });
  const syncMutation = useMutation({
    mutationFn: syncGmail,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["gmail-emails"] });
    },
  });
  const selectedEmail =
    emails.find((email) => email.id === selectedEmailId) ?? emails[0];
  const syncMessage = syncMutation.isPending
    ? "正在同步 Gmail…"
    : syncMutation.isError
      ? "同步失败，请重试"
      : syncMutation.data
        ? syncMutation.data.fetched === 0
          ? "已是最新状态"
          : `同步完成：新增 ${syncMutation.data.created}，更新 ${syncMutation.data.updated}`
        : null;

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
            onSync={() => syncMutation.mutate()}
            isSyncing={syncMutation.isPending}
            syncMessage={syncMessage}
          />
          {selectedEmail ? <EmailDetail email={selectedEmail} /> : null}
        </div>
      )}
    </div>
  );
}
