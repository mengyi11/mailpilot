import type { EmailDetailData } from "@/types/email";

export const demoEmails: EmailDetailData[] = [
  {
    id: "demo-launch-review",
    subject: "Project launch review",
    sender: { name: "Alex Chen", email: "alex@example.com" },
    preview: "请在周五17:00前确认发布清单，并回复仍然存在风险的项目。",
    receivedAt: "2026-10-01T13:54:00+08:00",
    isRead: false,
    isStarred: true,
    labels: ["项目", "需要回复"],
    priority: "high",
    recipients: [{ name: "Mengyi Xu", email: "mengyi@example.com" }],
    bodyText:
      "Hi Mengyi,\n\nBefore Friday at 5:00 PM, please review the final launch checklist and reply with any remaining risks. We will freeze the release scope after the review.\n\nBest,\nAlex",
    aiOverview: {
      summary: "周五17:00前确认发布清单，并回复仍然存在的发布风险。",
      category: "项目协作",
      priority: "high",
      confidence: 0.94,
    },
    translation: {
      sourceLanguage: "English",
      targetLanguage: "简体中文",
      translatedBody:
        "你好，Mengyi：\n\n请在周五下午5点前检查最终发布清单，并回复仍然存在的风险。评审结束后，我们将冻结发布范围。\n\nAlex",
    },
    actionItems: [
      {
        id: "action-review-checklist",
        title: "检查最终发布清单",
        dueAt: "2026-10-02T17:00:00+08:00",
        evidence:
          "Before Friday at 5:00 PM, please review the final launch checklist",
        completed: false,
      },
      {
        id: "action-reply-risks",
        title: "回复仍然存在的发布风险",
        dueAt: "2026-10-02T17:00:00+08:00",
        evidence: "reply with any remaining risks",
        completed: false,
      },
    ],
    calendarDraft: {
      id: "calendar-launch-deadline",
      title: "发布清单最终确认",
      startsAt: "2026-10-02T17:00:00+08:00",
      endsAt: null,
      timezone: "Asia/Singapore",
      location: null,
      evidence: "Before Friday at 5:00 PM",
    },
    replyDraft: {
      subject: "Re: Project launch review",
      body: "Hi Alex,\n\nI will review the final launch checklist before Friday at 5:00 PM and send you the remaining risks.\n\nBest,\nMengyi",
      tone: "专业简洁",
      language: "English",
    },
  },
  {
    id: "demo-interview-update",
    subject: "Interview schedule update",
    sender: { name: "Talent Team", email: "talent@example.com" },
    preview: "面试时间调整至下周二上午10:30，等待确认新的会议时间。",
    receivedAt: "2026-10-01T12:40:00+08:00",
    isRead: false,
    isStarred: false,
    labels: ["面试", "日历候选"],
    priority: "high",
    recipients: [{ name: "Mengyi Xu", email: "mengyi@example.com" }],
    bodyText:
      "Hello Mengyi,\n\nYour interview has been moved to Tuesday, 6 October 2026 at 10:30 AM Singapore time. Please reply to confirm the new time.\n\nRegards,\nTalent Team",
    aiOverview: {
      summary: "面试调整至10月6日10:30，需要回复确认新的时间。",
      category: "招聘与面试",
      priority: "high",
      confidence: 0.97,
    },
    translation: {
      sourceLanguage: "English",
      targetLanguage: "简体中文",
      translatedBody:
        "你好，Mengyi：\n\n你的面试已调整至2026年10月6日星期二上午10:30（新加坡时间）。请回复确认新的时间。\n\nTalent Team",
    },
    actionItems: [
      {
        id: "action-confirm-interview",
        title: "回复确认新的面试时间",
        dueAt: null,
        evidence: "Please reply to confirm the new time.",
        completed: false,
      },
    ],
    calendarDraft: {
      id: "calendar-interview",
      title: "Interview",
      startsAt: "2026-10-06T10:30:00+08:00",
      endsAt: "2026-10-06T11:30:00+08:00",
      timezone: "Asia/Singapore",
      location: "Online meeting",
      evidence: "Tuesday, 6 October 2026 at 10:30 AM Singapore time",
    },
    replyDraft: {
      subject: "Re: Interview schedule update",
      body: "Hello,\n\nThank you for the update. I confirm that I am available on Tuesday, 6 October 2026 at 10:30 AM Singapore time.\n\nBest regards,\nMengyi",
      tone: "正式礼貌",
      language: "English",
    },
  },
  {
    id: "demo-weekly-digest",
    subject: "Weekly product digest",
    sender: { name: "Product Updates", email: "updates@example.com" },
    preview: "本周更新包含新的审批流程、通知设置和移动端体验改进。",
    receivedAt: "2026-09-30T18:20:00+08:00",
    isRead: true,
    isStarred: false,
    labels: ["资讯"],
    priority: "normal",
    recipients: [{ name: "Mengyi Xu", email: "mengyi@example.com" }],
    bodyText:
      "This week we shipped approval workflow improvements, notification preferences, and a more compact mobile navigation. No action is required.",
    aiOverview: {
      summary: "产品周报介绍审批流程、通知设置和移动端导航改进，无需采取行动。",
      category: "产品资讯",
      priority: "normal",
      confidence: 0.91,
    },
    translation: {
      sourceLanguage: "English",
      targetLanguage: "简体中文",
      translatedBody:
        "本周我们上线了审批流程优化、通知偏好设置，以及更紧凑的移动端导航。无需采取行动。",
    },
    actionItems: [],
    calendarDraft: null,
    replyDraft: {
      subject: "Re: Weekly product digest",
      body: "Thanks for sharing the weekly update. I have reviewed the latest product changes.\n\nBest,\nMengyi",
      tone: "简洁",
      language: "English",
    },
  },
];
