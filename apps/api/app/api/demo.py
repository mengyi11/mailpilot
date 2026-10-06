from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict

from app.api.demo_messages import (
    GEMINI_ENTERPRISE_BODY,
    GEMINI_ENTERPRISE_TRANSLATION,
    GROUP_DYNAMICS_BODY,
    GROUP_DYNAMICS_TRANSLATION,
)


def to_camel(value: str) -> str:
    first, *rest = value.split("_")
    return first + "".join(part.capitalize() for part in rest)


class ApiModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class EmailAddress(ApiModel):
    name: str
    email: str


class AiOverview(ApiModel):
    summary: str
    category: str
    priority: str
    confidence: float


class Translation(ApiModel):
    source_language: str
    target_language: str
    translated_body: str
    translated_html: str | None = None
    ocr_blocks: list[dict] = []
    status: str = "completed"


class ActionItem(ApiModel):
    id: str
    title: str
    due_at: datetime | None
    evidence: str
    completed: bool


class CalendarDraft(ApiModel):
    id: str
    title: str
    starts_at: datetime
    ends_at: datetime | None
    timezone: str
    location: str | None
    evidence: str


class ReplyDraft(ApiModel):
    subject: str
    body: str
    tone: str
    language: str


class DemoEmail(ApiModel):
    id: str
    subject: str
    sender: EmailAddress
    preview: str
    received_at: datetime
    is_read: bool
    is_starred: bool
    labels: list[str]
    priority: str
    recipients: list[EmailAddress]
    body_text: str
    ai_overview: AiOverview
    translation: Translation
    action_items: list[ActionItem]
    calendar_drafts: list[CalendarDraft]
    reply_draft: ReplyDraft


router = APIRouter(prefix="/demo", tags=["demo"])


@router.get(
    "/emails",
    response_model=list[DemoEmail],
    summary="List safe demonstration emails",
)
async def list_demo_emails() -> list[DemoEmail]:
    """Return fictional emails so the UI can be developed without inbox access."""
    return [
        DemoEmail(
            id="ntu-group-dynamics-study",
            subject="Invitation: A Study on Group Dynamics",
            sender=EmailAddress(
                name="NTU Economics Research Team",
                email="economics-study@ntu.edu.sg",
            ),
            preview="参加约80分钟的经济学研究，可选择10月5日或7日的8个场次，平均报酬约S$15。",
            received_at="2026-10-01T09:15:00+08:00",
            is_read=False,
            is_starred=True,
            labels=["研究招募", "需要报名"],
            priority="high",
            recipients=[EmailAddress(name="NTU Students", email="students@ntu.edu.sg")],
            body_text=GROUP_DYNAMICS_BODY,
            ai_overview=AiOverview(
                summary="NTU经济学研究招募参与者，时长约80分钟，平均报酬约S$15；可从10月5日和7日的8个场次中选择并通过Qualtrics报名。",
                category="校园活动",
                priority="high",
                confidence=0.98,
            ),
            translation=Translation(
                source_language="English",
                target_language="简体中文",
                translated_body=GROUP_DYNAMICS_TRANSLATION,
            ),
            action_items=[
                ActionItem(
                    id="action-register-study",
                    title="选择场次并完成研究报名",
                    due_at=None,
                    evidence="If you are interested in participating, please register",
                    completed=False,
                )
            ],
            calendar_drafts=[
                CalendarDraft(id="study-slot-1", title="群体动力学研究 · 场次1", starts_at="2026-10-05T10:40:00+08:00", ends_at="2026-10-05T12:00:00+08:00", timezone="Asia/Singapore", location="ComLab 6 · SHHK-02-41", evidence="Timeslot 1: 10:40 am - 12:00 pm (ComLab 6)"),
                CalendarDraft(id="study-slot-2", title="群体动力学研究 · 场次2", starts_at="2026-10-05T11:15:00+08:00", ends_at="2026-10-05T12:35:00+08:00", timezone="Asia/Singapore", location="CATI Lab · SHHK-02-39", evidence="Timeslot 2: 11:15 am - 12:35 pm (CATI Lab)"),
                CalendarDraft(id="study-slot-3", title="群体动力学研究 · 场次3", starts_at="2026-10-05T15:40:00+08:00", ends_at="2026-10-05T17:00:00+08:00", timezone="Asia/Singapore", location="ComLab 6 · SHHK-02-41", evidence="Timeslot 3: 15:40 pm - 17:00 pm (ComLab 6)"),
                CalendarDraft(id="study-slot-4", title="群体动力学研究 · 场次4", starts_at="2026-10-05T16:15:00+08:00", ends_at="2026-10-05T17:35:00+08:00", timezone="Asia/Singapore", location="CATI Lab · SHHK-02-39", evidence="Timeslot 4: 16:15 pm - 17:35 pm (CATI Lab)"),
                CalendarDraft(id="study-slot-5", title="群体动力学研究 · 场次5", starts_at="2026-10-07T10:40:00+08:00", ends_at="2026-10-07T12:00:00+08:00", timezone="Asia/Singapore", location="ComLab 6 · SHHK-02-41", evidence="Timeslot 5: 10:40 am - 12:00 pm (ComLab 6)"),
                CalendarDraft(id="study-slot-6", title="群体动力学研究 · 场次6", starts_at="2026-10-07T11:15:00+08:00", ends_at="2026-10-07T12:35:00+08:00", timezone="Asia/Singapore", location="CATI Lab · SHHK-02-39", evidence="Timeslot 6: 11:15 am - 12:35 pm (CATI Lab)"),
                CalendarDraft(id="study-slot-7", title="群体动力学研究 · 场次7", starts_at="2026-10-07T15:40:00+08:00", ends_at="2026-10-07T17:00:00+08:00", timezone="Asia/Singapore", location="ComLab 6 · SHHK-02-41", evidence="Timeslot 7: 15:40 pm - 17:00 pm (ComLab 6)"),
                CalendarDraft(id="study-slot-8", title="群体动力学研究 · 场次8", starts_at="2026-10-07T16:15:00+08:00", ends_at="2026-10-07T17:35:00+08:00", timezone="Asia/Singapore", location="CATI Lab · SHHK-02-39", evidence="Timeslot 8: 16:15 pm - 17:35 pm (CATI Lab)"),
            ],
            reply_draft=ReplyDraft(
                subject="Re: A Study on Group Dynamics",
                body="Dear Research Team,\n\nI am interested in participating and will register for my preferred time slot using the form.\n\nBest regards,\nMengyi",
                tone="正式礼貌",
                language="English",
            ),
        ),
        DemoEmail(
            id="ntu-gemini-enterprise",
            subject="Explore Gemini Enterprise with your NTU account",
            sender=EmailAddress(name="NTU InsPIRE", email="inspire@ntu.edu.sg"),
            preview="NTU学生可使用受企业数据保护的Gemini Enterprise，并获得视频、课程和认证学习资源。",
            received_at="2026-10-01T08:30:00+08:00",
            is_read=False,
            is_starred=False,
            labels=["校园资讯", "AI工具"],
            priority="normal",
            recipients=[EmailAddress(name="NTU Students", email="students@ntu.edu.sg")],
            body_text=GEMINI_ENTERPRISE_BODY,
            ai_overview=AiOverview(
                summary="NTU学生可通过学校账户使用Gemini Enterprise；聊天和文件受企业数据保护，同时可访问AI入门、实践课程和认证资源。",
                category="校园资讯",
                priority="normal",
                confidence=0.96,
            ),
            translation=Translation(
                source_language="English",
                target_language="简体中文",
                translated_body=GEMINI_ENTERPRISE_TRANSLATION,
            ),
            action_items=[],
            calendar_drafts=[],
            reply_draft=ReplyDraft(
                subject="Re: Gemini Enterprise at NTU",
                body="Thank you for sharing these resources. I will explore Gemini Enterprise using my NTU account.\n\nBest regards,\nMengyi",
                tone="简洁礼貌",
                language="English",
            ),
        ),
        DemoEmail(
            id="demo-launch-review",
            subject="Project launch review",
            sender=EmailAddress(name="Alex Chen", email="alex@example.com"),
            preview="请在周五17:00前确认发布清单，并回复仍然存在风险的项目。",
            received_at="2026-10-01T13:54:00+08:00",
            is_read=False,
            is_starred=True,
            labels=["项目", "需要回复"],
            priority="high",
            recipients=[EmailAddress(name="Mengyi Xu", email="mengyi@example.com")],
            body_text=(
                "Hi Mengyi,\n\nBefore Friday at 5:00 PM, please review the final "
                "launch checklist and reply with any remaining risks. We will freeze "
                "the release scope after the review.\n\nBest,\nAlex"
            ),
            ai_overview=AiOverview(
                summary="周五17:00前确认发布清单，并回复仍然存在的发布风险。",
                category="项目协作",
                priority="high",
                confidence=0.94,
            ),
            translation=Translation(
                source_language="English",
                target_language="简体中文",
                translated_body=(
                    "你好，Mengyi：\n\n请在周五下午5点前检查最终发布清单，并回复仍然"
                    "存在的风险。评审结束后，我们将冻结发布范围。\n\nAlex"
                ),
            ),
            action_items=[
                ActionItem(
                    id="action-review-checklist",
                    title="检查最终发布清单",
                    due_at="2026-10-02T17:00:00+08:00",
                    evidence="Before Friday at 5:00 PM, please review the final launch checklist",
                    completed=False,
                ),
                ActionItem(
                    id="action-reply-risks",
                    title="回复仍然存在的发布风险",
                    due_at="2026-10-02T17:00:00+08:00",
                    evidence="reply with any remaining risks",
                    completed=False,
                ),
            ],
            calendar_drafts=[
                CalendarDraft(
                    id="calendar-launch-deadline",
                    title="发布清单最终确认",
                    starts_at="2026-10-02T17:00:00+08:00",
                    ends_at=None,
                    timezone="Asia/Singapore",
                    location=None,
                    evidence="Before Friday at 5:00 PM",
                ),
                CalendarDraft(
                    id="calendar-scope-freeze",
                    title="发布范围冻结",
                    starts_at="2026-10-02T17:30:00+08:00",
                    ends_at=None,
                    timezone="Asia/Singapore",
                    location=None,
                    evidence="We will freeze the release scope after the review.",
                ),
            ],
            reply_draft=ReplyDraft(
                subject="Re: Project launch review",
                body=(
                    "Hi Alex,\n\nI will review the final launch checklist before Friday "
                    "at 5:00 PM and send you the remaining risks.\n\nBest,\nMengyi"
                ),
                tone="专业简洁",
                language="English",
            ),
        ),
        DemoEmail(
            id="demo-interview-update",
            subject="Interview schedule update",
            sender=EmailAddress(name="Talent Team", email="talent@example.com"),
            preview="面试时间调整至下周二上午10:30，等待确认新的会议时间。",
            received_at="2026-10-01T12:40:00+08:00",
            is_read=False,
            is_starred=False,
            labels=["面试", "日历候选"],
            priority="high",
            recipients=[EmailAddress(name="Mengyi Xu", email="mengyi@example.com")],
            body_text=(
                "Hello Mengyi,\n\nYour interview has been moved to Tuesday, 6 October "
                "2026 at 10:30 AM Singapore time. Please reply to confirm the new time."
                "\n\nRegards,\nTalent Team"
            ),
            ai_overview=AiOverview(
                summary="面试调整至10月6日10:30，需要回复确认新的时间。",
                category="招聘与面试",
                priority="high",
                confidence=0.97,
            ),
            translation=Translation(
                source_language="English",
                target_language="简体中文",
                translated_body=(
                    "你好，Mengyi：\n\n你的面试已调整至2026年10月6日星期二上午10:30"
                    "（新加坡时间）。请回复确认新的时间。\n\nTalent Team"
                ),
            ),
            action_items=[
                ActionItem(
                    id="action-confirm-interview",
                    title="回复确认新的面试时间",
                    due_at=None,
                    evidence="Please reply to confirm the new time.",
                    completed=False,
                )
            ],
            calendar_drafts=[
                CalendarDraft(
                    id="calendar-interview",
                    title="Interview",
                    starts_at="2026-10-06T10:30:00+08:00",
                    ends_at="2026-10-06T11:30:00+08:00",
                    timezone="Asia/Singapore",
                    location="Online meeting",
                    evidence="Tuesday, 6 October 2026 at 10:30 AM Singapore time",
                )
            ],
            reply_draft=ReplyDraft(
                subject="Re: Interview schedule update",
                body=(
                    "Hello,\n\nThank you for the update. I confirm that I am available "
                    "on Tuesday, 6 October 2026 at 10:30 AM Singapore time."
                    "\n\nBest regards,\nMengyi"
                ),
                tone="正式礼貌",
                language="English",
            ),
        ),
        DemoEmail(
            id="demo-weekly-digest",
            subject="Weekly product digest",
            sender=EmailAddress(name="Product Updates", email="updates@example.com"),
            preview="本周更新包含新的审批流程、通知设置和移动端体验改进。",
            received_at="2026-09-30T18:20:00+08:00",
            is_read=True,
            is_starred=False,
            labels=["资讯"],
            priority="normal",
            recipients=[EmailAddress(name="Mengyi Xu", email="mengyi@example.com")],
            body_text=(
                "This week we shipped approval workflow improvements, notification "
                "preferences, and a more compact mobile navigation. No action is required."
            ),
            ai_overview=AiOverview(
                summary="产品周报介绍审批流程、通知设置和移动端导航改进，无需采取行动。",
                category="产品资讯",
                priority="normal",
                confidence=0.91,
            ),
            translation=Translation(
                source_language="English",
                target_language="简体中文",
                translated_body=(
                    "本周我们上线了审批流程优化、通知偏好设置，以及更紧凑的移动端导航。"
                    "无需采取行动。"
                ),
            ),
            action_items=[],
            calendar_drafts=[],
            reply_draft=ReplyDraft(
                subject="Re: Weekly product digest",
                body=(
                    "Thanks for sharing the weekly update. I have reviewed the latest "
                    "product changes.\n\nBest,\nMengyi"
                ),
                tone="简洁",
                language="English",
            ),
        ),
    ]
