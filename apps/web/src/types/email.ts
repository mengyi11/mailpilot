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

export type Translation = {
  sourceLanguage: string;
  targetLanguage: string;
  translatedBody: string;
  translatedHtml: string | null;
  ocrBlocks: Array<{
    imageIndex: number;
    sourceText: string;
    translatedText: string;
  }>;
  status: "pending" | "completed" | "failed";
};

export type ActionItem = {
  id: string;
  title: string;
  dueAt: string | null;
  evidence: string;
  completed: boolean;
};

export type CalendarDraft = {
  id: string;
  title: string;
  startsAt: string;
  endsAt: string | null;
  timezone: string;
  location: string | null;
  evidence: string;
};

export type ReplyDraft = {
  subject: string;
  body: string;
  tone: string;
  language: string;
};

export type EmailDetailData = EmailSummary & {
  recipients: EmailAddress[];
  bodyText: string;
  bodyHtml: string | null;
  aiOverview: AIOverview;
  translation: Translation;
  actionItems: ActionItem[];
  calendarDrafts: CalendarDraft[];
  replyDraft: ReplyDraft;
};
