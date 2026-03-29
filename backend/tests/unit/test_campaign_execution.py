from datetime import datetime, timezone
from types import SimpleNamespace

from app.core.enums import CampaignChannel
from app.services.campaign_execution import _max_steps, _next_delay


def test_campaign_step_counts() -> None:
    assert _max_steps(CampaignChannel.EMAIL) == 3
    assert _max_steps(CampaignChannel.WHATSAPP) == 2


def test_next_delay_schedule() -> None:
    assert _next_delay(CampaignChannel.EMAIL, 0).days == 3
    assert _next_delay(CampaignChannel.EMAIL, 1).days == 4
    assert _next_delay(CampaignChannel.WHATSAPP, 0).days == 3
    assert _next_delay(CampaignChannel.WHATSAPP, 1) is None

