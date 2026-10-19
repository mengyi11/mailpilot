import { z } from "zod";

export const calendarEventSchema = z.object({
  id: z.string(),
  title: z.string(),
  description: z.string().nullable(),
  startsAt: z.string(),
  endsAt: z.string().nullable(),
  timezone: z.string(),
  location: z.string().nullable(),
  attendees: z.array(z.string()),
  status: z.enum([
    "needs_clarification",
    "pending_approval",
    "executing",
    "confirmed",
    "verification_failed",
    "rejected",
  ]),
  source: z.enum(["email", "manual"]),
  emailId: z.string().nullable(),
  evidence: z.string().nullable(),
  createdAt: z.string(),
  approvalId: z.string().nullable(),
  approvalPayloadHash: z.string().nullable(),
  approvalExpiresAt: z.string().nullable(),
  providerEventId: z.string().nullable(),
  verified: z.boolean(),
});

export const calendarOverviewSchema = z.object({
  events: z.array(calendarEventSchema),
  candidates: z.array(calendarEventSchema),
});

export type CalendarEvent = z.infer<typeof calendarEventSchema>;
