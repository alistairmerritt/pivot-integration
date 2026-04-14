"""Blueprint installation and sync helpers for Pivot."""
from __future__ import annotations

import logging
import os
import shutil

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_DEVICE_SUFFIX, CONF_FRIENDLY_NAME

_LOGGER = logging.getLogger(__name__)


def sync_blueprints(hass: HomeAssistant) -> list[str]:
    """Copy blueprints from custom_components/pivot/blueprints/ → config/blueprints/automation(script)/pivot/.

    Only writes files whose content has changed, and uses an atomic temp-file
    swap so a crash mid-write never leaves a corrupt blueprint.

    Returns a list of relative paths that were actually written.
    """
    integration_dir = os.path.dirname(__file__)
    updated: list[str] = []

    for domain in ("automation", "script"):
        src_dir = os.path.join(integration_dir, "blueprints", domain)
        dst_dir = hass.config.path("blueprints", domain, "pivot")

        if not os.path.isdir(src_dir):
            continue

        os.makedirs(dst_dir, exist_ok=True)

        for fname in os.listdir(src_dir):
            if not fname.endswith(".yaml"):
                continue

            src_file = os.path.join(src_dir, fname)
            dst_file = os.path.join(dst_dir, fname)

            with open(src_file, "rb") as f:
                src_bytes = f.read()

            # Skip if destination is already identical
            if os.path.exists(dst_file):
                with open(dst_file, "rb") as f:
                    if f.read() == src_bytes:
                        continue

            # Atomic write via temp file
            tmp_file = dst_file + ".pivot_tmp"
            with open(tmp_file, "wb") as f:
                f.write(src_bytes)
            shutil.move(tmp_file, dst_file)

            rel = f"{domain}/pivot/{fname}"
            _LOGGER.info("Pivot: installed/updated blueprint %s", rel)
            updated.append(rel)

    return updated


async def install_blueprints(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Sync bundled blueprints and show a first-run persistent notification."""
    copied = await hass.async_add_executor_job(sync_blueprints, hass)
    suffix = entry.data[CONF_DEVICE_SUFFIX]
    friendly_name = entry.data[CONF_FRIENDLY_NAME]

    if copied:
        _LOGGER.info("Pivot: installed blueprints for %s: %s", suffix, copied)
        try:
            await hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "title": f"Pivot — {friendly_name} Blueprints Installed",
                    "message": (
                        f"Pivot blueprints have been installed for **{friendly_name}**.\n\n"
                        f"Button toggle works automatically — no script needed.\n\n"
                        f"**Optional automations:**\n"
                        f"Go to [Automations](/config/automation/dashboard) → Create → Search blueprints → **Pivot — Announce** "
                        f"to enable spoken announcements (requires a TTS provider).\n\n"
                        f"If you use the timer feature, also create an automation from **Pivot — Timer**."
                    ),
                    "notification_id": f"pivot_blueprints_{suffix}",
                },
                blocking=False,
            )
        except Exception as err:
            _LOGGER.warning(
                "Pivot: could not create blueprint install notification for %s: %s",
                suffix, err,
            )
