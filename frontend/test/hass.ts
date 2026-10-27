// A synthetic Home Assistant for the tests: one Pivot device ("pv_desk")
// whose four banks cover a light, a switch, a number and the timer.
import type { HassEntity, HomeAssistant } from '../src/types';

export const S = 'pv_desk';

export interface Call {
  domain: string;
  service: string;
  data: Record<string, unknown>;
}

function st(entity_id: string, state: string, attributes: Record<string, unknown> = {}): HassEntity {
  return { entity_id, state, attributes, last_changed: '2026-01-01T00:00:00Z', last_updated: '2026-01-01T00:00:00Z' };
}

export function baseStates(): Record<string, HassEntity> {
  const list = [
    st(`number.${S}_active_bank`, '1.0'),
    st(`switch.${S}_control_mode`, 'on'),
    st(`switch.${S}_announcements`, 'on'),
    st(`switch.${S}_mute_announcements`, 'off'),
    st(`switch.${S}_show_control_value`, 'on'),
    st(`switch.${S}_dim_when_idle`, 'off'),
    st(`text.${S}_media_player_entity`, 'media_player.desk_speaker'),
    st('media_player.desk_speaker', 'idle', { volume_level: 0.4 }),
    st(`select.${S}_timer_state`, 'idle'),
    st(`number.${S}_timer_duration`, '25.0'),
    st(`text.${S}_timer_end`, ''),
    st('light.desk_lamp', 'on', { friendly_name: 'Desk Lamp', brightness: 128 }),
    st('switch.fan_heater', 'off', { friendly_name: 'Fan Heater' }),
    st('input_number.speaker_volume', '30', { friendly_name: 'Speaker Volume' }),
    st('switch.desk_vpe_timer_silent_mode', 'off', { friendly_name: 'Desk VPE Timer Silent Mode' }),
  ];
  const banks: [string, string, string, string][] = [
    ['light.desk_lamp', '50.0', 'off', '#2889FF'],
    ['switch.fan_heater', '0.0', 'on', '#FF7D19'],
    ['input_number.speaker_volume', '30.0', 'off', '#97FF3D'],
    ['timer', '41.0', 'off', '#C800FF'],
  ];
  banks.forEach(([entity, value, passive, color], i) => {
    const n = i + 1;
    list.push(
      st(`text.${S}_bank_${n}_entity`, entity),
      st(`number.${S}_bank_${n}_value`, value),
      st(`binary_sensor.${S}_bank_${n}_passive`, passive),
      st(`text.${S}_bank_${n}_color`, color),
      st(`switch.${S}_bank_${n}_mirror_light`, 'off'),
      st(`switch.${S}_bank_${n}_announce_value`, 'off'),
    );
  });
  return Object.fromEntries(list.map((s) => [s.entity_id, s]));
}

export function makeHass(overrides: Record<string, Partial<HassEntity> | null> = {}, opts: { registry?: boolean } = {}) {
  const states = baseStates();
  for (const [id, patch] of Object.entries(overrides)) {
    if (patch === null) delete states[id];
    else states[id] = { ...(states[id] ?? { entity_id: id, attributes: {}, last_changed: '', last_updated: '' }), ...patch } as HassEntity;
  }
  const calls: Call[] = [];
  const registry = opts.registry !== false;
  const hass: HomeAssistant & { calls: Call[] } = {
    states,
    entities: registry
      ? {
          [`number.${S}_active_bank`]: { entity_id: `number.${S}_active_bank`, device_id: 'dev_pivot', platform: 'pivot' },
          [`switch.${S}_control_mode`]: { entity_id: `switch.${S}_control_mode`, device_id: 'dev_pivot', platform: 'pivot' },
          'switch.desk_vpe_timer_silent_mode': { entity_id: 'switch.desk_vpe_timer_silent_mode', device_id: 'dev_esp', platform: 'esphome', name: 'Timer Silent Mode' },
          'switch.desk_vpe_mute': { entity_id: 'switch.desk_vpe_mute', device_id: 'dev_esp', platform: 'esphome', name: 'Mute' },
        }
      : undefined,
    devices: registry
      ? {
          dev_pivot: { id: 'dev_pivot', name: S, name_by_user: 'Desk Pivot', identifiers: [['pivot', 'dev_esp']], manufacturer: 'Pivot' },
          dev_esp: { id: 'dev_esp', name: 'Desk VPE', name_by_user: null, identifiers: [], manufacturer: 'Espressif' },
        }
      : undefined,
    services: { pivot: { timer_toggle: {}, timer_cancel: {} }, number: { set_value: {} }, switch: { toggle: {} } },
    themes: {},
    calls,
    callService: async (domain, service, data = {}) => {
      calls.push({ domain, service, data });
    },
  };
  return hass;
}
