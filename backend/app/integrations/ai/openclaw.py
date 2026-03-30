from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.config import Settings, get_settings
from app.core.enums import ProviderHealth


@dataclass(slots=True)
class OpenClawProbeResult:
    health: ProviderHealth
    provider_name: str
    default_model: str | None
    payload: dict[str, Any]
    error: str | None = None
    checked_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class OpenClawRuntime:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def _run(self, args: list[str], timeout_seconds: int) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env.update(self.settings.openclaw_env)
        command = self.settings.openclaw_command
        if any(separator in command for separator in ("/", "\\")) or command.endswith((".cmd", ".bat", ".exe")):
            command = str(Path(command).resolve())
        return subprocess.run(
            [command, *args],
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            env=env,
        )

    def probe(self) -> OpenClawProbeResult:
        try:
            result = self._run(["models", "status", "--json"], self.settings.openclaw_status_timeout_seconds)
        except (subprocess.TimeoutExpired, TimeoutError):
            return OpenClawProbeResult(
                health=ProviderHealth.DEGRADED,
                provider_name="openclaw",
                default_model=None,
                payload={},
                error="Timed out while probing `openclaw models status --json`.",
            )
        except FileNotFoundError:
            return OpenClawProbeResult(
                health=ProviderHealth.OFFLINE,
                provider_name="openclaw",
                default_model=None,
                payload={},
                error="`openclaw` was not found on PATH for the running process.",
            )

        if result.returncode != 0:
            return OpenClawProbeResult(
                health=ProviderHealth.OFFLINE,
                provider_name="openclaw",
                default_model=None,
                payload={"stdout": result.stdout, "stderr": result.stderr},
                error=result.stderr.strip() or "OpenClaw returned a non-zero exit code.",
            )

        payload = self._parse_json_like_output(result.stdout)
        health = ProviderHealth.HEALTHY if payload else ProviderHealth.DEGRADED
        default_model = self._extract_default_model(payload)
        return OpenClawProbeResult(
            health=health,
            provider_name="openclaw",
            default_model=default_model,
            payload=payload,
            error=None if health == ProviderHealth.HEALTHY else "OpenClaw returned unstructured status output.",
        )

    def invoke_agent(
        self,
        *,
        agent: str,
        message: str,
        session_id: str,
        thinking: str = "medium",
        deliver: bool = False,
    ) -> dict[str, Any]:
        args = [
            "agent",
            "--agent",
            agent,
            "--session-id",
            session_id,
            "--message",
            message,
            "--thinking",
            thinking,
            "--json",
        ]
        if deliver:
            args.append("--deliver")

        result = self._run(args, self.settings.openclaw_agent_timeout_seconds)
        payload = self._parse_json_like_output(result.stdout)
        payload["_stderr"] = result.stderr
        payload["_returncode"] = result.returncode
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or f"OpenClaw agent run failed for {agent}")
        return payload

    @staticmethod
    def _extract_default_model(payload: dict[str, Any]) -> str | None:
        if not isinstance(payload, dict):
            return None
        for key in ("defaultModel", "default_model", "primary", "selectedModel"):
            value = payload.get(key)
            if isinstance(value, str):
                return value
        models = payload.get("models")
        if isinstance(models, list) and models:
            first = models[0]
            if isinstance(first, dict):
                for key in ("name", "id", "model"):
                    value = first.get(key)
                    if isinstance(value, str):
                        return value
        return None

    @staticmethod
    def _parse_json_like_output(raw: str) -> dict[str, Any]:
        text = raw.strip()
        if not text:
            return {}
        try:
            parsed = json.loads(text)
            return parsed if isinstance(parsed, dict) else {"items": parsed}
        except json.JSONDecodeError:
            lines = [line for line in text.splitlines() if line.strip()]
            for line in reversed(lines):
                try:
                    parsed = json.loads(line)
                    return parsed if isinstance(parsed, dict) else {"items": parsed}
                except json.JSONDecodeError:
                    continue
        return {"raw": text}
