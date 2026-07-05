"""Shared constants for Pivot tests."""
from custom_components.pivot.const import (
    CONF_ANNOUNCEMENTS,
    CONF_DEVICE_ID,
    CONF_DEVICE_SUFFIX,
    CONF_ESPHOME_DEVICE_NAME,
    CONF_FRIENDLY_NAME,
    CONF_MANAGEMENT_MODE,
    CONF_MEDIA_PLAYER_ENTITY,
    CONF_TTS_ENTITY,
    MANAGEMENT_NEITHER,
)

SUFFIX = "test_vpe"
ESPHOME_NAME = "home-assistant-voice-test1"
ESPHOME_SLUG = "home_assistant_voice_test1"
SYNC_SERVICE = f"{ESPHOME_SLUG}_pivot_sync_settings"

ENTRY_DATA = {
    CONF_DEVICE_ID: "fake-device-id",
    CONF_ESPHOME_DEVICE_NAME: ESPHOME_NAME,
    CONF_DEVICE_SUFFIX: SUFFIX,
    CONF_FRIENDLY_NAME: "Test VPE",
    CONF_ANNOUNCEMENTS: False,
    CONF_TTS_ENTITY: "",
    CONF_MEDIA_PLAYER_ENTITY: "",
    # "neither" skips the blueprint notification during tests
    CONF_MANAGEMENT_MODE: MANAGEMENT_NEITHER,
}
