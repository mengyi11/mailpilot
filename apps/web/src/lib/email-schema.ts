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

export const demoEmailsSchema = z.array(emailDetailSchema);
