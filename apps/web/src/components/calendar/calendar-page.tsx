"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  CalendarCheck,
  ChevronLeft,
  ChevronRight,
  Clock3,
  Mail,
  MapPin,
  PenLine,
  Plus,
  Trash2,
  Users,
  X,
} from "lucide-react";
import { useMemo, useState, type ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { CalendarApprovalDialog } from "@/components/calendar/calendar-approval-dialog";
import { apiRequest, ApiError } from "@/lib/api-client";
import {
  calendarEventSchema,
  calendarOverviewSchema,
  type CalendarEvent,
} from "@/lib/calendar-schema";

const weekDays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"];
const inputClass =
  "border-input bg-background h-10 w-full rounded-lg border px-3 text-sm outline-none focus:border-ring focus:ring-3 focus:ring-ring/20";

function dateKey(value: Date | string) {
  const date = typeof value === "string" ? new Date(value) : value;
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
}

function monthDays(month: Date) {
  const first = new Date(month.getFullYear(), month.getMonth(), 1);
  const mondayOffset = (first.getDay() + 6) % 7;
  const start = new Date(first);
  start.setDate(first.getDate() - mondayOffset);
  return Array.from({ length: 42 }, (_, index) => {
    const date = new Date(start);
    date.setDate(start.getDate() + index);
    return date;
  });
}

function formatTime(value: string) {
  return new Intl.DateTimeFormat("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function toLocalInput(value?: string | null) {
  const date = value ? new Date(value) : new Date();
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
  return local.toISOString().slice(0, 16);
}

export function CalendarPage() {
  const queryClient = useQueryClient();
  const [month, setMonth] = useState(
    () => new Date(new Date().getFullYear(), new Date().getMonth(), 1),
  );
  const [selectedDate, setSelectedDate] = useState(() => dateKey(new Date()));
  const [editor, setEditor] = useState<{
    mode: "create" | "edit";
    event?: CalendarEvent;
  } | null>(null);
  const [approvalCandidate, setApprovalCandidate] =
    useState<CalendarEvent | null>(null);
  const overview = useQuery({
    queryKey: ["calendar-overview"],
    queryFn: () => apiRequest("/calendar", { schema: calendarOverviewSchema }),
  });
  const refresh = () =>
    queryClient.invalidateQueries({ queryKey: ["calendar-overview"] });
  const decide = useMutation({
    mutationFn: (event: CalendarEvent) =>
      apiRequest(`/calendar/candidates/${event.id}/approve`, {
        method: "POST",
        body: JSON.stringify({
          approvalId: event.approvalId,
          payloadHash: event.approvalPayloadHash,
        }),
        schema: calendarEventSchema,
      }),
    onSuccess: () => {
      setApprovalCandidate(null);
      refresh();
    },
  });
  const reject = useMutation({
    mutationFn: (id: string) =>
      apiRequest(`/calendar/candidates/${id}/reject`, {
        method: "POST",
        schema: calendarEventSchema,
      }),
    onSuccess: refresh,
  });
  const remove = useMutation({
    mutationFn: (id: string) =>
      apiRequest(`/calendar/events/${id}`, { method: "DELETE" }),
    onSuccess: refresh,
  });
  const days = useMemo(() => monthDays(month), [month]);
  const byDay = useMemo(() => {
    const result = new Map<string, CalendarEvent[]>();
    for (const event of overview.data?.events ?? [])
      result.set(dateKey(event.startsAt), [
        ...(result.get(dateKey(event.startsAt)) ?? []),
        event,
      ]);
    return result;
  }, [overview.data]);
  const selectedEvents = byDay.get(selectedDate) ?? [];

  if (overview.isPending)
    return (
      <div className="text-muted-foreground flex min-h-[560px] items-center justify-center text-sm">
        正在读取日历…
      </div>
    );
  if (overview.isError)
    return (
      <div className="text-destructive flex min-h-[560px] items-center justify-center text-sm">
        无法读取日历，请确认后端服务正常。
      </div>
    );

  return (
    <div className="grid h-[calc(100vh-4rem)] min-h-[650px] overflow-hidden xl:grid-cols-[minmax(0,1fr)_350px]">
      <main className="min-w-0 overflow-y-auto p-5 md:p-7">
        <header className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-primary text-[11px] font-semibold tracking-[0.16em] uppercase">
              Internal calendar
            </p>
            <h1 className="mt-1 text-2xl font-semibold">日历</h1>
            <p className="text-muted-foreground mt-1 text-xs">
              确认邮件候选，或创建自己的事件。
            </p>
          </div>
          <Button onClick={() => setEditor({ mode: "create" })}>
            <Plus />
            新建事件
          </Button>
        </header>
        <section className="border-border bg-card mt-6 overflow-hidden rounded-2xl border shadow-sm">
          <div className="border-border flex items-center justify-between border-b px-5 py-4">
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="icon-sm"
                onClick={() =>
                  setMonth(
                    new Date(month.getFullYear(), month.getMonth() - 1, 1),
                  )
                }
              >
                <ChevronLeft />
              </Button>
              <h2 className="min-w-32 text-center text-sm font-semibold">
                {new Intl.DateTimeFormat("zh-CN", {
                  year: "numeric",
                  month: "long",
                }).format(month)}
              </h2>
              <Button
                variant="ghost"
                size="icon-sm"
                onClick={() =>
                  setMonth(
                    new Date(month.getFullYear(), month.getMonth() + 1, 1),
                  )
                }
              >
                <ChevronRight />
              </Button>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                const today = new Date();
                setMonth(new Date(today.getFullYear(), today.getMonth(), 1));
                setSelectedDate(dateKey(today));
              }}
            >
              今天
            </Button>
          </div>
          <div className="grid grid-cols-7 border-b">
            {weekDays.map((day) => (
              <div
                key={day}
                className="text-muted-foreground px-2 py-2 text-center text-[10px] font-semibold"
              >
                {day}
              </div>
            ))}
          </div>
          <div className="grid grid-cols-7">
            {days.map((day) => {
              const key = dateKey(day);
              const events = byDay.get(key) ?? [];
              const currentMonth = day.getMonth() === month.getMonth();
              const selected = key === selectedDate;
              const today = key === dateKey(new Date());
              return (
                <button
                  type="button"
                  key={key}
                  onClick={() => setSelectedDate(key)}
                  className={`border-border hover:bg-muted/40 min-h-24 border-r border-b p-2 text-left transition-colors ${!currentMonth ? "bg-muted/20 text-muted-foreground/55" : ""} ${selected ? "bg-primary/7 ring-primary ring-1 ring-inset" : ""}`}
                >
                  <span
                    className={`flex size-6 items-center justify-center rounded-full text-[11px] font-semibold ${today ? "bg-primary text-primary-foreground" : ""}`}
                  >
                    {day.getDate()}
                  </span>
                  <div className="mt-1 space-y-1">
                    {events.slice(0, 2).map((event) => (
                      <span
                        key={event.id}
                        className={`block truncate rounded px-1.5 py-1 text-[9px] font-medium ${event.source === "email" ? "bg-primary/12 text-foreground" : "bg-sky-500/10 text-sky-700 dark:text-sky-300"}`}
                      >
                        {formatTime(event.startsAt)} {event.title}
                      </span>
                    ))}
                    {events.length > 2 ? (
                      <span className="text-muted-foreground block px-1 text-[9px]">
                        +{events.length - 2} 项
                      </span>
                    ) : null}
                  </div>
                </button>
              );
            })}
          </div>
        </section>
      </main>
      <aside className="border-border bg-card/55 min-h-0 overflow-y-auto border-l p-5">
        <section>
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-sm font-semibold">
                {new Intl.DateTimeFormat("zh-CN", {
                  month: "long",
                  day: "numeric",
                  weekday: "short",
                }).format(new Date(`${selectedDate}T12:00:00`))}
              </h2>
              <p className="text-muted-foreground mt-0.5 text-[10px]">
                {selectedEvents.length} 个已确认事件
              </p>
            </div>
            <Button
              variant="outline"
              size="icon-sm"
              onClick={() => setEditor({ mode: "create" })}
            >
              <Plus />
            </Button>
          </div>
          <div className="mt-4 space-y-2">
            {selectedEvents.length ? (
              selectedEvents.map((event) => (
                <EventCard
                  key={event.id}
                  event={event}
                  onEdit={() => setEditor({ mode: "edit", event })}
                  onDelete={() => remove.mutate(event.id)}
                />
              ))
            ) : (
              <EmptyState>这一天没有事件</EmptyState>
            )}
          </div>
        </section>
        <section className="border-border mt-7 border-t pt-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-sm font-semibold">邮件候选</h2>
              <p className="text-muted-foreground mt-0.5 text-[10px]">
                确认后才会写入 Google Calendar
              </p>
            </div>
            <span className="bg-primary/12 text-primary rounded-full px-2 py-1 text-[10px] font-semibold">
              {overview.data?.candidates.length ?? 0}
            </span>
          </div>
          <div className="mt-4 space-y-2">
            {overview.data?.candidates.length ? (
              overview.data.candidates.map((candidate) => (
                <CandidateCard
                  key={candidate.id}
                  event={candidate}
                  busy={decide.isPending || reject.isPending}
                  onApprove={() => setApprovalCandidate(candidate)}
                  onReject={() => reject.mutate(candidate.id)}
                />
              ))
            ) : (
              <EmptyState>目前没有等待确认的候选</EmptyState>
            )}
          </div>
        </section>
      </aside>
      {editor ? (
        <EventEditor
          mode={editor.mode}
          event={editor.event}
          selectedDate={selectedDate}
          onClose={() => setEditor(null)}
          onSaved={() => {
            setEditor(null);
            refresh();
          }}
        />
      ) : null}
      {approvalCandidate ? (
        <CalendarApprovalDialog
          event={approvalCandidate}
          busy={decide.isPending}
          error={
            decide.error instanceof ApiError
              ? decide.error.message
              : decide.isError
                ? "创建失败，请稍后重试。"
                : undefined
          }
          onClose={() => {
            if (!decide.isPending) setApprovalCandidate(null);
          }}
          onConfirm={() => decide.mutate(approvalCandidate)}
        />
      ) : null}
    </div>
  );
}

function EventCard({
  event,
  onEdit,
  onDelete,
}: {
  event: CalendarEvent;
  onEdit: () => void;
  onDelete: () => void;
}) {
  return (
    <article className="border-border bg-card rounded-xl border p-3">
      <div className="flex items-start gap-3">
        <span
          className={`mt-1 h-8 w-1 rounded-full ${event.source === "email" ? "bg-primary" : "bg-sky-500"}`}
        />
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <p className="truncate text-sm font-semibold">{event.title}</p>
            {event.source === "email" ? (
              <Mail className="text-muted-foreground size-3" />
            ) : null}
          </div>
          <p className="text-muted-foreground mt-1 flex items-center gap-1 text-[10px]">
            <Clock3 className="size-3" />
            {formatTime(event.startsAt)}
            {event.endsAt ? ` – ${formatTime(event.endsAt)}` : ""}
          </p>
          {event.location ? (
            <p className="text-muted-foreground mt-1 flex items-center gap-1 truncate text-[10px]">
              <MapPin className="size-3" />
              {event.location}
            </p>
          ) : null}
          {event.attendees.length ? (
            <p className="text-muted-foreground mt-1 flex items-center gap-1 truncate text-[10px]">
              <Users className="size-3" />
              {event.attendees.join("、")}
            </p>
          ) : null}
        </div>
        <div className="flex">
          <Button variant="ghost" size="icon-xs" onClick={onEdit}>
            <PenLine />
          </Button>
          <Button variant="ghost" size="icon-xs" onClick={onDelete}>
            <Trash2 />
          </Button>
        </div>
      </div>
    </article>
  );
}
function CandidateCard({
  event,
  busy,
  onApprove,
  onReject,
}: {
  event: CalendarEvent;
  busy: boolean;
  onApprove: () => void;
  onReject: () => void;
}) {
  return (
    <article className="border-primary/20 bg-primary/5 rounded-xl border p-3">
      <div className="flex items-start gap-2">
        <CalendarCheck className="text-primary mt-0.5 size-4 shrink-0" />
        <div className="min-w-0 flex-1">
          <p className="text-xs leading-5 font-semibold">{event.title}</p>
          <p className="text-muted-foreground mt-1 text-[10px]">
            {new Intl.DateTimeFormat("zh-CN", {
              month: "short",
              day: "numeric",
              hour: "2-digit",
              minute: "2-digit",
            }).format(new Date(event.startsAt))}
          </p>
          {event.evidence ? (
            <p className="text-muted-foreground mt-2 line-clamp-2 text-[10px] italic">
              “{event.evidence}”
            </p>
          ) : null}
        </div>
      </div>
      <div className="mt-3 grid grid-cols-2 gap-2">
        <Button variant="outline" size="sm" disabled={busy} onClick={onReject}>
          <X />
          忽略
        </Button>
        <Button size="sm" disabled={busy} onClick={onApprove}>
          <CalendarCheck />
          添加
        </Button>
      </div>
    </article>
  );
}

function EventEditor({
  mode,
  event,
  selectedDate,
  onClose,
  onSaved,
}: {
  mode: "create" | "edit";
  event?: CalendarEvent;
  selectedDate: string;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [title, setTitle] = useState(event?.title ?? "");
  const [description, setDescription] = useState(event?.description ?? "");
  const [location, setLocation] = useState(event?.location ?? "");
  const [attendees, setAttendees] = useState(event?.attendees.join(", ") ?? "");
  const [start, setStart] = useState(
    event ? toLocalInput(event.startsAt) : `${selectedDate}T09:00`,
  );
  const [end, setEnd] = useState(
    event?.endsAt ? toLocalInput(event.endsAt) : `${selectedDate}T09:30`,
  );
  const [error, setError] = useState("");
  const save = useMutation({
    mutationFn: () =>
      apiRequest(
        mode === "edit" && event
          ? `/calendar/events/${event.id}`
          : "/calendar/events",
        {
          method: mode === "edit" ? "PATCH" : "POST",
          body: JSON.stringify({
            title,
            description: description || null,
            startsAt: new Date(start).toISOString(),
            endsAt: end ? new Date(end).toISOString() : null,
            timezone: "Asia/Singapore",
            location: location || null,
            attendees: attendees
              .split(",")
              .map((value) => value.trim())
              .filter(Boolean),
          }),
          schema: calendarEventSchema,
        },
      ),
    onSuccess: onSaved,
    onError: (value) =>
      setError(value instanceof Error ? value.message : "保存失败"),
  });
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <button
        type="button"
        className="absolute inset-0 bg-black/40 backdrop-blur-sm"
        onClick={onClose}
        aria-label="关闭"
      />
      <form
        className="bg-card relative w-full max-w-lg rounded-2xl border p-5 shadow-2xl"
        onSubmit={(e) => {
          e.preventDefault();
          if (!title.trim()) return setError("请输入事件名称");
          if (new Date(end) <= new Date(start))
            return setError("结束时间必须晚于开始时间");
          save.mutate();
        }}
      >
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-lg font-semibold">
              {mode === "create" ? "新建事件" : "编辑事件"}
            </h2>
            <p className="text-muted-foreground mt-1 text-xs">
              保存在 MailPilot 内部日历
            </p>
          </div>
          <Button
            type="button"
            variant="ghost"
            size="icon-sm"
            onClick={onClose}
          >
            <X />
          </Button>
        </div>
        <div className="mt-5 space-y-4">
          <Field label="事件名称">
            <input
              className={inputClass}
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="例如：项目讨论"
              autoFocus
            />
          </Field>
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="开始时间">
              <input
                className={inputClass}
                type="datetime-local"
                value={start}
                onChange={(e) => setStart(e.target.value)}
              />
            </Field>
            <Field label="结束时间">
              <input
                className={inputClass}
                type="datetime-local"
                value={end}
                onChange={(e) => setEnd(e.target.value)}
              />
            </Field>
          </div>
          <Field label="地点">
            <input
              className={inputClass}
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="会议室或线上链接"
            />
          </Field>
          <Field label="参与人邮箱">
            <input
              className={inputClass}
              value={attendees}
              onChange={(e) => setAttendees(e.target.value)}
              placeholder="name@example.com，多个邮箱用英文逗号分隔"
            />
          </Field>
          <Field label="备注">
            <textarea
              className={`${inputClass} h-24 resize-none py-3`}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="可选"
            />
          </Field>
          {error ? <p className="text-destructive text-xs">{error}</p> : null}
        </div>
        <div className="mt-6 flex justify-end gap-2">
          <Button type="button" variant="outline" onClick={onClose}>
            取消
          </Button>
          <Button type="submit" disabled={save.isPending}>
            {save.isPending ? "保存中…" : "保存事件"}
          </Button>
        </div>
      </form>
    </div>
  );
}
function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="block">
      <span className="text-muted-foreground mb-1.5 block text-xs font-medium">
        {label}
      </span>
      {children}
    </label>
  );
}
function EmptyState({ children }: { children: ReactNode }) {
  return (
    <div className="border-border text-muted-foreground rounded-xl border border-dashed px-4 py-7 text-center text-xs">
      {children}
    </div>
  );
}
