from app.core.enums import ProviderHealth
from app.integrations.ai.openclaw import OpenClawRuntime


def test_parse_json_like_output_dict() -> None:
    payload = OpenClawRuntime._parse_json_like_output('{"defaultModel":"openai-codex/gpt-5.4"}')
    assert payload["defaultModel"] == "openai-codex/gpt-5.4"


def test_probe_timeout_maps_to_degraded(monkeypatch) -> None:
    runtime = OpenClawRuntime()

    def fake_run(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise TimeoutError

    monkeypatch.setattr(runtime, "_run", fake_run)
    result = runtime.probe()
    assert result.health in {ProviderHealth.DEGRADED, ProviderHealth.OFFLINE}

