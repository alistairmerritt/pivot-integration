"""Config flow for Pivot."""
from __future__ import annotations

import ipaddress
import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import selector

from .button import get_button_event_entity
from .const import (
    CONF_ANNOUNCEMENTS,
    CONF_DEVICE_ID,
    CONF_DEVICE_SUFFIX,
    CONF_ESPHOME_DEVICE_NAME,
    CONF_FRIENDLY_NAME,
    CONF_MANAGEMENT_MODE,
    CONF_MEDIA_PLAYER_ENTITY,
    CONF_TTS_ENTITY,
    DOMAIN,
    MANAGEMENT_BLUEPRINTS,
    NUM_BANKS,
    make_suffix,
    option_or_data,
)
from .const import (
    entity_id as make_entity_id,
)

_LOGGER = logging.getLogger(__name__)


def _get_esphome_devices(hass: HomeAssistant) -> dict[str, str]:
    dev_reg = dr.async_get(hass)
    pivot_candidates: dict[str, str] = {}

    for device in dev_reg.devices.values():
        esphome_entries = [
            eid for eid in device.config_entries
            if (entry := hass.config_entries.async_get_entry(eid)) is not None
            and entry.domain == "esphome"
        ]
        if not esphome_entries:
            continue

        label = device.name_by_user or device.name or device.id
        pivot_candidates[device.id] = label

    return pivot_candidates


def _is_ip_address(value: str) -> bool:
    """True if value is a bare IPv4/IPv6 address rather than a hostname."""
    if not value:
        return False
    try:
        ipaddress.ip_address(value)
    except ValueError:
        return False
    return True


def _get_esphome_device_name(hass: HomeAssistant, device: dr.DeviceEntry) -> str | None:
    """Return the ESPHome device name (e.g. 'home-assistant-voice-0aaae0').

    Current ESPHome stores the canonical name in entry.data["device_name"].
    Older versions used "name". Both are preferred over entry.data["host"],
    which is either "home-assistant-voice-0aaae0.local", the bare name, or an
    IP address. The .local suffix is stripped; an IP address is rejected.
    """
    for eid in device.config_entries:
        entry = hass.config_entries.async_get_entry(eid)
        if entry and entry.domain == "esphome":
            # Never log entry.data wholesale — ESPHome stores "password" and
            # "noise_psk" in there. Only allowlisted, non-secret fields.
            _LOGGER.debug(
                "ESPHome entry for device %s: title=%r device_name=%r host=%r",
                device.id,
                entry.title,
                entry.data.get("device_name"),
                entry.data.get("host"),
            )
            # "device_name" is the canonical hostname in current ESPHome.
            # "name" is the legacy key; "host" is a last resort because the
            # user may have configured ESPHome by IP address.
            name = (
                entry.data.get("device_name")
                or entry.data.get("name")
                or entry.data.get("host")
                or ""
            )
            name = name.removesuffix(".local").strip()
            if _is_ip_address(name):
                # make_suffix() would strip the dots and produce a bogus
                # suffix like "192168142", silently breaking every entity ID
                # and the esphome.<slug>_pivot_sync_settings action.
                _LOGGER.warning(
                    "ESPHome entry for %s is configured by IP address (%s) and "
                    "reports no device name — cannot determine entity ID suffix",
                    device.id, name,
                )
                return None
            if name:
                return name
            # The title is the user-visible friendly name, not the device's
            # network hostname, so using it as a suffix will produce wrong
            # entity IDs. Treat this as a hard failure rather than silently
            # producing a misconfigured entry.
            _LOGGER.warning(
                "Could not find ESPHome device name in entry data for %s "
                "(title=%r) — cannot determine correct entity ID suffix",
                device.id, entry.title,
            )
            return None
    return None


def _already_configured(hass: HomeAssistant, device_id: str) -> bool:
    return any(
        entry.data.get(CONF_DEVICE_ID) == device_id
        for entry in hass.config_entries.async_entries(DOMAIN)
    )


def _suffix_in_use(hass: HomeAssistant, suffix: str) -> bool:
    return any(
        entry.data.get(CONF_DEVICE_SUFFIX) == suffix
        for entry in hass.config_entries.async_entries(DOMAIN)
    )


def _bank_entity_schema(current: dict[str, str] | None = None) -> vol.Schema:
    """Build a schema with a timer-bank single-select and one EntitySelector per bank.

    A 'timer_banks' single-select lets users mark one bank as a timer bank without
    typing the reserved value 'timer' into an entity field. The step handler writes
    'timer' to that bank and ignores its entity picker value.
    Entity pickers are shown for all banks but left blank for the timer bank.
    """
    current = current or {}
    fields = {}

    timer_default = next(
        (str(i + 1) for i in range(NUM_BANKS) if current.get(f"bank_{i}_entity") == "timer"),
        "none",
    )
    fields[vol.Optional("timer_banks", default=timer_default)] = selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[
                selector.SelectOptionDict(value="none", label="No timer bank"),
                selector.SelectOptionDict(value="1", label="Bank 1"),
                selector.SelectOptionDict(value="2", label="Bank 2"),
                selector.SelectOptionDict(value="3", label="Bank 3"),
                selector.SelectOptionDict(value="4", label="Bank 4"),
            ],
            multiple=False,
            mode=selector.SelectSelectorMode.LIST,
        )
    )

    entity_sel = selector.EntitySelector(
        selector.EntitySelectorConfig(
            domain=["light", "switch", "input_boolean", "fan", "climate", "media_player", "cover", "scene", "script", "input_number", "number"],
            multiple=False,
        )
    )
    for i in range(NUM_BANKS):
        key = f"bank_{i}_entity"
        existing = current.get(key) or None
        # Don't pre-fill 'timer' — that bank is represented by the timer_banks selector
        if existing and existing != "timer":
            fields[vol.Optional(key, default=existing)] = entity_sel
        else:
            fields[vol.Optional(key)] = entity_sel
    return vol.Schema(fields)


def _apply_timer_banks(user_input: dict) -> dict[str, str]:
    """Return a dict of bank_N_entity values with the timer bank resolved.

    The selected bank in 'timer_banks' is set to 'timer'; all others use the
    entity picker value (or empty string). 'none' means no timer bank.
    """
    timer_bank = user_input.get("timer_banks", "none")
    result = {}
    for i in range(NUM_BANKS):
        key = f"bank_{i}_entity"
        if str(i + 1) == timer_bank:
            result[key] = "timer"
        else:
            result[key] = user_input.get(key) or ""
    return result


def _move_pivot_device(
    hass: HomeAssistant, entry: config_entries.ConfigEntry, new_device_id: str
) -> None:
    """Carry the entry's own Pivot device across to the new device link.

    Pivot's device is identified by the linked ESPHome device's ID, so without
    this the reload would build a SECOND Pivot device and move every entity to
    it — losing the device's area, any name given to it, and any automation
    that targets the device. Re-identifying the existing device keeps all of
    that. Entity IDs and unique IDs are unaffected either way.
    """
    old_device_id = entry.data.get(CONF_DEVICE_ID)
    if not old_device_id or old_device_id == new_device_id:
        return
    dev_reg = dr.async_get(hass)
    pivot_device = dev_reg.async_get_device(identifiers={(DOMAIN, old_device_id)})
    if pivot_device is None or entry.entry_id not in pivot_device.config_entries:
        return
    if dev_reg.async_get_device(identifiers={(DOMAIN, new_device_id)}) is not None:
        # A Pivot device for the target already exists (a previous entry for
        # that device left one behind). Leave both alone rather than risk a
        # registry collision; the reload attaches the entities to it.
        _LOGGER.debug(
            "Pivot: a device already exists for %s — not re-identifying %s",
            new_device_id, pivot_device.id,
        )
        return
    dev_reg.async_update_device(
        pivot_device.id, new_identifiers={(DOMAIN, new_device_id)}
    )


class PivotConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Pivot: four steps to add a device, plus reconfigure."""

    VERSION = 1

    def __init__(self) -> None:
        self._selected_device_id: str | None = None
        self._esphome_device_name: str | None = None
        self._device_suffix: str | None = None
        self._friendly_name: str | None = None
        self._pending_entry_data: dict = {}

    # ------------------------------------------------------------------
    # Step 1: Pick an ESPHome device
    # ------------------------------------------------------------------
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}
        esphome_devices = _get_esphome_devices(self.hass)

        if not esphome_devices:
            return self.async_abort(reason="no_esphome_devices")

        if user_input is not None:
            device_id = user_input[CONF_DEVICE_ID]

            if _already_configured(self.hass, device_id):
                return self.async_abort(reason="already_configured")

            dev_reg = dr.async_get(self.hass)
            device = dev_reg.async_get(device_id)

            if device is None:
                errors[CONF_DEVICE_ID] = "device_not_found"
            else:
                esphome_name = _get_esphome_device_name(self.hass, device)
                if not esphome_name:
                    errors[CONF_DEVICE_ID] = "cannot_read_device_name"
                else:
                    suffix = make_suffix(esphome_name)
                    if _suffix_in_use(self.hass, suffix):
                        errors[CONF_DEVICE_ID] = "suffix_collision"
                    else:
                        self._selected_device_id = device_id
                        self._esphome_device_name = esphome_name
                        self._device_suffix = suffix
                        self._friendly_name = (
                            device.name_by_user or device.name or esphome_name
                        )
                        return await self.async_step_confirm()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_DEVICE_ID): vol.In(esphome_devices),
            }),
            errors=errors,
        )

    # ------------------------------------------------------------------
    # Step 2: Firmware confirmation + device suffix review
    # ------------------------------------------------------------------
    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            if not user_input.get("firmware_confirmed"):
                errors["firmware_confirmed"] = "must_confirm_firmware"
            else:
                raw = user_input.get(CONF_DEVICE_SUFFIX, "").strip()
                suffix = make_suffix(raw)
                if not suffix:
                    errors[CONF_DEVICE_SUFFIX] = "suffix_required"
                elif _suffix_in_use(self.hass, suffix):
                    errors[CONF_DEVICE_SUFFIX] = "suffix_collision"
                else:
                    self._device_suffix = suffix
                    return await self.async_step_options()

        return self.async_show_form(
            step_id="confirm",
            data_schema=vol.Schema({
                vol.Required("firmware_confirmed", default=False): bool,
                # Pre-fill with the auto-derived suffix so the user can review
                # it without having to retype from scratch.
                vol.Required(CONF_DEVICE_SUFFIX, default=self._device_suffix or ""): str,
            }),
            errors=errors,
            description_placeholders={
                "device_name": self._friendly_name,
            },
        )

    # ------------------------------------------------------------------
    # Step 3: Setup options (announcements + management mode)
    # ------------------------------------------------------------------
    async def async_step_options(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            self._pending_entry_data = {
                CONF_DEVICE_ID: self._selected_device_id,
                CONF_ESPHOME_DEVICE_NAME: self._esphome_device_name,
                CONF_DEVICE_SUFFIX: self._device_suffix,
                CONF_FRIENDLY_NAME: self._friendly_name,
                CONF_ANNOUNCEMENTS: user_input.get(CONF_ANNOUNCEMENTS, True),
                CONF_TTS_ENTITY: user_input.get(CONF_TTS_ENTITY) or "",
                CONF_MEDIA_PLAYER_ENTITY: user_input.get(CONF_MEDIA_PLAYER_ENTITY) or "",
                CONF_MANAGEMENT_MODE: MANAGEMENT_BLUEPRINTS,
            }
            return await self.async_step_banks_initial()

        tts_sel = selector.EntitySelector(
            selector.EntitySelectorConfig(domain="tts", multiple=False)
        )
        mp_sel = selector.EntitySelector(
            selector.EntitySelectorConfig(domain="media_player", multiple=False)
        )

        return self.async_show_form(
            step_id="options",
            data_schema=vol.Schema({
                vol.Optional(CONF_TTS_ENTITY): tts_sel,
                vol.Optional(CONF_MEDIA_PLAYER_ENTITY): mp_sel,
                vol.Optional(CONF_ANNOUNCEMENTS, default=True): selector.BooleanSelector(),
            }),
            description_placeholders={
                "device_name": self._friendly_name,
            },
        )

    async def async_step_banks_initial(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step 4 (initial setup only): Assign entities to banks."""
        if user_input is not None:
            for key, value in _apply_timer_banks(user_input).items():
                self._pending_entry_data[key] = value
            return self.async_create_entry(
                title=self._friendly_name,
                data=self._pending_entry_data,
            )

        return self.async_show_form(
            step_id="banks_initial",
            data_schema=_bank_entity_schema({}),
        )

    # ------------------------------------------------------------------
    # Reconfigure: re-link the entry to an ESPHome device
    # ------------------------------------------------------------------
    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Point this entry at a different ESPHome device, keeping everything else.

        Needed when the VPE is added to Home Assistant again — re-adopted in
        ESPHome, reset, or first added by IP address: it becomes a new device,
        and the entry kept watching the old one, so button presses did nothing.
        Only the device link changes. The suffix must keep matching the
        firmware, and bank assignments and settings live in Pivot's own
        entities, which survive the reload.
        """
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        esphome_devices = _get_esphome_devices(self.hass)
        if not esphome_devices:
            return self.async_abort(reason="no_esphome_devices")

        if user_input is not None:
            device_id = user_input[CONF_DEVICE_ID]
            device = dr.async_get(self.hass).async_get(device_id)
            in_use = any(
                other.entry_id != entry.entry_id
                and other.data.get(CONF_DEVICE_ID) == device_id
                for other in self.hass.config_entries.async_entries(DOMAIN)
            )
            if in_use:
                errors[CONF_DEVICE_ID] = "device_in_use"
            elif device is None:
                errors[CONF_DEVICE_ID] = "device_not_found"
            else:
                esphome_name = _get_esphome_device_name(self.hass, device)
                if not esphome_name:
                    errors[CONF_DEVICE_ID] = "cannot_read_device_name"
                else:
                    _move_pivot_device(self.hass, entry, device_id)
                    return self.async_update_reload_and_abort(
                        entry,
                        data_updates={
                            CONF_DEVICE_ID: device_id,
                            CONF_ESPHOME_DEVICE_NAME: esphome_name,
                        },
                    )

        # Several copies of one VPE can exist after a re-add, often with
        # similar names. Flag the ones whose button cannot be heard, so the
        # live copy is easy to pick. The list holds every ESPHome device, so
        # one with no button at all (a plug, a sensor) is labelled as such.
        labels: dict[str, str] = {}
        for candidate_id, label in esphome_devices.items():
            button_entity_id = get_button_event_entity(self.hass, candidate_id)
            if button_entity_id is None:
                label = f"{label} (no button)"
            else:
                button_state = self.hass.states.get(button_entity_id)
                if button_state is None or button_state.state == "unavailable":
                    label = f"{label} (unavailable)"
            labels[candidate_id] = label

        current = entry.data.get(CONF_DEVICE_ID)
        device_key = (
            vol.Required(CONF_DEVICE_ID, default=current)
            if current in labels
            else vol.Required(CONF_DEVICE_ID)
        )
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema({device_key: vol.In(labels)}),
            errors=errors,
            description_placeholders={
                "suffix": entry.data.get(CONF_DEVICE_SUFFIX, ""),
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        return PivotOptionsFlow()


class PivotOptionsFlow(config_entries.OptionsFlowWithReload):
    """Options flow for Pivot.

    Step 1: General settings (TTS / media player / announcements).
    Step 2: Bank entity assignment (writes directly to live text entities).

    Bank assignments are stored in entity state rather than config_entry.options
    so that entity IDs remain stable across reloads. config_entry.options holds
    only the general settings from step 1.
    """

    def __init__(self) -> None:
        self._pending: dict = {}

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step 1: General settings."""
        if user_input is not None:
            self._pending = {
                CONF_ANNOUNCEMENTS: user_input.get(CONF_ANNOUNCEMENTS, True),
                CONF_TTS_ENTITY: user_input.get(CONF_TTS_ENTITY) or "",
                CONF_MEDIA_PLAYER_ENTITY: user_input.get(CONF_MEDIA_PLAYER_ENTITY) or "",
                CONF_MANAGEMENT_MODE: MANAGEMENT_BLUEPRINTS,
            }
            return await self.async_step_banks()

        tts_sel = selector.EntitySelector(
            selector.EntitySelectorConfig(domain="tts", multiple=False)
        )
        mp_sel = selector.EntitySelector(
            selector.EntitySelectorConfig(domain="media_player", multiple=False)
        )

        # option_or_data, not `options.get(...) or data.get(...)`: a cleared
        # field is stored as "" and must stay cleared, not fall back to data.
        current_tts = option_or_data(self.config_entry, CONF_TTS_ENTITY) or None
        current_mp = option_or_data(self.config_entry, CONF_MEDIA_PLAYER_ENTITY) or None
        current_ann = bool(
            self.config_entry.options.get(CONF_ANNOUNCEMENTS,
                self.config_entry.data.get(CONF_ANNOUNCEMENTS, True))
        )

        schema_fields: dict = {}
        if current_tts:
            schema_fields[vol.Optional(CONF_TTS_ENTITY, default=current_tts)] = tts_sel
        else:
            schema_fields[vol.Optional(CONF_TTS_ENTITY)] = tts_sel
        if current_mp:
            schema_fields[vol.Optional(CONF_MEDIA_PLAYER_ENTITY, default=current_mp)] = mp_sel
        else:
            schema_fields[vol.Optional(CONF_MEDIA_PLAYER_ENTITY)] = mp_sel
        schema_fields[vol.Optional(CONF_ANNOUNCEMENTS, default=current_ann)] = selector.BooleanSelector()

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema_fields),
        )

    async def async_step_banks(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step 2: Assign entities to banks — writes directly to text entities."""
        suffix = self.config_entry.data.get(CONF_DEVICE_SUFFIX, "")
        _LOGGER.debug("async_step_banks suffix=%r", suffix)

        current = {}
        for i in range(NUM_BANKS):
            key = f"bank_{i}_entity"
            text_eid = make_entity_id("text", suffix, f"bank_{i + 1}_entity") if suffix else None
            if text_eid:
                state = self.hass.states.get(text_eid)
                _LOGGER.debug("Pre-populate %s: state=%r", text_eid, state.state if state else None)
                current[key] = (
                    state.state
                    if state and state.state not in ("unknown", "unavailable", "")
                    else ""
                )
            else:
                current[key] = self.config_entry.options.get(key, "")

        if user_input is not None:
            _LOGGER.debug("async_step_banks user_input: %s", user_input)
            for key, value in _apply_timer_banks(user_input).items():
                i = int(key.split("_")[1])
                text_eid = make_entity_id("text", suffix, f"bank_{i + 1}_entity")
                _LOGGER.debug("Writing bank %d: entity_id=%s value=%r", i + 1, text_eid, value)
                state = self.hass.states.get(text_eid)
                if state is None:
                    _LOGGER.warning("Text entity %s not found — skipping", text_eid)
                    continue
                await self.hass.services.async_call(
                    "text",
                    "set_value",
                    {"entity_id": text_eid, "value": value},
                    blocking=True,
                )

            return self.async_create_entry(title="", data=self._pending)

        return self.async_show_form(
            step_id="banks",
            data_schema=_bank_entity_schema(current),
        )
