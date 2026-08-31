"""Tests for the Pivot config flow."""
import logging

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import device_registry as dr
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.pivot.config_flow import _get_esphome_device_name
from custom_components.pivot.const import (
    CONF_DEVICE_ID,
    CONF_DEVICE_SUFFIX,
    CONF_ESPHOME_DEVICE_NAME,
    CONF_TTS_ENTITY,
    DOMAIN,
    option_or_data,
)

from .const import ESPHOME_NAME, SUFFIX


async def test_abort_without_esphome_devices(hass):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "no_esphome_devices"


# What current Home Assistant actually writes into an ESPHome config entry.
# There is no "name" key any more, and the secrets live right beside the rest.
REAL_ESPHOME_DATA = {
    "device_name": ESPHOME_NAME,
    "host": f"{ESPHOME_NAME}.local",
    "port": 6053,
    "password": "",
    "noise_psk": "",
}


async def _create_esphome_device(hass, data: dict | None = None) -> dr.DeviceEntry:
    esphome_entry = MockConfigEntry(
        domain="esphome",
        data=REAL_ESPHOME_DATA if data is None else data,
    )
    esphome_entry.add_to_hass(hass)
    dev_reg = dr.async_get(hass)
    return dev_reg.async_get_or_create(
        config_entry_id=esphome_entry.entry_id,
        identifiers={("esphome", "aa:bb:cc")},
        name="Test VPE",
    )


async def test_full_flow_creates_entry(hass):
    device = await _create_esphome_device(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_DEVICE_ID: device.id}
    )
    assert result["step_id"] == "confirm"

    # Suffix is auto-derived from the ESPHome device name for review
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"firmware_confirmed": True, CONF_DEVICE_SUFFIX: SUFFIX},
    )
    assert result["step_id"] == "options"

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["step_id"] == "banks_initial"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"timer_banks": "2", "bank_0_entity": "light.kitchen"},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_DEVICE_SUFFIX] == SUFFIX
    assert result["data"][CONF_ESPHOME_DEVICE_NAME] == ESPHOME_NAME
    assert result["data"]["bank_0_entity"] == "light.kitchen"
    assert result["data"]["bank_1_entity"] == "timer"
    await hass.async_block_till_done()

    # The created entry is set up and the initial assignments are seeded
    # into the live text entities (then stripped from entry data).
    assert hass.states.get(f"text.{SUFFIX}_bank_1_entity").state == "light.kitchen"
    assert hass.states.get(f"text.{SUFFIX}_bank_2_entity").state == "timer"


async def test_firmware_must_be_confirmed(hass):
    device = await _create_esphome_device(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_DEVICE_ID: device.id}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"firmware_confirmed": False, CONF_DEVICE_SUFFIX: SUFFIX},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"firmware_confirmed": "must_confirm_firmware"}


# --- ESPHome device-name discovery -------------------------------------------
# The suffix derived here becomes every Pivot entity ID and the name of the
# esphome.<slug>_pivot_sync_settings action, so getting it wrong breaks the
# whole integration silently.


async def test_device_name_preferred_over_host(hass):
    """device_name is canonical in current HA; host may be an IP address."""
    device = await _create_esphome_device(hass, {
        "device_name": ESPHOME_NAME,
        "host": "192.168.1.42",
    })
    assert _get_esphome_device_name(hass, device) == ESPHOME_NAME


async def test_legacy_name_key_still_supported(hass):
    """Very old ESPHome entries used "name"; keep honouring them."""
    device = await _create_esphome_device(hass, {"name": ESPHOME_NAME})
    assert _get_esphome_device_name(hass, device) == ESPHOME_NAME


async def test_host_fallback_strips_local_suffix(hass):
    device = await _create_esphome_device(hass, {"host": f"{ESPHOME_NAME}.local"})
    assert _get_esphome_device_name(hass, device) == ESPHOME_NAME


async def test_ip_address_host_is_rejected(hass):
    """An IP host must fail loudly rather than produce a bogus suffix.

    make_suffix() strips the dots, so "192.168.1.42" would silently become
    "192168142" — breaking every entity ID and the sync action name.
    """
    device = await _create_esphome_device(hass, {"host": "192.168.1.42"})
    assert _get_esphome_device_name(hass, device) is None


async def test_esphome_secrets_are_never_logged(hass, caplog):
    """entry.data holds password and noise_psk — they must not reach the log."""
    device = await _create_esphome_device(hass, {
        "device_name": ESPHOME_NAME,
        "host": f"{ESPHOME_NAME}.local",
        "password": "super-secret-password",
        "noise_psk": "super-secret-noise-psk",
    })
    with caplog.at_level(logging.DEBUG, logger="custom_components.pivot.config_flow"):
        assert _get_esphome_device_name(hass, device) == ESPHOME_NAME

    assert "super-secret-password" not in caplog.text
    assert "super-secret-noise-psk" not in caplog.text


# --- Options that can be cleared ---------------------------------------------


async def test_cleared_option_stays_cleared(hass):
    """Emptying TTS/media must stick.

    `options.get(key) or data.get(key)` cannot express "deliberately cleared":
    "" is falsy, so the old entry.data value came back and the field could
    never be emptied.
    """
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_TTS_ENTITY: "tts.old_engine"},
        options={CONF_TTS_ENTITY: ""},
    )
    assert option_or_data(entry, CONF_TTS_ENTITY) == ""


async def test_absent_option_falls_back_to_data(hass):
    """A key that was never set in options still reads from entry.data."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_TTS_ENTITY: "tts.old_engine"},
        options={},
    )
    assert option_or_data(entry, CONF_TTS_ENTITY) == "tts.old_engine"
