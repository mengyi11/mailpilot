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
    summaryEn: z.string().nullable().default(null),
    summaryZh: z.string().nullable().default(null),
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
      status: z.enum(["pending_approval", "confirmed", "rejected"]).optional(),
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
  ragIndexed: z.number().int().nonnegative().default(0),
});

export const analyzeEmailResponseSchema = z.object({
  analysisId: z.uuid(),
  emailId: z.uuid(),
  status: z.enum(["completed", "read_only"]),
  category: z.string(),
  priority: z.enum(["low", "normal", "high"]),
  summary: z.string(),
  summaryEn: z.string().nullable(),
  summaryZh: z.string().nullable(),
  translationNeeded: z.boolean(),
  actions: z.array(
    z.object({
      title: z.string(),
      description: z.string().nullable().optional(),
      dueAt: z.iso.datetime({ offset: true }).nullable().optional(),
      evidence: z.string().nullable().optional(),
      confidence: z.number().min(0).max(1).nullable().optional(),
    }),
  ),
  calendarCandidates: z.array(
    z.object({
      id: z.uuid(),
      title: z.string(),
      startsAt: z.iso.datetime({ offset: true }),
      endsAt: z.iso.datetime({ offset: true }).nullable(),
      timezone: z.string(),
      location: z.string().nullable(),
      evidence: z.string(),
      confidence: z.number().min(0).max(1),
      status: z.string(),
    }),
  ),
  workflowRunId: z.string(),
  elapsedTime: z.number().nullable(),
  totalTokens: z.number().int().nonnegative().nullable(),
  validationMode: z.enum([
    "strict",
    "schema_repair",
    "strong_model_repair",
    "read_only_fallback",
  ]),
  readOnly: z.boolean(),
});

export const translateEmailResponseSchema = z.object({
  emailId: z.uuid(),
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
  status: z.literal("completed"),
  cached: z.boolean(),
  workflowRunId: z.string().nullable(),
  totalTokens: z.number().int().nullable(),
});

export const ragSearchResponseSchema = z.object({
  answer: z.string(),
  answer_mode: z.string(),
  answer_context: z.string(),
  citations: z.array(
    z.object({
      citation_id: z.string(),
      chunk_id: z.uuid(),
      email_id: z.uuid(),
      thread_id: z.uuid().nullable(),
      subject: z.string(),
      sender: z.string(),
      sent_at: z.iso.datetime({ offset: true }),
      excerpt: z.string(),
      similarity: z.number().min(0).max(1),
    }),
  ),
  result_count: z.number().int().nonnegative(),
  no_results: z.boolean(),
  message: z.string().nullable().optional(),
});

export type AnalyzeEmailResponse = z.infer<typeof analyzeEmailResponseSchema>;
export type TranslateEmailResponse = z.infer<
  typeof translateEmailResponseSchema
>;
export type RagSearchResponse = z.infer<typeof ragSearchResponseSchema>;
