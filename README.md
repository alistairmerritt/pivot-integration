# Pivot — HA Integration

[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

A HACS integration for Home Assistant that creates the required entities, handles button toggle natively, and installs blueprint files for optional announcement and timer automations for Pivot firmware on the Home Assistant Voice Preview Edition (VPE).

> **New to Pivot?** Start at the [Pivot documentation site](https://alistairmerritt.github.io/pivot) for a full getting started guide, firmware setup, and troubleshooting.

## What is Pivot?

Pivot turns your VPE into a physical control knob for Home Assistant. Assign any entity (light, fan, media player, climate, cover, scene, or script) to each of the four colour-coded banks. Turn the knob to adjust brightness, volume, temperature, fan speed, or cover position with real-time LED feedback. Press the button to toggle or activate. Switch between normal mode (voice mode) and Control mode via a double press.

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

Blueprint files are installed automatically into `/config/blueprints/`. You create the automations yourself from the HA UI. Advanced users can also build their own automations from scratch using the fired events.

## Prerequisites

1. Your VPE must already be added to HA via the **ESPHome integration**
2. The device must be running **Pivot firmware** — see [pivot-firmware](https://github.com/alistairmerritt/pivot-firmware)
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

## Full documentation

Full entity reference, custom automation guide, file management details, and troubleshooting are all at the [Pivot documentation site](https://alistairmerritt.github.io/pivot).

## Related repositories

- [pivot-firmware](https://github.com/alistairmerritt/pivot-firmware) — ESPHome firmware for the VPE
- [pivot docs](https://alistairmerritt.github.io/pivot/) — documentation site

---

## License

Pivot includes work derived from the official [Home Assistant Voice Preview Edition](https://github.com/esphome/home-assistant-voice-pe) ESPHome configuration and is licensed under the [Apache License 2.0](LICENSE).
