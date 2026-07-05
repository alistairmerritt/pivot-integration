"""Tests for the Pivot config flow."""
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import device_registry as dr
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.pivot.const import (
    CONF_DEVICE_ID,
    CONF_DEVICE_SUFFIX,
    CONF_ESPHOME_DEVICE_NAME,
    DOMAIN,
)

from .const import ESPHOME_NAME, SUFFIX


async def test_abort_without_esphome_devices(hass):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "no_esphome_devices"


async def _create_esphome_device(hass) -> dr.DeviceEntry:
    esphome_entry = MockConfigEntry(domain="esphome", data={"name": ESPHOME_NAME})
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
