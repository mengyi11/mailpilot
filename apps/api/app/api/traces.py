from __future__ import annotations
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.core.errors import AppError
from app.db.models.agent import AgentRun, AgentStep, Approval, ToolCall
from app.db.session import get_db
from app.api.memory import current_user_id
from app.schemas.trace import AgentTraceResponse, TraceApprovalResponse, TraceOverviewResponse, TraceStepResponse, TraceToolResponse
from app.services.trace import redact

router = APIRouter(prefix="/traces", tags=["agent-trace"])

def _trace(run: AgentRun, db: Session) -> AgentTraceResponse:
    steps = db.scalars(select(AgentStep).where(AgentStep.agent_run_id == run.id).order_by(AgentStep.sequence)).all()
    tools = db.scalars(select(ToolCall).where(ToolCall.agent_run_id == run.id).order_by(ToolCall.created_at)).all()
    approvals = db.scalars(select(Approval).where(Approval.agent_run_id == run.id).order_by(Approval.requested_at)).all()
    return AgentTraceResponse.model_validate({
        "id": run.id, "trace_id": run.trace_id, "email_id": run.email_id, "user_goal": run.user_goal,
        "workflow_name": run.workflow_name, "workflow_version": run.workflow_version, "prompt_version": run.prompt_version,
        "model_name": run.model_name, "status": run.status, "input_tokens": run.input_tokens, "output_tokens": run.output_tokens,
        "cost_usd": run.cost_usd, "duration_ms": run.duration_ms, "retry_count": run.retry_count, "token_budget": run.token_budget,
        "input_data": redact(run.input_data), "output_data": redact(run.output_data), "error_code": run.error_code,
        "error_message": run.error_message, "created_at": run.created_at, "started_at": run.started_at, "completed_at": run.completed_at,
        "steps": [redact(TraceStepResponse.model_validate(s).model_dump()) for s in steps],
        "tools": [redact(TraceToolResponse.model_validate(t).model_dump()) for t in tools],
        "approvals": [redact(TraceApprovalResponse.model_validate(a).model_dump()) for a in approvals],
    })

@router.get("/overview", response_model=TraceOverviewResponse)
def overview(db: Session = Depends(get_db)) -> TraceOverviewResponse:
    uid = current_user_id(db)
    rows = db.scalars(select(AgentRun).where(AgentRun.user_id == uid).order_by(AgentRun.created_at.desc()).limit(100)).all()
    return TraceOverviewResponse(runs=len(rows), total_tokens=sum((r.input_tokens or 0)+(r.output_tokens or 0) for r in rows), total_cost_usd=sum((r.cost_usd or 0) for r in rows), avg_latency_ms=round(sum(r.duration_ms or 0 for r in rows)/len(rows), 1) if rows else 0, failed_runs=sum(r.status == "failed" for r in rows))

@router.get("", response_model=list[AgentTraceResponse])
def list_traces(db: Session = Depends(get_db)) -> list[AgentTraceResponse]:
    uid = current_user_id(db)
    return [_trace(r, db) for r in db.scalars(select(AgentRun).where(AgentRun.user_id == uid).order_by(AgentRun.created_at.desc()).limit(30)).all()]

@router.get("/{run_id}", response_model=AgentTraceResponse)
def get_trace(run_id: UUID, db: Session = Depends(get_db)) -> AgentTraceResponse:
    run = db.scalar(select(AgentRun).where(AgentRun.id == run_id, AgentRun.user_id == current_user_id(db)))
    if run is None: raise AppError(code="TRACE_NOT_FOUND", message="Agent trace was not found.", status_code=404)
    return _trace(run, db)
