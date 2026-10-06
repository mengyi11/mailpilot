import { z } from "zod";

const emailAddressSchema = z.object({
  name: z.string(),
  email: z.email(),
});

const prioritySchema = z.enum(["high", "normal", "low"]);

export const emailDetailSchema = z.object({
  id: z.string(),
  subject: z.string(),
  sender: emailAddressSchema,
  preview: z.string(),
  receivedAt: z.iso.datetime({ offset: true }),
  isRead: z.boolean(),
  isStarred: z.boolean(),
  labels: z.array(z.string()),
  priority: prioritySchema,
  recipients: z.array(emailAddressSchema),
  bodyText: z.string(),
  bodyHtml: z.string().nullable(),
  aiOverview: z.object({
    summary: z.string(),
    category: z.string(),
    priority: prioritySchema,
    confidence: z.number().min(0).max(1),
  }),
  translation: z.object({
    sourceLanguage: z.string(),
    targetLanguage: z.string(),
    translatedBody: z.string(),
    translatedHtml: z.string().nullable(),
    ocrBlocks: z.array(
      z.object({
        imageIndex: z.number().int().nonnegative(),
        sourceText: z.string(),
        translatedText: z.string(),
      }),
    ),
    status: z.enum(["pending", "completed", "failed"]),
  }),
  actionItems: z.array(
    z.object({
      id: z.string(),
      title: z.string(),
      dueAt: z.iso.datetime({ offset: true }).nullable(),
      evidence: z.string(),
      completed: z.boolean(),
    }),
  ),
  calendarDrafts: z.array(
    z.object({
      id: z.string(),
      title: z.string(),
      startsAt: z.iso.datetime({ offset: true }),
      endsAt: z.iso.datetime({ offset: true }).nullable(),
      timezone: z.string(),
      location: z.string().nullable(),
      evidence: z.string(),
    }),
  ),
  replyDraft: z.object({
    subject: z.string(),
    body: z.string(),
    tone: z.string(),
    language: z.string(),
  }),
});

export const emailsSchema = z.array(emailDetailSchema);
export const demoEmailsSchema = emailsSchema;

export const gmailSyncResultSchema = z.object({
  accountId: z.string(),
  requested: z.number().int().nonnegative(),
  fetched: z.number().int().nonnegative(),
  created: z.number().int().nonnegative(),
  updated: z.number().int().nonnegative(),
  skipped: z.number().int().nonnegative(),
  failed: z.number().int().nonnegative(),
  mode: z.enum(["full", "incremental"]),
  historyId: z.string().nullable(),
});
