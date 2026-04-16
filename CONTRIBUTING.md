# Contributing to Pivot Integration

Thanks for your interest in contributing. Contributions of all kinds are welcome — bug reports, fixes, documentation improvements, and feature suggestions.

## Before you start

- Check the [open issues](https://github.com/alistairmerritt/pivot-integration/issues) to see if your bug or idea is already tracked.
- For large changes, open an issue first to discuss the approach before writing code.

## How to contribute

1. Fork the repository and create a branch from `main`.
2. Make your changes inside `custom_components/pivot/`.
3. Test with real hardware running Pivot firmware. State what you tested in the PR.
4. Open a pull request. Fill in the PR template — describe what changed, why, and how you tested it.

## What to test

Before opening a PR, verify:

- Home Assistant does not log errors on startup after installing the integration
- Entity creation works correctly for a new device (number, switch, text, light entities all appear)
- Bank control works — turning the knob adjusts the assigned entity
- Button toggle works — single press in Control Mode activates or toggles the assigned entity
- The `pivot_knob_turn` and `pivot_button_press` events fire correctly

If your change touches a specific entity type, bank logic, or announcement behaviour, test that path specifically.

## HACS compliance

- `hacs.json` must be kept valid
- `manifest.json` must include accurate `requirements`, `dependencies`, and `version`
- Do not introduce new Python dependencies without updating `manifest.json`

## Coding style

Follow the patterns already in `custom_components/pivot/`. Use type hints. Keep Home Assistant API usage compatible with the minimum HA version declared in `manifest.json`.

## Reporting bugs

Use the [bug report template](https://github.com/alistairmerritt/pivot-integration/issues/new?template=bug_report.md). Include your integration version, Home Assistant version, and relevant log output.

## Questions

If you have a question about how Pivot works, open a [discussion](https://github.com/alistairmerritt/pivot-integration/discussions) rather than an issue.
