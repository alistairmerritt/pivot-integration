# Pivot — HA Integration

A HACS integration for Home Assistant that creates the required entities and, depending on setup mode, can also create the automation logic for Pivot firmware on the Home Assistant Voice Preview Edition (VPE).

> **New to Pivot?** Start at the [Pivot documentation site](https://alistairmerritt.github.io/pivot-docs) for a full getting started guide, firmware setup, and troubleshooting.

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
4. **Fires events** — `pivot_knob_turn` and `pivot_button_press` on the HA event bus for use in your own automations

What happens next depends on the **setup mode** you choose:

| Mode | What Pivot does |
| --- | --- |
| **Automatic** | Writes `pivot_{suffix}_bank_toggle.yaml` and `pivot_{suffix}_announcements.yaml`, adds a single `!include` line to your `scripts.yaml` and `automations.yaml`. Fully managed — created and removed automatically. |
| **Blueprints** | Copies blueprint files into `/config/blueprints/`. You create the automations yourself from the HA UI. |
| **Manual** | Pivot does not touch any of your YAML files. Bank control and event firing still work — use the fired events to build your own automations. |

The setup mode can be changed at any time from the integration's **Configure** menu.

## Prerequisites

1. Your VPE must already be added to HA via the **ESPHome integration**
2. The device must be running **Pivot firmware** — see [pivot-firmware](https://github.com/alistairmerritt/pivot-firmware)
3. **Allow device to perform Home Assistant actions** must be enabled in the ESPHome integration options for your device

## Installation

### Via HACS

1. HACS → Integrations → ⋮ → Custom repositories
2. Add `https://github.com/alistairmerritt/pivot`, category: **Integration**
3. Search for **Pivot** and install
4. Restart Home Assistant

### Manual

Copy `custom_components/pivot` into your HA `custom_components` directory and restart.

## Setup

1. Settings → Devices & Services → Add Integration → search **Pivot**
2. Select your VPE from the dropdown
3. Confirm and enter the `device_suffix` from your firmware YAML
4. Choose a setup mode and optionally configure announcements
5. Go to **Configure** on the integration to assign entities to each bank

For a detailed walkthrough see the [getting started guide](https://alistairmerritt.github.io/pivot-docs/getting-started).

## Full documentation

Full entity reference, custom automation guide, file management details, and troubleshooting are all at the [Pivot documentation site](https://alistairmerritt.github.io/pivot-docs).

## Related repositories

- [pivot-firmware](https://github.com/alistairmerritt/pivot-firmware) — ESPHome firmware for the VPE
- [pivot-docs](https://github.com/alistairmerritt/pivot-docs) — documentation site
