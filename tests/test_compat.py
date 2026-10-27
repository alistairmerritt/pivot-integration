"""Compatibility with newer Home Assistant behaviour and with other integrations."""
from types import SimpleNamespace

from custom_components.pivot.const import device_entry_ids

from .const import SUFFIX


def test_device_entry_ids_before_2026_10():
    """Older Home Assistant: a device lists its config entries."""
    device = SimpleNamespace(config_entries={"esphome_entry", "other_entry"})
    assert device_entry_ids(device) == {"esphome_entry", "other_entry"}


class _Device:
    """A 2026.10+ device entry: config_entries still works but is deprecated."""

    def __init__(self, entry_id, composite=False, all_entries=()):
        self.config_entry_id = entry_id
        self.is_composite_device = composite
        self._all = set(all_entries)
        self.deprecated_reads = 0

    @property
    def config_entries(self):
        if not self.is_composite_device:
            self.deprecated_reads += 1
        return self._all or ({self.config_entry_id} if self.config_entry_id else set())


def test_device_entry_ids_2026_10_uses_config_entry_id():
    device = _Device("esphome_entry")
    assert device_entry_ids(device) == {"esphome_entry"}
    assert device.deprecated_reads == 0


def test_device_entry_ids_2026_10_without_an_entry():
    device = _Device(None)
    assert device_entry_ids(device) == set()
    assert device.deprecated_reads == 0


def test_device_entry_ids_2026_10_restored_composite():
    device = _Device("esphome_entry", composite=True, all_entries={"esphome_entry", "other_entry"})
    assert device_entry_ids(device) == {"esphome_entry", "other_entry"}
    assert device.deprecated_reads == 0


async def test_colour_light_reports_a_brightness(hass, setup_pivot):
    """An RGB light with brightness None breaks Google Assistant's state queries."""
    state = hass.states.get(f"light.{SUFFIX}_bank_1_color_light")
    assert state.attributes["color_mode"] == "rgb"
    assert state.attributes["brightness"] == 255
