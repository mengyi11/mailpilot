"use client";

import { MailOpen } from "lucide-react";
import { useState } from "react";

import { EmailList } from "@/components/mail/email-list";
import { demoEmails } from "@/data/demo-emails";

export function InboxPage() {
  const [selectedEmailId, setSelectedEmailId] = useState<string | null>(
    demoEmails[0]?.id ?? null,
  );

  return (
    <div className="mx-auto max-w-7xl px-5 py-6 md:px-8 md:py-8">
      <div className="mb-5">
        <p className="text-xs font-medium tracking-[0.16em] text-stone-500 uppercase">
          Inbox
        </p>
        <h2 className="mt-1 text-2xl font-semibold tracking-tight">
          智能收件箱
        </h2>
        <p className="mt-1 text-sm text-stone-500">
          选择邮件，查看原文和AI提取结果。
        </p>
      </div>

      <div className="grid min-h-[680px] gap-5 lg:grid-cols-[360px_minmax(0,1fr)]">
        <EmailList
          emails={demoEmails}
          selectedEmailId={selectedEmailId}
          onSelectEmail={setSelectedEmailId}
        />
        <section className="flex min-h-80 items-center justify-center rounded-2xl border border-dashed border-stone-300 bg-white p-8 text-center">
          <div>
            <MailOpen
              className="mx-auto size-8 text-stone-300"
              aria-hidden="true"
            />
            <p className="mt-4 text-sm font-medium">邮件详情即将接入</p>
            <p className="mt-1 text-xs text-stone-500">
              当前已选择：{selectedEmailId ?? "无"}
            </p>
          </div>
        </section>
      </div>
    </div>
  );
}
