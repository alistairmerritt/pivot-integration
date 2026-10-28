"""Blueprint notification helper for Pivot.

Blueprints are no longer bundled with the integration — they are hosted
publicly and imported directly via URL. This module fires a one-time
persistent notification on first setup to point users to the import links.
"""
from __future__ import annotations

import logging
from urllib.parse import quote

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_DEVICE_SUFFIX, CONF_FRIENDLY_NAME

_LOGGER = logging.getLogger(__name__)

# The `stable` branch, not `main`: it only moves when a release is published
# (.github/workflows/stable.yml), so an import never picks up unreleased work.
_BLUEPRINT_BASE = (
    "https://raw.githubusercontent.com/alistairmerritt/pivot-integration"
    "/stable/blueprints/automation"
)


def _import_link(file_name: str) -> str:
    """My Home Assistant link that opens the blueprint import dialog."""
    url = f"{_BLUEPRINT_BASE}/{file_name}"
    return (
        "https://my.home-assistant.io/redirect/blueprint_import/"
        f"?blueprint_url={quote(url, safe='')}"
    )


TIMER_CONTROL_URL = _import_link("pivot_timer.yaml")
TIMER_VOICE_URL = _import_link("pivot_timer_voice.yaml")


async def install_blueprints(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Show a one-time setup notification pointing to the blueprint import URLs."""
    # Only show once — skip if this entry has already been notified.
    if entry.data.get("setup_notified"):
        return

    suffix = entry.data[CONF_DEVICE_SUFFIX]
    friendly_name = entry.data[CONF_FRIENDLY_NAME]

    try:
        await hass.services.async_call(
            "persistent_notification",
            "create",
            {
                "title": f"Pivot — {friendly_name} Ready",
                "message": (
                    f"**{friendly_name}** is set up.\n\n"
                    f"To use the timer, import the blueprints via the links below "
                    f"(one-time per Home Assistant instance — not per device):\n\n"
                    f"- [Pivot - Timer Control]({TIMER_CONTROL_URL})\n"
                    f"- [Pivot - Timer - Voice]({TIMER_VOICE_URL})\n\n"
                    f"When a Pivot update changes a blueprint, the release notes "
                    f"say so: use **Re-import blueprint** on it to pick up the "
                    f"new version."
                ),
                "notification_id": f"pivot_setup_{suffix}",
            },
            blocking=False,
        )
        hass.config_entries.async_update_entry(
            entry, data={**entry.data, "setup_notified": True}
        )
    except Exception as err:
        _LOGGER.warning(
            "Pivot: could not create setup notification for %s: %s",
            suffix, err,
        )
