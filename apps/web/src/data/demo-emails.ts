import type { EmailSummary } from "@/types/email";

export const demoEmails: EmailSummary[] = [
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
  },
];
