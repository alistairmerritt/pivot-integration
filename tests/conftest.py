"""Shared fixtures for Pivot tests."""
import pytest
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    MockModule,
    mock_integration,
)

from custom_components.pivot.const import DOMAIN

from .const import ENTRY_DATA


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading custom integrations in all tests."""
    return


@pytest.fixture(autouse=True)
def mock_esphome(hass):
    """Satisfy the manifest's esphome dependency without the real
    integration (whose usb/bluetooth/ffmpeg chain cannot load in tests)."""
    mock_integration(hass, MockModule("esphome"))


@pytest.fixture
async def setup_pivot(hass):
    """Set up a Pivot config entry and return it."""
    entry = MockConfigEntry(domain=DOMAIN, data=dict(ENTRY_DATA), title="Test VPE")
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry
