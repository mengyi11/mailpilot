"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Activity,
  Brain,
  Check,
  Clock3,
  ContactRound,
  Globe2,
  Languages,
  Laptop,
  Moon,
  Palette,
  Plus,
  Save,
  ShieldCheck,
  Sparkles,
  Sun,
  Trash2,
  UserRound,
} from "lucide-react";
import { useEffect, useMemo, useState, type ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { apiRequest } from "@/lib/api-client";
import {
  memoryItemsSchema,
  preferencesSchema,
  replyPreviewSchema,
  sessionRunsSchema,
  type Preferences,
} from "@/lib/memory-schema";

type SettingsSection = "general" | "ai" | "memory" | "activity";
type ThemeChoice = "light" | "dark" | "system";
const fieldClass =
  "border-input bg-background focus:border-ring focus:ring-ring/20 h-10 w-full rounded-lg border px-3 text-sm outline-none transition-shadow focus:ring-3";
const sections = [
  {
    id: "general",
    label: "通用设置",
    description: "外观、语言与联系人",
    icon: UserRound,
  },
  { id: "ai", label: "AI 偏好", description: "回复与日程规则", icon: Sparkles },
  { id: "memory", label: "Memory", description: "长期偏好与控制", icon: Brain },
  {
    id: "activity",
    label: "运行记录",
    description: "Agent 执行轨迹",
    icon: Activity,
  },
] satisfies Array<{
  id: SettingsSection;
  label: string;
  description: string;
  icon: typeof UserRound;
}>;
const weekdays = [
  [1, "一"],
  [2, "二"],
  [3, "三"],
  [4, "四"],
  [5, "五"],
  [6, "六"],
  [7, "日"],
] as const;

function applyTheme(choice: ThemeChoice) {
  const dark =
    choice === "dark" ||
    (choice === "system" &&
      window.matchMedia("(prefers-color-scheme: dark)").matches);
  document.documentElement.classList.toggle("dark", dark);
  document.documentElement.style.colorScheme = dark ? "dark" : "light";
  window.localStorage.setItem("mailpilot-theme", choice);
  window.dispatchEvent(
    new CustomEvent("mailpilot-theme-change", { detail: choice }),
  );
}

export function MemorySettingsPage() {
  const queryClient = useQueryClient();
  const [activeSection, setActiveSection] =
    useState<SettingsSection>("general");
  const [form, setForm] = useState<Preferences | null>(null);
  const [theme, setTheme] = useState<ThemeChoice>("system");
  const [contactName, setContactName] = useState("");
  const [contactEmail, setContactEmail] = useState("");
  const preferences = useQuery({
    queryKey: ["memory-preferences"],
    queryFn: () =>
      apiRequest("/memory/preferences", { schema: preferencesSchema }),
  });
  const memories = useQuery({
    queryKey: ["memory-items"],
    queryFn: () => apiRequest("/memory/items", { schema: memoryItemsSchema }),
  });
  const runs = useQuery({
    queryKey: ["memory-session-runs"],
    queryFn: () =>
      apiRequest("/memory/session-runs", { schema: sessionRunsSchema }),
  });

  useEffect(() => {
    // The local copy is an editable form draft.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (preferences.data) setForm(preferences.data);
    const saved = window.localStorage.getItem("mailpilot-theme");
    setTheme(
      saved === "light" || saved === "dark" || saved === "system"
        ? saved
        : "system",
    );
  }, [preferences.data]);

  const isDirty = useMemo(
    () =>
      Boolean(
        form &&
        preferences.data &&
        JSON.stringify(form) !== JSON.stringify(preferences.data),
      ),
    [form, preferences.data],
  );
  const save = useMutation({
    mutationFn: (value: Preferences) =>
      apiRequest("/memory/preferences", {
        method: "PUT",
        body: JSON.stringify({
          defaultLanguage: value.defaultLanguage,
          translationLanguage: value.translationLanguage,
          timezone: value.timezone,
          autoTranslate: value.autoTranslate,
          replyTone: value.replyTone,
          workingHoursStart: value.workingHoursStart,
          workingHoursEnd: value.workingHoursEnd,
          workingDays: value.workingDays,
          meetingDurationMinutes: value.meetingDurationMinutes,
          emailSignature: value.emailSignature,
          importantContacts: value.importantContacts,
          longTermMemoryEnabled: value.longTermMemoryEnabled,
        }),
        schema: preferencesSchema,
      }),
    onSuccess: (data) => {
      setForm(data);
      queryClient.setQueryData(["memory-preferences"], data);
      queryClient.invalidateQueries({ queryKey: ["reply-preview"] });
    },
  });
  const updateMemory = useMutation({
    mutationFn: ({ id, isActive }: { id: string; isActive: boolean }) =>
      apiRequest(`/memory/items/${id}`, {
        method: "PATCH",
        body: JSON.stringify({ isActive }),
      }),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["memory-items"] }),
  });
  const deleteMemory = useMutation({
    mutationFn: (id: string) =>
      apiRequest(`/memory/items/${id}`, { method: "DELETE" }),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["memory-items"] }),
  });
  const preview = useQuery({
    queryKey: [
      "reply-preview",
      preferences.data?.replyTone,
      preferences.data?.emailSignature,
    ],
    enabled: Boolean(preferences.data),
    queryFn: () =>
      apiRequest("/memory/reply-preview", {
        method: "POST",
        body: JSON.stringify({
          recipientName: "Alex",
          purpose: "I have received your email and will follow up shortly.",
        }),
        schema: replyPreviewSchema,
      }),
  });

  if (preferences.isPending || !form)
    return <PageMessage>正在读取个性化设置…</PageMessage>;
  if (preferences.isError)
    return (
      <PageMessage error>
        无法读取设置，请确认 Gmail 与后端服务已连接。
      </PageMessage>
    );

  return (
    <div className="h-[calc(100vh-4rem)] overflow-hidden">
      <div className="grid h-full lg:grid-cols-[248px_minmax(0,1fr)]">
        <aside className="border-border bg-card/65 hidden border-r p-5 lg:flex lg:flex-col">
          <div className="px-2">
            <p className="text-primary text-[11px] font-semibold tracking-[0.16em] uppercase">
              Settings
            </p>
            <h1 className="mt-1 text-xl font-semibold">设置中心</h1>
            <p className="text-muted-foreground mt-1 text-xs leading-5">
              管理界面与 Agent 的个性化行为。
            </p>
          </div>
          <nav className="mt-6 space-y-1" aria-label="设置分类">
            {sections.map((item) => {
              const Icon = item.icon;
              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => setActiveSection(item.id)}
                  className={`flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left transition-colors ${activeSection === item.id ? "bg-sidebar-accent text-sidebar-accent-foreground shadow-[inset_3px_0_0_var(--primary)]" : "text-muted-foreground hover:bg-muted hover:text-foreground"}`}
                >
                  <Icon className="size-4" />
                  <span>
                    <span className="block text-sm font-semibold">
                      {item.label}
                    </span>
                    <span className="block text-[10px] opacity-75">
                      {item.description}
                    </span>
                  </span>
                </button>
              );
            })}
          </nav>
          <div className="border-border bg-background/70 mt-auto rounded-xl border p-3">
            <div className="flex items-center gap-2 text-xs font-semibold">
              <ShieldCheck className="text-primary size-4" />
              你的数据由你控制
            </div>
            <p className="text-muted-foreground mt-1.5 text-[10px] leading-4">
              长期 Memory 可随时停用或删除，不会被当成邮件事实。
            </p>
          </div>
        </aside>
        <main className="min-w-0 overflow-y-auto">
          <div className="mx-auto max-w-5xl px-5 py-7 md:px-8 md:py-9">
            <div className="mb-6 flex gap-2 overflow-x-auto pb-1 lg:hidden">
              {sections.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => setActiveSection(item.id)}
                  className={`shrink-0 rounded-full px-3 py-1.5 text-xs font-semibold ${activeSection === item.id ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"}`}
                >
                  {item.label}
                </button>
              ))}
            </div>
            <header className="border-border flex flex-wrap items-end justify-between gap-4 border-b pb-6">
              <div>
                <h2 className="text-2xl font-semibold tracking-tight">
                  {sections.find((item) => item.id === activeSection)?.label}
                </h2>
                <p className="text-muted-foreground mt-1 text-sm">
                  {sectionDescription(activeSection)}
                </p>
              </div>
              <div className="flex items-center gap-3">
                {isDirty ? (
                  <span className="text-muted-foreground text-xs">
                    有未保存的更改
                  </span>
                ) : save.isSuccess ? (
                  <span className="flex items-center gap-1 text-xs text-emerald-600">
                    <Check className="size-3.5" />
                    已同步
                  </span>
                ) : null}
                <Button
                  onClick={() => save.mutate(form)}
                  disabled={!isDirty || save.isPending}
                >
                  <Save />
                  {save.isPending ? "保存中…" : "保存更改"}
                </Button>
              </div>
            </header>
            <div className="mt-6">
              {activeSection === "general" ? (
                <GeneralSettings
                  form={form}
                  setForm={setForm}
                  theme={theme}
                  setTheme={(value) => {
                    setTheme(value);
                    applyTheme(value);
                  }}
                  contactName={contactName}
                  contactEmail={contactEmail}
                  setContactName={setContactName}
                  setContactEmail={setContactEmail}
                />
              ) : null}
              {activeSection === "ai" ? (
                <AiSettings
                  form={form}
                  setForm={setForm}
                  preview={preview.data}
                />
              ) : null}
              {activeSection === "memory" ? (
                <MemorySettings
                  form={form}
                  setForm={setForm}
                  memories={memories.data ?? []}
                  updateMemory={(id, isActive) =>
                    updateMemory.mutate({ id, isActive })
                  }
                  deleteMemory={(id) => deleteMemory.mutate(id)}
                />
              ) : null}
              {activeSection === "activity" ? (
                <ActivitySettings
                  runs={runs.data ?? []}
                  loading={runs.isPending}
                />
              ) : null}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

function GeneralSettings({
  form,
  setForm,
  theme,
  setTheme,
  contactName,
  contactEmail,
  setContactName,
  setContactEmail,
}: {
  form: Preferences;
  setForm: (value: Preferences) => void;
  theme: ThemeChoice;
  setTheme: (value: ThemeChoice) => void;
  contactName: string;
  contactEmail: string;
  setContactName: (value: string) => void;
  setContactEmail: (value: string) => void;
}) {
  return (
    <div className="space-y-5">
      <SettingsCard
        icon={Palette}
        title="外观"
        description="仅保存在当前设备，不会发送给 Agent。"
        badge="本地设置"
      >
        <div className="grid gap-3 sm:grid-cols-3">
          <ThemeOption
            active={theme === "light"}
            icon={Sun}
            label="日间模式"
            onClick={() => setTheme("light")}
          />
          <ThemeOption
            active={theme === "dark"}
            icon={Moon}
            label="夜间模式"
            onClick={() => setTheme("dark")}
          />
          <ThemeOption
            active={theme === "system"}
            icon={Laptop}
            label="跟随系统"
            onClick={() => setTheme("system")}
          />
        </div>
      </SettingsCard>
      <SettingsCard
        icon={Languages}
        title="语言与地区"
        description="同步给 Agent，用于翻译和日期解释。"
        badge="Agent 使用"
      >
        <div className="grid gap-4 sm:grid-cols-3">
          <Field label="界面与摘要语言">
            <select
              className={fieldClass}
              value={form.defaultLanguage}
              onChange={(e) =>
                setForm({ ...form, defaultLanguage: e.target.value })
              }
            >
              <option value="zh-CN">简体中文</option>
              <option value="en">English</option>
            </select>
          </Field>
          <Field label="默认翻译目标">
            <select
              className={fieldClass}
              value={form.translationLanguage}
              onChange={(e) =>
                setForm({ ...form, translationLanguage: e.target.value })
              }
            >
              <option value="zh-CN">简体中文</option>
              <option value="en">English</option>
            </select>
          </Field>
          <Field label="时区">
            <select
              className={fieldClass}
              value={form.timezone}
              onChange={(e) => setForm({ ...form, timezone: e.target.value })}
            >
              <option value="Asia/Singapore">新加坡（GMT+8）</option>
              <option value="Asia/Shanghai">中国标准时间</option>
              <option value="UTC">UTC</option>
            </select>
          </Field>
        </div>
        <ToggleRow
          icon={Globe2}
          title="自动翻译外语邮件"
          description="检测到非目标语言邮件时准备翻译版本"
          checked={form.autoTranslate}
          onChange={(checked) => setForm({ ...form, autoTranslate: checked })}
        />
      </SettingsCard>
      <SettingsCard
        icon={ContactRound}
        title="重要联系人"
        description="用于优先级提示，不会改变邮件事实。"
        badge={`${form.importantContacts.length} 人`}
      >
        <div className="grid gap-2 sm:grid-cols-[1fr_1.4fr_auto]">
          <input
            className={fieldClass}
            value={contactName}
            onChange={(e) => setContactName(e.target.value)}
            placeholder="联系人姓名"
          />
          <input
            className={fieldClass}
            value={contactEmail}
            onChange={(e) => setContactEmail(e.target.value)}
            placeholder="name@example.com"
          />
          <Button
            variant="outline"
            className="h-10"
            onClick={() => {
              if (!contactName.trim() || !contactEmail.trim()) return;
              setForm({
                ...form,
                importantContacts: [
                  ...form.importantContacts,
                  {
                    name: contactName.trim(),
                    email: contactEmail.trim(),
                    note: null,
                  },
                ],
              });
              setContactName("");
              setContactEmail("");
            }}
          >
            <Plus />
            添加
          </Button>
        </div>
        {form.importantContacts.length ? (
          <div className="border-border divide-border divide-y overflow-hidden rounded-xl border">
            {form.importantContacts.map((contact, index) => (
              <div
                key={`${contact.email}-${index}`}
                className="flex items-center gap-3 px-4 py-3"
              >
                <span className="bg-primary/12 text-primary flex size-9 items-center justify-center rounded-full text-xs font-bold">
                  {contact.name.slice(0, 1).toUpperCase()}
                </span>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-semibold">
                    {contact.name}
                  </p>
                  <p className="text-muted-foreground truncate text-xs">
                    {contact.email}
                  </p>
                </div>
                <Button
                  variant="ghost"
                  size="icon-sm"
                  onClick={() =>
                    setForm({
                      ...form,
                      importantContacts: form.importantContacts.filter(
                        (_, itemIndex) => itemIndex !== index,
                      ),
                    })
                  }
                >
                  <Trash2 />
                </Button>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState>尚未添加重要联系人</EmptyState>
        )}
      </SettingsCard>
    </div>
  );
}

function AiSettings({
  form,
  setForm,
  preview,
}: {
  form: Preferences;
  setForm: (value: Preferences) => void;
  preview?: { subject: string; body: string; tone: string };
}) {
  return (
    <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_360px]">
      <div className="space-y-5">
        <SettingsCard
          icon={Sparkles}
          title="回复偏好"
          description="ReplySkill 生成新草稿时读取这些设置。"
          badge="Agent 使用"
        >
          <Field label="默认回复语气">
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
              {(["professional", "friendly", "concise", "formal"] as const).map(
                (tone) => (
                  <button
                    type="button"
                    key={tone}
                    onClick={() => setForm({ ...form, replyTone: tone })}
                    className={`rounded-lg border px-3 py-2 text-xs font-semibold ${form.replyTone === tone ? "border-primary bg-primary/10" : "border-border text-muted-foreground hover:bg-muted"}`}
                  >
                    {toneLabel(tone)}
                  </button>
                ),
              )}
            </div>
          </Field>
          <Field label="邮件落款">
            <textarea
              className={`${fieldClass} h-28 resize-none py-3 leading-5`}
              value={form.emailSignature}
              onChange={(e) =>
                setForm({ ...form, emailSignature: e.target.value })
              }
              placeholder="Mengyi Xu\nMailPilot"
            />
          </Field>
        </SettingsCard>
        <SettingsCard
          icon={Clock3}
          title="工作与日程"
          description="ScheduleSkill 用它判断工作时段和会议长度。"
          badge="Agent 使用"
        >
          <div className="grid gap-4 sm:grid-cols-3">
            <Field label="工作开始">
              <input
                className={fieldClass}
                type="time"
                value={form.workingHoursStart}
                onChange={(e) =>
                  setForm({ ...form, workingHoursStart: e.target.value })
                }
              />
            </Field>
            <Field label="工作结束">
              <input
                className={fieldClass}
                type="time"
                value={form.workingHoursEnd}
                onChange={(e) =>
                  setForm({ ...form, workingHoursEnd: e.target.value })
                }
              />
            </Field>
            <Field label="默认会议时长">
              <select
                className={fieldClass}
                value={form.meetingDurationMinutes}
                onChange={(e) =>
                  setForm({
                    ...form,
                    meetingDurationMinutes: Number(e.target.value),
                  })
                }
              >
                <option value={15}>15 分钟</option>
                <option value={30}>30 分钟</option>
                <option value={45}>45 分钟</option>
                <option value={60}>60 分钟</option>
              </select>
            </Field>
          </div>
          <Field label="工作日">
            <div className="flex flex-wrap gap-2">
              {weekdays.map(([day, label]) => {
                const active = form.workingDays.includes(day);
                return (
                  <button
                    type="button"
                    key={day}
                    onClick={() =>
                      setForm({
                        ...form,
                        workingDays: active
                          ? form.workingDays.filter((value) => value !== day)
                          : [...form.workingDays, day].sort(),
                      })
                    }
                    className={`flex size-9 items-center justify-center rounded-full text-xs font-semibold ${active ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"}`}
                  >
                    {label}
                  </button>
                );
              })}
            </div>
          </Field>
        </SettingsCard>
      </div>
      <aside className="xl:sticky xl:top-0 xl:self-start">
        <SettingsCard
          icon={ShieldCheck}
          title="草稿效果预览"
          description="显示最近已保存的偏好，保存后自动更新。"
        >
          <div className="border-border bg-background overflow-hidden rounded-xl border">
            <div className="border-border border-b px-4 py-3">
              <p className="text-muted-foreground text-[10px] uppercase">
                Subject
              </p>
              <p className="mt-1 text-sm font-semibold">
                {preview?.subject ?? "Re: Follow-up"}
              </p>
            </div>
            <div className="min-h-56 px-4 py-4 text-sm leading-6 whitespace-pre-line">
              {preview?.body ?? "正在准备预览…"}
            </div>
          </div>
          <p className="text-muted-foreground text-[10px]">
            这里只生成预览，不会自动发送邮件。
          </p>
        </SettingsCard>
      </aside>
    </div>
  );
}

function MemorySettings({
  form,
  setForm,
  memories,
  updateMemory,
  deleteMemory,
}: {
  form: Preferences;
  setForm: (value: Preferences) => void;
  memories: Array<{
    id: string;
    decision: "accepted" | "rejected";
    summary: string;
    suggestionType: string;
    isActive: boolean;
  }>;
  updateMemory: (id: string, isActive: boolean) => void;
  deleteMemory: (id: string) => void;
}) {
  return (
    <div className="space-y-5">
      <SettingsCard
        icon={Brain}
        title="长期 Memory"
        description="让 Agent 参考你曾经接受或拒绝的建议。"
        badge={form.longTermMemoryEnabled ? "已开启" : "已关闭"}
      >
        <ToggleRow
          icon={Brain}
          title="允许 Agent 使用长期 Memory"
          description="关闭后记录仍保留，但 Tool 不会返回这些记录"
          checked={form.longTermMemoryEnabled}
          onChange={(checked) =>
            setForm({ ...form, longTermMemoryEnabled: checked })
          }
        />
        <div className="grid gap-3 sm:grid-cols-3">
          <Boundary title="可以影响" value="回复方式与建议排序" />
          <Boundary title="不能影响" value="邮件原文和事实判断" />
          <Boundary title="用户控制" value="查看、停用或删除" />
        </div>
      </SettingsCard>
      <SettingsCard
        icon={ShieldCheck}
        title="已保存的行为记录"
        description="只记录用户明确接受或拒绝的建议。"
        badge={`${memories.filter((item) => item.isActive).length} 条生效`}
      >
        {memories.length ? (
          <div className="space-y-2">
            {memories.map((memory) => (
              <div
                key={memory.id}
                className={`border-border rounded-xl border p-4 ${memory.isActive ? "bg-card" : "bg-muted/35 opacity-70"}`}
              >
                <div className="flex items-start gap-3">
                  <span
                    className={`rounded-full px-2 py-1 text-[10px] font-semibold ${memory.decision === "accepted" ? "bg-emerald-500/10 text-emerald-700" : "bg-red-500/10 text-red-700"}`}
                  >
                    {memory.decision === "accepted" ? "已接受" : "已拒绝"}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm leading-5">{memory.summary}</p>
                    <p className="text-muted-foreground mt-1 text-[10px]">
                      {memory.suggestionType} · 不是邮件事实
                    </p>
                  </div>
                  <div className="flex gap-1">
                    <Button
                      variant="outline"
                      size="xs"
                      onClick={() => updateMemory(memory.id, !memory.isActive)}
                    >
                      {memory.isActive ? "停用" : "启用"}
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon-xs"
                      onClick={() => deleteMemory(memory.id)}
                    >
                      <Trash2 />
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState>
            还没有行为 Memory。接受或拒绝 Agent 建议后，记录会出现在这里。
          </EmptyState>
        )}
      </SettingsCard>
    </div>
  );
}

function ActivitySettings({
  runs,
  loading,
}: {
  runs: Array<{
    id: string;
    workflowName: string;
    status: string;
    traceId: string;
    steps: number;
    toolCalls: number;
    approvals: number;
  }>;
  loading: boolean;
}) {
  return (
    <SettingsCard
      icon={Activity}
      title="Agent 运行记录"
      description="Session Memory 保存执行状态，不用于个性化推断。"
      badge={`${runs.length} 次运行`}
    >
      {loading ? (
        <EmptyState>正在读取运行记录…</EmptyState>
      ) : runs.length ? (
        <div className="border-border divide-border divide-y overflow-hidden rounded-xl border">
          {runs.map((run) => (
            <div
              key={run.id}
              className="grid gap-3 px-4 py-4 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center"
            >
              <div className="flex min-w-0 items-center gap-3">
                <span
                  className={`size-2 rounded-full ${run.status === "completed" ? "bg-emerald-500" : run.status === "failed" ? "bg-red-500" : "bg-amber-500"}`}
                />
                <div className="min-w-0">
                  <p className="truncate text-sm font-semibold">
                    {run.workflowName}
                  </p>
                  <p className="text-muted-foreground truncate font-mono text-[10px]">
                    Trace · {run.traceId}
                  </p>
                </div>
              </div>
              <div className="flex gap-2 text-[10px]">
                <Metric value={run.steps} label="Steps" />
                <Metric value={run.toolCalls} label="Tools" />
                <Metric value={run.approvals} label="Approvals" />
              </div>
            </div>
          ))}
        </div>
      ) : (
        <EmptyState>
          完成一次邮件分析后，这里会出现 Run、Step、Tool 和 Approval。
        </EmptyState>
      )}
    </SettingsCard>
  );
}

function SettingsCard({
  icon: Icon,
  title,
  description,
  badge,
  children,
}: {
  icon: typeof Brain;
  title: string;
  description: string;
  badge?: string;
  children: ReactNode;
}) {
  return (
    <section className="border-border bg-card rounded-2xl border shadow-sm">
      <header className="border-border flex items-start gap-3 border-b px-5 py-4">
        <span className="bg-primary/12 text-primary flex size-9 shrink-0 items-center justify-center rounded-xl">
          <Icon className="size-4" />
        </span>
        <div className="min-w-0 flex-1">
          <h3 className="text-sm font-semibold">{title}</h3>
          <p className="text-muted-foreground mt-0.5 text-xs leading-5">
            {description}
          </p>
        </div>
        {badge ? (
          <span className="bg-muted text-muted-foreground shrink-0 rounded-full px-2.5 py-1 text-[10px] font-semibold">
            {badge}
          </span>
        ) : null}
      </header>
      <div className="space-y-5 p-5">{children}</div>
    </section>
  );
}
function ThemeOption({
  active,
  icon: Icon,
  label,
  onClick,
}: {
  active: boolean;
  icon: typeof Sun;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`flex items-center gap-3 rounded-xl border p-3 text-left ${active ? "border-primary bg-primary/10" : "border-border hover:bg-muted"}`}
    >
      <span
        className={`flex size-9 items-center justify-center rounded-lg ${active ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"}`}
      >
        <Icon className="size-4" />
      </span>
      <span className="text-sm font-semibold">{label}</span>
      {active ? <Check className="text-primary ml-auto size-4" /> : null}
    </button>
  );
}
function ToggleRow({
  icon: Icon,
  title,
  description,
  checked,
  onChange,
}: {
  icon: typeof Brain;
  title: string;
  description: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
}) {
  return (
    <label className="bg-muted/35 flex cursor-pointer items-center gap-3 rounded-xl p-4">
      <span className="bg-background flex size-9 items-center justify-center rounded-lg">
        <Icon className="text-primary size-4" />
      </span>
      <span className="min-w-0 flex-1">
        <span className="block text-sm font-semibold">{title}</span>
        <span className="text-muted-foreground block text-xs leading-5">
          {description}
        </span>
      </span>
      <span
        className={`relative h-6 w-11 rounded-full ${checked ? "bg-primary" : "bg-muted-foreground/25"}`}
      >
        <input
          type="checkbox"
          className="sr-only"
          checked={checked}
          onChange={(event) => onChange(event.target.checked)}
        />
        <span
          className={`absolute top-1 size-4 rounded-full bg-white shadow-sm transition-transform ${checked ? "translate-x-6" : "translate-x-1"}`}
        />
      </span>
    </label>
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
    <div className="border-border bg-muted/20 text-muted-foreground rounded-xl border border-dashed px-5 py-8 text-center text-xs">
      {children}
    </div>
  );
}
function Boundary({ title, value }: { title: string; value: string }) {
  return (
    <div className="bg-muted/35 rounded-xl p-3">
      <p className="text-muted-foreground text-[10px] font-semibold uppercase">
        {title}
      </p>
      <p className="mt-1 text-xs font-medium">{value}</p>
    </div>
  );
}
function Metric({ value, label }: { value: number; label: string }) {
  return (
    <span className="bg-muted rounded-lg px-2 py-1">
      <strong>{value}</strong> {label}
    </span>
  );
}
function PageMessage({
  children,
  error = false,
}: {
  children: ReactNode;
  error?: boolean;
}) {
  return (
    <div
      className={`${error ? "text-destructive" : "text-muted-foreground"} flex min-h-[560px] items-center justify-center text-sm`}
    >
      {children}
    </div>
  );
}
function toneLabel(tone: Preferences["replyTone"]) {
  return {
    professional: "专业",
    friendly: "友好",
    concise: "简洁",
    formal: "正式",
  }[tone];
}
function sectionDescription(section: SettingsSection) {
  return {
    general: "管理此设备的显示方式，以及同步给 Agent 的语言与联系人信息。",
    ai: "决定 ReplySkill 和 ScheduleSkill 如何为你生成结果。",
    memory: "查看和控制 Agent 可以长期参考的用户行为记录。",
    activity: "检查每次 Agent Run 的步骤、工具调用和待审批操作。",
  }[section];
}
