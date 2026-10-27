import { describe, expect, it } from 'vitest';
import { findPivotDevice, listPivotDevices } from '../src/discovery';
import { S, makeHass } from './hass';

describe('device discovery', () => {
  it('finds Pivot devices from the registry with their display name', () => {
    expect(listPivotDevices(makeHass())).toEqual([
      { suffix: S, name: 'Desk Pivot', deviceId: 'dev_pivot', esphomeDeviceId: 'dev_esp', timerSilentEntity: 'switch.desk_vpe_timer_silent_mode' },
    ]);
  });
  it('finds the silent switch by name when its entity ID was renamed', () => {
    const hass = makeHass();
    hass.entities!['switch.renamed'] = { entity_id: 'switch.renamed', device_id: 'dev_esp', platform: 'esphome', name: 'Timer Silent Mode' };
    delete hass.entities!['switch.desk_vpe_timer_silent_mode'];
    expect(findPivotDevice(hass, S)?.timerSilentEntity).toBe('switch.renamed');
  });
  it('falls back to states when the registry is not available', () => {
    expect(listPivotDevices(makeHass({}, { registry: false }))).toEqual([{ suffix: S, name: S }]);
  });
  it('returns nothing for an unknown suffix', () => {
    expect(findPivotDevice(makeHass(), 'nope')).toBeUndefined();
  });
});
