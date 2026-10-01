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
