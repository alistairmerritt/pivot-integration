# Pivot — HA Integration

[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

A HACS integration for Home Assistant that creates the required entities, handles button toggle natively, and installs blueprint files for optional announcement and timer automations for Pivot firmware on the Home Assistant Voice Preview Edition (VPE).

> **New to Pivot?** Start at the [Pivot documentation site](https://alistairmerritt.github.io/pivot) for a full getting started guide, firmware setup, and troubleshooting.

## What is Pivot?

Pivot turns your VPE into a physical control knob for Home Assistant. Assign any entity (light, fan, media player, climate, cover, scene, or script) to each of the four colour-coded banks. Turn the knob to adjust brightness, volume, temperature, fan speed, or cover position with real-time LED feedback. Press the button to toggle or activate. Switch between Normal mode (voice mode) and Control mode via a double press.

### Banks

| Bank | Default Colour |
| ---- | -------------- |
| 1 | Blue |
| 2 | Orange |
| 3 | Green |
| 4 | Purple |

Switch banks by holding the knob and turning. The LED ring changes colour to show the active bank.

## What the integration does

When you add a Pivot device, the integration always:

1. **Creates all entities** — number, switch, text, binary sensor, and light entities attached to your ESPHome device
2. **Starts bank control** — listens internally for knob turns and applies values to assigned entities
3. **Syncs with your assigned entity** — when you switch banks, the knob value snaps to the assigned entity's current state
4. **Handles button toggle natively** — single press in Control Mode toggles or activates the active bank's entity automatically, no script required
5. **Fires events** — `pivot_knob_turn` and `pivot_button_press` on the HA event bus for use in your own automations

Blueprint files are installed automatically into `/config/blueprints/`. You create the automations yourself from the HA UI. Advanced users can also build their own automations from scratch using the fired events — see [Custom Automations](https://alistairmerritt.github.io/pivot/automations/).

## Prerequisites

1. Your VPE must already be added to HA via the **ESPHome integration**
2. The device must be running **Pivot firmware** (ESPHome Device Builder 2026.4.0 or later required) — see [pivot-firmware](https://github.com/alistairmerritt/pivot-firmware)
3. **Allow device to perform Home Assistant actions** must be enabled in the ESPHome integration options for your device

## Installation

### Via HACS

1. HACS → Integrations → ⋮ → Custom repositories
2. Add `https://github.com/alistairmerritt/pivot-integration`, category: **Integration**
3. Search for **Pivot** and install
4. Restart Home Assistant

### Manual

Copy `custom_components/pivot` into your HA `custom_components` directory and restart.

## Setup

1. Settings → Devices & Services → Add Integration → search **Pivot**
2. Select your VPE from the dropdown
3. Confirm and enter the `device_suffix` from your firmware YAML
4. Optionally configure a TTS service and media player — these are shared across all blueprints automatically
5. Go to **Configure** on the integration to assign entities to each bank

For a detailed walkthrough see the [getting started guide](https://alistairmerritt.github.io/pivot/getting-started/).

## Entities created

### Number entities

| Entity | Purpose |
| --- | --- |
| `number.{suffix}_bank_1_value` through `_bank_4_value` | Bank values (0–100%) |
| `number.{suffix}_active_bank` | Active bank (1–4) |

### Switch entities

| Entity | Purpose |
| --- | --- |
| `switch.{suffix}_control_mode` | Control Mode vs Normal (voice) Mode |
| `switch.{suffix}_show_control_value` | Keep gauge LEDs permanently visible in Control Mode |
| `switch.{suffix}_dim_when_idle` | Dim gauge LEDs to 50% after 2 s of inactivity (requires Show Control Value) |
| `switch.{suffix}_announcements` | Enable/disable bank-change and triple-press TTS announcements |
| `switch.{suffix}_mute_announcements` | Temporarily mute all spoken announcements without changing other settings |
| `switch.{suffix}_bank_N_mirror_light` | Mirror assigned RGB light colour on the LED ring (per bank) |
| `switch.{suffix}_bank_N_announce_value` | Announce entity value via TTS after knob settles (per bank) |

### Text entities

| Entity | Purpose |
| --- | --- |
| `text.{suffix}_bank_N_entity` | Entity assigned to each bank |
| `text.{suffix}_tts_entity` | TTS service used by announcements and Timer blueprint |
| `text.{suffix}_media_player_entity` | Speaker used by announcements and Timer blueprint |

### Timer entities (disabled by default)

Enable in the HA entity registry if you want to use the [Pivot Timer](https://alistairmerritt.github.io/pivot/timer/) feature.

| Entity | Purpose |
| --- | --- |
| `number.{suffix}_timer_duration` | Timer duration in minutes (1–60) |
| `select.{suffix}_timer_state` | Timer state — idle, running, or paused |
| `text.{suffix}_timer_end` | Internal — stores the countdown end time |

> **Do not rename Pivot entity IDs.** The firmware and integration build entity IDs from your `device_suffix` at runtime. Renaming any entity ID will break the connection. If you need a friendlier label, change the entity's **Name**, not its **Entity ID**.

## Supported entity domains

| Domain | Knob (Control Mode) | Button press |
| --- | --- | --- |
| `light` | Brightness % | Toggle on/off |
| `media_player` | Volume (0–100%) | Play/pause |
| `fan` | Speed % | Toggle on/off |
| `climate` | Temperature (16–30°C) | Toggle on/off |
| `cover` | Position % | Toggle open/close |
| `input_number` / `number` | Value scaled to entity min–max | — |
| `switch` / `input_boolean` | — | Toggle |
| `scene` | — | Activate |
| `script` | — | Run |

## Full documentation

Full entity reference, custom automation guide, and troubleshooting are at the [Pivot documentation site](https://alistairmerritt.github.io/pivot).

## Related repositories

- [pivot-firmware](https://github.com/alistairmerritt/pivot-firmware) — ESPHome firmware for the VPE
- [pivot docs](https://alistairmerritt.github.io/pivot/) — documentation site

---

## License

Pivot includes work derived from the official [Home Assistant Voice Preview Edition](https://github.com/esphome/home-assistant-voice-pe) ESPHome configuration and is licensed under the [Apache License 2.0](LICENSE).
