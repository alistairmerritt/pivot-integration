"""Tests for spoken value announcements."""
from custom_components.pivot.announcements import format_value_announcement

BLIND = {"supported_features": 15, "current_position": 40}
GARAGE = {"supported_features": 3}


async def test_positional_cover_announces_percent(hass):
    hass.states.async_set("cover.blind", "open", BLIND)
    assert format_value_announcement(hass, "cover.blind", 50) == "50 percent open."
    assert format_value_announcement(hass, "cover.blind", 0) == "Closing."
    assert format_value_announcement(hass, "cover.blind", 100) == "Opening."


async def test_open_close_only_cover_is_never_announced(hass):
    """The knob does nothing to these covers, so it must not claim it did."""
    for state in ("open", "closed"):
        hass.states.async_set("cover.garage", state, GARAGE)
        for value in (0, 50, 100):
            assert format_value_announcement(hass, "cover.garage", value) is None
