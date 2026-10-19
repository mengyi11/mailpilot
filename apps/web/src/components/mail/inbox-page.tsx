"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { EmailDetail } from "@/components/mail/email-detail";
import { EmailList } from "@/components/mail/email-list";
import { useGlobalSearch } from "@/components/search/global-search-context";
import {
  InboxEmptyState,
  InboxErrorState,
  InboxLoadingState,
} from "@/components/mail/inbox-states";
import { apiRequest } from "@/lib/api-client";
import {
  analyzeEmailResponseSchema,
  emailsSchema,
  gmailSyncResultSchema,
  translateEmailResponseSchema,
} from "@/lib/email-schema";

function getEmails() {
  return apiRequest("/gmail/emails?limit=15", { schema: emailsSchema });
}

function syncGmail() {
  return apiRequest("/gmail/sync?limit=15", {
    method: "POST",
    schema: gmailSyncResultSchema,
  });
}

function analyzeEmail(emailId: string) {
  return apiRequest(`/emails/${emailId}/analyze`, {
    method: "POST",
    schema: analyzeEmailResponseSchema,
  });
}

function translateEmail(emailId: string) {
  return apiRequest(`/emails/${emailId}/translate`, {
    method: "POST",
    body: JSON.stringify({ targetLanguage: "zh-CN" }),
    schema: translateEmailResponseSchema,
  });
}

export function InboxPage() {
  const queryClient = useQueryClient();
  const globalSearch = useGlobalSearch();
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
  const analysisMutation = useMutation({
    mutationFn: analyzeEmail,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["gmail-emails"] });
    },
  });
  const translationMutation = useMutation({
    mutationFn: translateEmail,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["gmail-emails"] });
    },
  });
  const normalizedQuery = globalSearch.mailQuery.trim().toLocaleLowerCase();
  const visibleEmails = normalizedQuery
    ? emails.filter((email) =>
        [
          email.sender.name,
          email.sender.email,
          email.subject,
          email.preview,
        ].some((value) => value.toLocaleLowerCase().includes(normalizedQuery)),
      )
    : emails;
  const selectedEmail =
    visibleEmails.find((email) => email.id === selectedEmailId) ??
    visibleEmails[0];
  const syncMessage = syncMutation.isPending
    ? "正在同步 Gmail…"
    : syncMutation.isError
      ? "同步失败，请重试"
      : syncMutation.data
        ? syncMutation.data.fetched === 0
          ? "已是最新状态"
          : `同步完成：新增 ${syncMutation.data.created}，更新 ${syncMutation.data.updated}，索引 ${syncMutation.data.ragIndexed}`
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
            emails={visibleEmails}
            selectedEmailId={selectedEmailId}
            onSelectEmail={setSelectedEmailId}
            onSync={() => syncMutation.mutate()}
            isSyncing={syncMutation.isPending}
            syncMessage={syncMessage}
          />
          {selectedEmail ? (
            <EmailDetail
              key={selectedEmail.id}
              email={selectedEmail}
              analysis={
                analysisMutation.data?.emailId === selectedEmail.id
                  ? analysisMutation.data
                  : undefined
              }
              isAnalyzing={analysisMutation.isPending}
              analysisError={
                analysisMutation.isError ? analysisMutation.error : null
              }
              onAnalyze={() => analysisMutation.mutate(selectedEmail.id)}
              translation={
                translationMutation.data?.emailId === selectedEmail.id
                  ? translationMutation.data
                  : undefined
              }
              isTranslating={translationMutation.isPending}
              translationError={
                translationMutation.isError ? translationMutation.error : null
              }
              onTranslate={() => translationMutation.mutate(selectedEmail.id)}
            />
          ) : null}
        </div>
      )}
    </div>
  );
}
