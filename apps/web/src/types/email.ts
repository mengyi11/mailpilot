export type EmailAddress = {
  name: string;
  email: string;
};

export type EmailSummary = {
  id: string;
  subject: string;
  sender: EmailAddress;
  preview: string;
  receivedAt: string;
  isRead: boolean;
  isStarred: boolean;
  labels: string[];
  priority: "high" | "normal" | "low";
};

export type AIOverview = {
  summary: string;
  category: string;
  priority: "high" | "normal" | "low";
  confidence: number;
};

export type EmailDetailData = EmailSummary & {
  recipients: EmailAddress[];
  bodyText: string;
  aiOverview: AIOverview;
};
