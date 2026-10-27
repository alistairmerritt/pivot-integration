// Finds Pivot devices from what the frontend already knows, so a card only
// needs the device suffix: no entity IDs typed by hand.
//
// Each Pivot config entry owns a "Pivot" device whose identifiers are
// [["pivot", <linked ESPHome device id>]]. The Pivot entities live on it; the
// timer silent switch lives on the ESPHome device, under an entity ID that
// does not follow the suffix (e.g. switch.spare_vpe_timer_silent_mode).

import type { HomeAssistant } from './types';

export interface PivotDevice {
  suffix: string;
  name: string;
  deviceId?: string;
  esphomeDeviceId?: string;
  timerSilentEntity?: string;
}

const ACTIVE_BANK = /^number\.(.+)_active_bank$/;
const registryCache = new WeakMap<object, { devices: unknown; list: PivotDevice[] }>();

function silentSwitchFor(hass: HomeAssistant, esphomeDeviceId: string | undefined): string | undefined {
  if (!esphomeDeviceId || !hass.entities) return undefined;
  const candidates = Object.values(hass.entities).filter(
    (e) => e.device_id === esphomeDeviceId && e.entity_id.startsWith('switch.'),
  );
  return (
    candidates.find((e) => e.entity_id.endsWith('_timer_silent_mode'))?.entity_id ??
    candidates.find((e) => (e.name ?? '').toLowerCase() === 'timer silent mode')?.entity_id
  );
}

function fromRegistry(hass: HomeAssistant): PivotDevice[] {
  const out: PivotDevice[] = [];
  for (const entry of Object.values(hass.entities ?? {})) {
    if (entry.platform !== 'pivot') continue;
    const match = ACTIVE_BANK.exec(entry.entity_id);
    if (!match) continue;
    const device = entry.device_id ? hass.devices?.[entry.device_id] : undefined;
    const esphomeDeviceId = device?.identifiers?.find((i) => i[0] === 'pivot')?.[1];
    out.push({
      suffix: match[1],
      name: device?.name_by_user || device?.name || match[1],
      deviceId: entry.device_id,
      esphomeDeviceId,
      timerSilentEntity: silentSwitchFor(hass, esphomeDeviceId),
    });
  }
  return out;
}

function fromStates(hass: HomeAssistant): PivotDevice[] {
  const out: PivotDevice[] = [];
  for (const id of Object.keys(hass.states)) {
    const match = ACTIVE_BANK.exec(id);
    if (match && hass.states[`text.${match[1]}_bank_1_entity`]) out.push({ suffix: match[1], name: match[1] });
  }
  return out;
}

/** All Pivot devices, sorted by name. Cached per registry snapshot. */
export function listPivotDevices(hass: HomeAssistant | undefined): PivotDevice[] {
  if (!hass) return [];
  let list: PivotDevice[] | undefined;
  if (hass.entities && Object.keys(hass.entities).length) {
    const cached = registryCache.get(hass.entities);
    if (cached && cached.devices === hass.devices) list = cached.list;
    else {
      list = fromRegistry(hass).sort((a, b) => a.name.localeCompare(b.name));
      registryCache.set(hass.entities, { devices: hass.devices, list });
    }
  }
  // Older frontends, or a registry that has not loaded yet: fall back to states.
  return list && list.length ? list : fromStates(hass).sort((a, b) => a.name.localeCompare(b.name));
}

export function findPivotDevice(hass: HomeAssistant | undefined, suffix: string | undefined): PivotDevice | undefined {
  if (!hass || !suffix) return undefined;
  return (
    listPivotDevices(hass).find((d) => d.suffix === suffix) ??
    (hass.states[`number.${suffix}_active_bank`] ? { suffix, name: suffix } : undefined)
  );
}
