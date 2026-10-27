"""Serve the Pivot dashboard cards (pivot-cards.js) from the integration.

The cards ship inside the integration so a HACS install or update is all a
user needs: no separate frontend repository, no Lovelace resource to add.
"""
from __future__ import annotations

import hashlib
import logging
from pathlib import Path

from homeassistant.components.frontend import DATA_EXTRA_MODULE_URL, add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant
from homeassistant.loader import async_get_integration

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

CARDS_URL = "/pivot_static/pivot-cards.js"
CARDS_FILE = Path(__file__).parent / "frontend" / "pivot-cards.js"
_REGISTERED_KEY = f"{DOMAIN}_frontend_registered"


def _file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:10]


async def async_register_frontend(hass: HomeAssistant) -> None:
    """Serve pivot-cards.js and load it on every frontend page, once per run.

    The URL carries the integration version and a content hash, so a new
    release (or a rebuilt file) is never served from a browser or companion
    app cache.
    """
    if hass.data.get(_REGISTERED_KEY):
        return
    if hass.http is None or DATA_EXTRA_MODULE_URL not in hass.data:
        # frontend/http are after_dependencies: absent only in stripped-down
        # setups (and unit tests). The integration works without the cards.
        _LOGGER.debug("Pivot: frontend not loaded; dashboard cards not registered")
        return
    if not CARDS_FILE.is_file():
        _LOGGER.warning("Pivot: %s is missing; dashboard cards are unavailable", CARDS_FILE)
        return

    integration = await async_get_integration(hass, DOMAIN)
    digest = await hass.async_add_executor_job(_file_digest, CARDS_FILE)
    await hass.http.async_register_static_paths(
        [StaticPathConfig(CARDS_URL, str(CARDS_FILE), True)]
    )
    add_extra_js_url(hass, f"{CARDS_URL}?v={integration.version}-{digest}")
    hass.data[_REGISTERED_KEY] = True
    _LOGGER.debug("Pivot: dashboard cards served from %s", CARDS_URL)
