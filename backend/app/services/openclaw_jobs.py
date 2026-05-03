from __future__ import annotations

import json
import time
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.core.enums import AIRunJobType, AIRunStatus
from app.integrations.ai.openclaw import OpenClawRuntime
from app.models.domain import AIRun, Business


JOB_TO_AGENT_SETTING = {
    AIRunJobType.LEAD_ENRICHMENT: "openclaw_agent_enrichment",
    AIRunJobType.CONTACT_DISCOVERY: "openclaw_agent_contact_discovery",
    AIRunJobType.SITE_AUDIT: "openclaw_agent_site_audit",
    AIRunJobType.DRAFT_EMAIL: "openclaw_agent_draft_email",
    AIRunJobType.DRAFT_WHATSAPP: "openclaw_agent_draft_whatsapp",
    AIRunJobType.REPLY_CLASSIFIER: "openclaw_agent_reply_classifier",
}


def _logical_agent_name(runtime: OpenClawRuntime, job_type: AIRunJobType) -> str:
    return getattr(runtime.settings, JOB_TO_AGENT_SETTING[job_type])


def _codex_window_threshold(runtime: OpenClawRuntime) -> int:
    threshold = int(runtime.settings.codex_budget_max_runs_per_window * runtime.settings.codex_switch_threshold_percent / 100)
    return max(1, threshold)


def _recent_codex_run_count(db: Session, runtime: OpenClawRuntime) -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=runtime.settings.codex_budget_window_hours)
    runs = db.query(AIRun).filter(AIRun.created_at >= cutoff).all()
    return sum(1 for run in runs if (run.model_alias or "").startswith("codex"))


def _should_use_copilot(db: Session, runtime: OpenClawRuntime) -> bool:
    return _recent_codex_run_count(db, runtime) >= _codex_window_threshold(runtime)


def _quota_like_error(exc: Exception) -> bool:
    text = str(exc).lower()
    markers = ("rate limit", "quota", "limit reached", "429", "included limits", "too many requests")
    return any(marker in text for marker in markers)


def _provider_agent(logical_agent: str, provider: str) -> str:
    return f"{logical_agent}-{provider}"


def _session_id(job_type: AIRunJobType, run_id: str, suffix: str | None = None) -> str:
    base = f"{job_type.value}-{run_id}"
    return f"{base}-{suffix}" if suffix else base


def run_openclaw_job(
    db: Session,
    *,
    business: Business | None,
    job_type: AIRunJobType,
    model_alias: str,
    message_payload: dict[str, Any],
    runtime: OpenClawRuntime | None = None,
) -> AIRun:
    runtime = runtime or OpenClawRuntime()
    logical_agent = _logical_agent_name(runtime, job_type)
    prefer_copilot = _should_use_copilot(db, runtime)
    selected_provider = "copilot" if prefer_copilot else "codex"
    selected_alias = "copilot_best" if prefer_copilot else "codex_best"
    run = AIRun(
        business_id=business.id if business else None,
        provider_name="openclaw",
        model_alias=selected_alias,
        job_type=job_type,
        status=AIRunStatus.PENDING,
    )
    db.add(run)
    db.flush()

    started = time.perf_counter()
    try:
        response = runtime.invoke_agent(
            agent=_provider_agent(logical_agent, selected_provider),
            session_id=_session_id(job_type, str(run.id)),
            message=json.dumps(message_payload, ensure_ascii=False),
        )
        run.status = AIRunStatus.SUCCEEDED
        run.output_json = response
    except Exception as exc:  # pragma: no cover - exercised in integration tests with monkeypatching
        if selected_provider == "codex" and _quota_like_error(exc):
            try:
                response = runtime.invoke_agent(
                    agent=_provider_agent(logical_agent, "copilot"),
                    session_id=_session_id(job_type, str(run.id), "copilot"),
                    message=json.dumps(message_payload, ensure_ascii=False),
                )
                run.model_alias = "copilot_best"
                run.status = AIRunStatus.SUCCEEDED
                run.output_json = response
            except Exception as retry_exc:  # pragma: no cover
                run.status = AIRunStatus.FAILED
                run.error_text = f"{exc} | fallback_failed: {retry_exc}"
        else:
            run.status = AIRunStatus.FAILED
            run.error_text = str(exc)
    finally:
        run.duration_ms = int((time.perf_counter() - started) * 1000)
        db.flush()
    return run

