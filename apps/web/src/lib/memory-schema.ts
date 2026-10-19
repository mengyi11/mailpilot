import { z } from "zod";

export const importantContactSchema = z.object({
  name: z.string(),
  email: z.string(),
  note: z.string().nullable(),
});

export const preferencesSchema = z.object({
  id: z.string(),
  defaultLanguage: z.string(),
  translationLanguage: z.string(),
  timezone: z.string(),
  autoTranslate: z.boolean(),
  replyTone: z.enum(["professional", "friendly", "concise", "formal"]),
  workingHoursStart: z.string(),
  workingHoursEnd: z.string(),
  workingDays: z.array(z.number()),
  meetingDurationMinutes: z.number(),
  emailSignature: z.string(),
  importantContacts: z.array(importantContactSchema),
  longTermMemoryEnabled: z.boolean(),
  updatedAt: z.string(),
});

export const memoryItemSchema = z.object({
  id: z.string(),
  decision: z.enum(["accepted", "rejected"]),
  suggestionType: z.string(),
  summary: z.string(),
  sourceEmailId: z.string().nullable(),
  isActive: z.boolean(),
  createdAt: z.string(),
  updatedAt: z.string(),
  isEmailFact: z.literal(false),
});

export const memoryItemsSchema = z.array(memoryItemSchema);

export const sessionRunSchema = z.object({
  id: z.string(),
  workflowName: z.string(),
  status: z.string(),
  traceId: z.string(),
  emailId: z.string().nullable(),
  steps: z.number(),
  toolCalls: z.number(),
  approvals: z.number(),
  createdAt: z.string(),
});

export const sessionRunsSchema = z.array(sessionRunSchema);

export const replyPreviewSchema = z.object({
  tone: z.string(),
  subject: z.string(),
  body: z.string(),
});

export type Preferences = z.infer<typeof preferencesSchema>;
export type MemoryItem = z.infer<typeof memoryItemSchema>;
