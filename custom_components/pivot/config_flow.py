"""Config flow for Pivot."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import device_registry as dr, selector

from .const import (
    DOMAIN,
    CONF_DEVICE_ID,
    CONF_ESPHOME_DEVICE_NAME,
    CONF_DEVICE_SUFFIX,
    CONF_FRIENDLY_NAME,
    CONF_ANNOUNCEMENTS,
    CONF_TTS_ENTITY,
    CONF_MEDIA_PLAYER_ENTITY,
    CONF_SATELLITE_ENTITY,
    CONF_MANAGEMENT_MODE,
    MANAGEMENT_MANAGED,
    MANAGEMENT_BLUEPRINTS,
    MANAGEMENT_NEITHER,
    NUM_BANKS,
    BANK_NAMES,
    make_suffix,
)

_LOGGER = logging.getLogger(__name__)

# Config keys for bank entity assignments
CONF_BANK_ENTITIES = [f"bank_{i}_entity" for i in range(NUM_BANKS)]


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


def _get_esphome_device_name(hass: HomeAssistant, device: dr.DeviceEntry) -> str | None:
    """Return the ESPHome device name (e.g. 'home-assistant-voice-0aaae0').

    ESPHome config entries store the hostname in entry.data["host"] as either
    "home-assistant-voice-0aaae0.local" or "home-assistant-voice-0aaae0".
    We strip the .local suffix to get the bare device name.
    """
    for eid in device.config_entries:
        entry = hass.config_entries.async_get_entry(eid)
        if entry and entry.domain == "esphome":
            _LOGGER.debug(
                "ESPHome entry for device %s: title=%r data=%s",
                device.id, entry.title, dict(entry.data)
            )
            # Try "name" first (older ESPHome versions), then "host"
            name = entry.data.get("name") or entry.data.get("host") or ""
            # Strip .local suffix if present
            name = name.removesuffix(".local").strip()
            if name:
                return name
            # Last resort: use title but warn — this will be the friendly name, not device name
            _LOGGER.warning(
                "Could not find ESPHome device name in entry data for %s, "
                "falling back to title %r — this may cause entity ID mismatches",
                device.id, entry.title
            )
            return entry.title
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
    """Build a schema with a timer-bank multi-select and one EntitySelector per bank.

    A 'timer_banks' multi-select lets users mark any bank as a timer bank without
    typing the reserved value 'timer' into an entity field. The step handler writes
    'timer' to those banks and ignores their entity picker value.
    Entity pickers are shown for all banks but left blank for timer banks.
    """
    current = current or {}
    fields = {}

    timer_defaults = [
        str(i + 1)
        for i in range(NUM_BANKS)
        if current.get(f"bank_{i}_entity") == "timer"
    ]
    fields[vol.Optional("timer_banks", default=timer_defaults)] = selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[
                selector.SelectOptionDict(value="1", label="Bank 1"),
                selector.SelectOptionDict(value="2", label="Bank 2"),
                selector.SelectOptionDict(value="3", label="Bank 3"),
                selector.SelectOptionDict(value="4", label="Bank 4"),
            ],
            multiple=True,
            mode=selector.SelectSelectorMode.LIST,
        )
    )

    entity_sel = selector.EntitySelector(
        selector.EntitySelectorConfig(
            domain=["light", "switch", "fan", "climate", "media_player", "cover", "scene", "script", "input_number", "number"],
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
    """Return a dict of bank_N_entity values with timer banks resolved.

    Banks selected in 'timer_banks' are set to 'timer'; all others use the
    entity picker value (or empty string).
    """
    timer_banks = user_input.get("timer_banks", [])
    result = {}
    for i in range(NUM_BANKS):
        key = f"bank_{i}_entity"
        if str(i + 1) in timer_banks:
            result[key] = "timer"
        else:
            result[key] = user_input.get(key) or ""
    return result


class PivotConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Three-step config flow for Pivot."""

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
    # Step 2: Firmware confirmation + device suffix entry
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
                if not raw:
                    errors[CONF_DEVICE_SUFFIX] = "suffix_required"
                else:
                    suffix = make_suffix(raw)
                    if _suffix_in_use(self.hass, suffix):
                        errors[CONF_DEVICE_SUFFIX] = "suffix_collision"
                    else:
                        self._device_suffix = suffix
                        return await self.async_step_options()

        return self.async_show_form(
            step_id="confirm",
            data_schema=vol.Schema({
                vol.Required("firmware_confirmed", default=False): bool,
                vol.Required(CONF_DEVICE_SUFFIX, default=""): str,
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
            # Store options data and proceed to bank entity assignment
            self._pending_entry_data = {
                CONF_DEVICE_ID: self._selected_device_id,
                CONF_ESPHOME_DEVICE_NAME: self._esphome_device_name,
                CONF_DEVICE_SUFFIX: self._device_suffix,
                CONF_FRIENDLY_NAME: self._friendly_name,
                CONF_ANNOUNCEMENTS: user_input.get(CONF_ANNOUNCEMENTS, True),
                CONF_TTS_ENTITY: user_input.get(CONF_TTS_ENTITY) or "",
                CONF_MEDIA_PLAYER_ENTITY: user_input.get(CONF_MEDIA_PLAYER_ENTITY) or "",
                CONF_MANAGEMENT_MODE: user_input.get(CONF_MANAGEMENT_MODE, MANAGEMENT_BLUEPRINTS),
            }
            return await self.async_step_banks_initial()

        tts_sel = selector.EntitySelector(
            selector.EntitySelectorConfig(domain="tts", multiple=False)
        )
        mp_sel = selector.EntitySelector(
            selector.EntitySelectorConfig(domain="media_player", multiple=False)
        )
        mode_sel = selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[
                    selector.SelectOptionDict(value=MANAGEMENT_BLUEPRINTS, label="Blueprint setup"),
                    selector.SelectOptionDict(value=MANAGEMENT_NEITHER, label="Manual setup"),
                ],
                mode=selector.SelectSelectorMode.LIST,
            )
        )

        return self.async_show_form(
            step_id="options",
            data_schema=vol.Schema({
                vol.Required(CONF_MANAGEMENT_MODE, default=MANAGEMENT_BLUEPRINTS): mode_sel,
                vol.Required(CONF_ANNOUNCEMENTS, default=True): bool,
                vol.Optional(CONF_TTS_ENTITY): tts_sel,
                vol.Optional(CONF_MEDIA_PLAYER_ENTITY): mp_sel,
            }),
            description_placeholders={
                "device_name": self._friendly_name,
            },
        )

    async def async_step_banks_initial(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step 3 (initial setup only): Assign entities to banks."""
        from .const import entity_id as make_entity_id

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

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        return PivotOptionsFlow()


class PivotOptionsFlow(config_entries.OptionsFlowWithReload):
    """
    Options flow for Pivot:
      1. General settings (management mode + announcements)
      2. Bank entity assignment
    """

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step 1: General settings."""
        current_mode = (
            self.config_entry.options.get(CONF_MANAGEMENT_MODE)
            or self.config_entry.data.get(CONF_MANAGEMENT_MODE)
            or MANAGEMENT_BLUEPRINTS
        )
        # Treat legacy managed mode as blueprints
        if current_mode == MANAGEMENT_MANAGED:
            current_mode = MANAGEMENT_BLUEPRINTS

        if user_input is not None:
            new_mode = user_input.get(CONF_MANAGEMENT_MODE, MANAGEMENT_BLUEPRINTS)
            self._pending = {
                CONF_ANNOUNCEMENTS: user_input[CONF_ANNOUNCEMENTS],
                CONF_TTS_ENTITY: user_input.get(CONF_TTS_ENTITY) or "",
                CONF_MEDIA_PLAYER_ENTITY: user_input.get(CONF_MEDIA_PLAYER_ENTITY) or "",
                CONF_MANAGEMENT_MODE: new_mode,
            }
            return await self.async_step_banks()

        tts_sel = selector.EntitySelector(
            selector.EntitySelectorConfig(domain="tts", multiple=False)
        )
        mp_sel = selector.EntitySelector(
            selector.EntitySelectorConfig(domain="media_player", multiple=False)
        )
        mode_sel = selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[
                    selector.SelectOptionDict(value=MANAGEMENT_BLUEPRINTS, label="Blueprint setup"),
                    selector.SelectOptionDict(value=MANAGEMENT_NEITHER, label="Manual setup"),
                ],
                mode=selector.SelectSelectorMode.LIST,
            )
        )

        current_tts = (
            self.config_entry.options.get(CONF_TTS_ENTITY)
            or self.config_entry.data.get(CONF_TTS_ENTITY)
            or None
        )
        current_mp = (
            self.config_entry.options.get(CONF_MEDIA_PLAYER_ENTITY)
            or self.config_entry.data.get(CONF_MEDIA_PLAYER_ENTITY)
            or None
        )

        schema_fields: dict = {
            vol.Required(CONF_MANAGEMENT_MODE, default=current_mode or MANAGEMENT_BLUEPRINTS): mode_sel,
            vol.Required(
                CONF_ANNOUNCEMENTS,
                default=self.config_entry.options.get(
                    CONF_ANNOUNCEMENTS,
                    self.config_entry.data.get(CONF_ANNOUNCEMENTS, True),
                ),
            ): bool,
        }
        if current_tts:
            schema_fields[vol.Optional(CONF_TTS_ENTITY, default=current_tts)] = tts_sel
        else:
            schema_fields[vol.Optional(CONF_TTS_ENTITY)] = tts_sel
        if current_mp:
            schema_fields[vol.Optional(CONF_MEDIA_PLAYER_ENTITY, default=current_mp)] = mp_sel
        else:
            schema_fields[vol.Optional(CONF_MEDIA_PLAYER_ENTITY)] = mp_sel

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema_fields),
        )

    async def async_step_banks(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step 2: Assign entities to banks — writes directly to text entities."""
        from .const import CONF_DEVICE_SUFFIX, entity_id as make_entity_id

        suffix = self.config_entry.data.get(CONF_DEVICE_SUFFIX, "")
        _LOGGER.debug("async_step_banks suffix=%r", suffix)

        current = {}
        for i in range(NUM_BANKS):
            key = f"bank_{i}_entity"
            text_eid = make_entity_id("text", suffix, key) if suffix else None
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
                text_eid = make_entity_id("text", suffix, key)
                _LOGGER.debug("Writing bank %d: entity_id=%s value=%r", i, text_eid, value)
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
