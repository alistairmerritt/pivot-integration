# Pivot Integration

[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

Custom Home Assistant integration for Pivot, a physical control dial built on the Home Assistant Voice Preview Edition (VPE). Install through HACS.

This integration works alongside [Pivot firmware](https://github.com/alistairmerritt/pivot-firmware) to expose banks, entities, settings, timer controls and Pivot-related behaviour inside Home Assistant. It provisions all required entities automatically when you add a Pivot device, and handles button toggle logic natively without requiring additional scripts or automations.

---

### Full documentation

**This README is a quick overview of this repository only.**
For installation, setup, configuration, examples and troubleshooting, use the full Pivot documentation:

**https://alistairmerritt.github.io/pivot/**

---

## What this repository contains

- Home Assistant custom integration files
- Pivot bank configuration and entity provisioning
- Entities and services used by Pivot (number, switch, text, binary sensor, light)
- Timer support
- Blueprint files for announcements and timer automations
- HACS installation support
- Integration-side logic for controlling Pivot behaviour

For full documentation on how these components work and how to set them up, see the [Pivot documentation site](https://alistairmerritt.github.io/pivot/).

## Prerequisites

Before installing the integration:

1. Your VPE must already be added to Home Assistant via the **ESPHome integration**
2. The device must be running **Pivot firmware** — see [pivot-firmware](https://github.com/alistairmerritt/pivot-firmware)
3. **Allow device to perform Home Assistant actions** must be enabled in the ESPHome integration options for your device

If you haven't set up Pivot firmware yet, start with the [getting started guide](https://alistairmerritt.github.io/pivot/getting-started/).

## Installation

Install through HACS as a custom repository:

**Repository:** `https://github.com/alistairmerritt/pivot-integration`  
**Category:** Integration

After installing, restart Home Assistant.

For the full installation and setup process, follow the Pivot documentation:

https://alistairmerritt.github.io/pivot/integration/

Or start from the beginning with the getting started guide:

https://alistairmerritt.github.io/pivot/getting-started/

> **Do not rename Pivot entity IDs.** The firmware and integration build entity IDs from your `device_suffix` at runtime. Renaming any entity ID will break the connection. If you need a friendlier label, change the entity's **Name**, not its **Entity ID**.

---

## Related links

- [Pivot documentation](https://alistairmerritt.github.io/pivot/) — installation, setup, examples and troubleshooting
- [Pivot project page](https://madewithmerritt.com/pivot/) — hardware overview and demonstrations
- [Pivot firmware](https://github.com/alistairmerritt/pivot-firmware) — ESPHome firmware for the VPE

## License

Pivot includes work derived from the official [Home Assistant Voice Preview Edition](https://github.com/esphome/home-assistant-voice-pe) ESPHome configuration and is licensed under the [Apache License 2.0](LICENSE).
