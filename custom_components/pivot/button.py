"""Button event listener, bank toggle, and button entity lookup for Pivot."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.event import async_track_state_change_event

from .announcements import do_tts
from .const import CONF_DEVICE_ID, CONF_DEVICE_SUFFIX, CONF_ESPHOME_DEVICE_NAME

_LOGGER = logging.getLogger(__name__)


async def do_bank_toggle(hass: HomeAssistant, suffix: str, bank_entity: str) -> None:
    """Toggle the entity assigned to the active bank."""
    if not bank_entity or bank_entity in ("unknown", "unavailable", "timer"):
        return
    domain = bank_entity.split(".")[0] if "." in bank_entity else ""
    try:
        if domain == "scene":
            await hass.services.async_call("scene", "turn_on", {"entity_id": bank_entity})
        elif domain == "script":
            await hass.services.async_call("script", "turn_on", {"entity_id": bank_entity})
        elif domain == "media_player":
            await hass.services.async_call("media_player", "media_play_pause", {"entity_id": bank_entity})
        elif domain == "cover":
            await hass.services.async_call("cover", "toggle", {"entity_id": bank_entity})
        else:
            await hass.services.async_call("homeassistant", "toggle", {"entity_id": bank_entity})
    except Exception:
        _LOGGER.exception("Pivot: error toggling %s for %s", bank_entity, suffix)


def get_button_event_entity(hass: HomeAssistant, device_id: str) -> str | None:
    """Find the button press event entity for a VPE device.

    Matches the event entity with device_class 'button' on the ESPHome device.
    Falls back to any event-domain entity on the device if device_class is absent.
    """
    ent_reg = er.async_get(hass)
    fallback = None
    for entity in er.async_entries_for_device(ent_reg, device_id):
        if entity.domain != "event":
            continue
        if (entity.original_device_class or entity.device_class) == "button":
            return entity.entity_id
        fallback = entity.entity_id
    return fallback


def setup_button_event_listener(
    hass: HomeAssistant, entry: ConfigEntry,
    tts_entity: str = "",
    media_player: str = "",
    announce_enabled: bool = False,
) -> object | None:
    """Listen for VPE button press events and fire pivot_button_press on the HA bus."""
    suffix = entry.data[CONF_DEVICE_SUFFIX]
    device_id = entry.data.get(CONF_DEVICE_ID)

    # Older config entries may not have device_id stored — look it up by ESPHome device name.
    if not device_id:
        esphome_name = entry.data.get(CONF_ESPHOME_DEVICE_NAME)
        if esphome_name:
            dev_reg = dr.async_get(hass)
            for device in dev_reg.devices.values():
                for eid in device.config_entries:
                    cfg = hass.config_entries.async_get_entry(eid)
                    if cfg and cfg.domain == "esphome":
                        host = (cfg.data.get("name") or cfg.data.get("host") or "").removesuffix(".local").strip()
                        if host == esphome_name:
                            device_id = device.id
                            break
                if device_id:
                    break
        if not device_id:
            _LOGGER.warning(
                "Pivot: no device_id for %s — button toggle will not work. "
                "Re-add the integration entry to fix this.",
                suffix,
            )
            return None

    button_entity_id = get_button_event_entity(hass, device_id)
    if not button_entity_id:
        _LOGGER.warning(
            "Pivot: no button press event entity found for %s (device_id=%s) — "
            "button toggle will not work. Ensure the device is running Pivot firmware v0.0.15+.",
            suffix, device_id,
        )
        return None

    _LOGGER.debug("Pivot: watching %s for button presses on %s", button_entity_id, suffix)

    @callback
    def _on_button_press(event) -> None:
        new_state = event.data.get("new_state")
        if new_state is None:
            return

        # Skip reconnect transitions — entity restores last state when the
        # ESPHome device comes back online, which would look like a real press.
        old_state = event.data.get("old_state")
        if old_state is None or old_state.state in ("unavailable", "unknown"):
            _LOGGER.debug(
                "Pivot: skipping %s button event for %s — reconnect transition "
                "(old_state=%s)",
                button_entity_id, suffix,
                old_state.state if old_state else None,
            )
            return

        press_type = new_state.attributes.get("event_type")
        if not press_type:
            _LOGGER.debug("Pivot: %s fired with no event_type — ignoring", button_entity_id)
            return

        # Resolve active bank and assigned entity
        active_bank_state = hass.states.get(f"number.{suffix}_active_bank")
        try:
            bank_idx = int(float(active_bank_state.state)) - 1 if active_bank_state else 0
        except ValueError:
            bank_idx = 0

        text_state = hass.states.get(f"text.{suffix}_bank_{bank_idx}_entity")
        bank_entity = (
            text_state.state
            if text_state and text_state.state not in ("", "unknown", "unavailable")
            else ""
        )

        control_mode_state = hass.states.get(f"switch.{suffix}_control_mode")
        control_mode = control_mode_state.state == "on" if control_mode_state else False

        _LOGGER.debug(
            "Pivot: %s press_type=%s control_mode=%s bank=%s bank_entity=%s",
            suffix, press_type, control_mode, bank_idx + 1, bank_entity or "(none)",
        )

        # Perform toggle natively — no blueprint required.
        if press_type == "single_press" and control_mode and bank_entity:
            hass.async_create_task(do_bank_toggle(hass, suffix, bank_entity))

        hass.bus.async_fire(
            "pivot_button_press",
            {
                "suffix": suffix,
                "bank": bank_idx + 1,  # 1-based
                "bank_entity": bank_entity,
                "press_type": press_type,
                "control_mode": control_mode,
            },
        )

        # Native triple press re-announcement (system announcement, not value announcement)
        if (press_type == "triple_press"
                and announce_enabled and tts_entity and media_player
                and bank_entity and "." in bank_entity):
            _ann = hass.states.get(f"switch.{suffix}_announcements")
            _mute = hass.states.get(f"switch.{suffix}_mute_announcements")
            if (_ann and _ann.state == "on"
                    and not (_mute and _mute.state == "on")):
                _es = hass.states.get(bank_entity)
                _name = (_es.attributes.get("friendly_name") if _es else None) or bank_entity
                hass.async_create_task(do_tts(hass, tts_entity, media_player, _name))

    return async_track_state_change_event(hass, [button_entity_id], _on_button_press)
