import { describe, expect, it } from 'vitest';
import {
  activeBankNumber,
  bankName,
  banksToShow,
  formatClock,
  legibleOnLight,
  minutesFromValue,
  readBank,
  readTimer,
  selectedPreset,
  showAnnounce,
  showMirror,
  showSlider,
  timerBankNumber,
  timerBarValue,
  timerLabel,
  timerPresets,
  timerPresetsError,
  valueFromMinutes,
  valueLabel,
} from '../src/logic';
import { S, makeHass } from './hass';

const NOW = Date.parse('2026-01-01T12:00:00Z');
const label = (overrides: Parameters<typeof makeHass>[0], n: number) => {
  const hass = makeHass(overrides);
  return valueLabel(readBank(hass, S, n), readTimer(hass, S, NOW));
};

describe('reading a bank', () => {
  it('reads the bound entity, value, colour and active state', () => {
    const b = readBank(makeHass(), S, 1);
    expect(b).toMatchObject({ entityId: 'light.desk_lamp', domain: 'light', value: 50, color: '#2889FF', active: true, controlOn: true, passive: false });
    expect(bankName(b)).toBe('Desk Lamp');
  });
  it('treats "timer" as the timer, not an entity', () => {
    const b = readBank(makeHass(), S, 4);
    expect(b.isTimer).toBe(true);
    expect(b.entityId).toBeUndefined();
    expect(bankName(b)).toBe('Timer');
  });
  it('names an empty bank plainly and falls back to the default colour', () => {
    const b = readBank(makeHass({ [`text.${S}_bank_2_entity`]: { state: '' }, [`text.${S}_bank_2_color`]: { state: 'garbage' } }), S, 2);
    expect(bankName(b)).toBe('No entity assigned');
    expect(b.color).toBe('#FF7D19');
    expect(showSlider(b)).toBe(false);
  });
  it('shows the raw entity ID when the bound entity is missing', () => {
    expect(bankName(readBank(makeHass({ 'light.desk_lamp': null }), S, 1))).toBe('light.desk_lamp');
  });
});

describe('value label', () => {
  it('percent for a dimmable entity', () => expect(label({}, 1)).toBe('50%'));
  it('Off when the entity is off', () => expect(label({ 'light.desk_lamp': { state: 'off' } }, 1)).toBe('Off'));
  it('nothing at 0 or when unavailable', () => {
    expect(label({ [`number.${S}_bank_3_value`]: { state: '0' } }, 3)).toBe('');
    expect(label({ 'light.desk_lamp': { state: 'unavailable' } }, 1)).toBe('');
  });
  it('On/Off for passive switches', () => {
    expect(label({}, 2)).toBe('Off');
    expect(label({ 'switch.fan_heater': { state: 'on' } }, 2)).toBe('On');
  });
  it('Open/Closed for passive covers, by state', () => {
    const cover = { [`text.${S}_bank_2_entity`]: { state: 'cover.garage' }, 'cover.garage': { state: 'closing', attributes: {} } };
    expect(label(cover, 2)).toBe('Closing');
  });
  it('position wording for positional covers', () => {
    const o = { [`text.${S}_bank_3_entity`]: { state: 'cover.blind' }, 'cover.blind': { state: 'open', attributes: {} } };
    expect(label({ ...o, [`number.${S}_bank_3_value`]: { state: '0' } }, 3)).toBe('Closed');
    expect(label({ ...o, [`number.${S}_bank_3_value`]: { state: '100' } }, 3)).toBe('Open');
    expect(label({ ...o, [`number.${S}_bank_3_value`]: { state: '42.4' } }, 3)).toBe('42% Open');
  });
  it('target temperature for climate', () => {
    const o = { [`text.${S}_bank_3_entity`]: { state: 'climate.room' }, 'climate.room': { state: 'cool', attributes: { temperature: 21.6 } } };
    expect(label(o, 3)).toBe('22°');
  });
});

describe('timer', () => {
  it('idle reads the real duration, not the gauge', () => expect(label({}, 4)).toBe('25 mins'));
  it('one minute is singular', () => expect(label({ [`number.${S}_timer_duration`]: { state: '1' } }, 4)).toBe('1 min'));
  it('running counts down as m:ss', () => {
    const end = new Date(NOW + 754_000).toISOString();
    expect(label({ [`select.${S}_timer_state`]: { state: 'running' }, [`text.${S}_timer_end`]: { state: end } }, 4)).toBe('12:34');
  });
  it('hours show as h:mm:ss', () => expect(formatClock(3725)).toBe('1:02:05'));
  it('paused shows the time left', () => {
    expect(label({ [`select.${S}_timer_state`]: { state: 'paused' }, [`text.${S}_timer_end`]: { state: 'P125' } }, 4)).toBe('Paused – 2:05');
  });
  it('alerting says so', () => expect(label({ [`select.${S}_timer_state`]: { state: 'alerting' } }, 4)).toBe('Timer Finished'));
  it('falls back to the gauge when the timer entities are disabled', () => {
    const hass = makeHass({ [`select.${S}_timer_state`]: null });
    const t = readTimer(hass, S, NOW);
    expect(t.enabled).toBe(false);
    expect(timerLabel(t, 50)).toBe('30 mins');
    expect(timerLabel(t, 24)).toBe('15 mins');
  });
  it('maps knob values to minutes exactly like the integration', () => {
    expect([0, 24, 50, 75, 100].map(minutesFromValue)).toEqual([1, 15, 30, 45, 60]);
    for (let m = 1; m <= 60; m++) expect(minutesFromValue(valueFromMinutes(m))).toBe(m);
  });
  it('matches Python for every knob value (generated from bank_control.py arithmetic)', () => {
    const python = [1, 2, 2, 3, 3, 4, 5, 5, 6, 6, 7, 7, 8, 9, 9, 10, 10, 11, 12, 12, 13, 13, 14, 15, 15, 16, 16, 17, 18, 18, 19, 19, 20, 20, 21, 22, 22, 23, 23, 24, 25, 25, 26, 26, 27, 28, 28, 29, 29, 30, 30, 31, 32, 32, 33, 33, 34, 35, 35, 36, 36, 37, 38, 38, 39, 39, 40, 41, 41, 42, 42, 43, 43, 44, 45, 45, 46, 46, 47, 48, 48, 49, 49, 50, 51, 51, 52, 52, 53, 54, 54, 55, 55, 56, 56, 57, 58, 58, 59, 59, 60];
    expect(Array.from({ length: 101 }, (_, v) => minutesFromValue(v))).toEqual(python);
  });
  it('bar drains with the time left and shows the duration when idle', () => {
    expect(timerBarValue({ enabled: true, state: 'running', durationMin: 10, remainingSecs: 300 }, 0)).toBeCloseTo(50);
    expect(timerBarValue({ enabled: true, state: 'idle', durationMin: 60 }, 0)).toBe(100);
    // A voice timer longer than the stored duration: trust the gauge.
    expect(timerBarValue({ enabled: true, state: 'running', durationMin: 5, remainingSecs: 900 }, 37)).toBe(37);
  });
  it('highlights the preset matching the duration', () => {
    expect(selectedPreset({ enabled: true, state: 'idle', durationMin: 30 }, 0)).toBe(30);
    expect(selectedPreset({ enabled: true, state: 'idle', durationMin: 31 }, 0)).toBeUndefined();
    expect(selectedPreset({ enabled: true, state: 'running', durationMin: 30 }, 0)).toBeUndefined();
  });
});

describe('which rows show', () => {
  it('Mirror only for lights; Announce for supported, non-passive domains', () => {
    const hass = makeHass();
    const [light, sw, num, timer] = [1, 2, 3, 4].map((n) => readBank(hass, S, n));
    expect([light, sw, num, timer].map(showMirror)).toEqual([true, false, false, false]);
    expect([light, sw, num, timer].map(showAnnounce)).toEqual([true, false, true, false]);
    expect([light, sw, num, timer].map(showSlider)).toEqual([true, false, true, true]);
  });
  it('a passive cover gets no Announce row', () => {
    const b = readBank(makeHass({ [`text.${S}_bank_2_entity`]: { state: 'cover.garage' }, 'cover.garage': { state: 'open', attributes: {} } }), S, 2);
    expect(showAnnounce(b)).toBe(false);
  });
});

describe('colours on light themes', () => {
  it('darkens only near-white colours', () => {
    expect(legibleOnLight('#2889FF')).toBe('#2889FF');
    expect(legibleOnLight('#FFFEFA')).not.toBe('#FFFEFA');
  });
});

describe('timer presets', () => {
  it('the default four keep the templates’ bank values', () => {
    expect(timerPresets().map((p) => [p.minutes, p.value])).toEqual([[15, 24], [30, 50], [45, 75], [60, 100]]);
    expect(timerPresets([30]).map((p) => p.value)).toEqual([50]);
  });

  it('any minute from 1 to 60 gets a bank value the integration reads back as that minute', () => {
    for (let m = 1; m <= 60; m++) {
      const [preset] = timerPresets([m]);
      expect(preset.label).toBe(`${m}m`);
      expect(minutesFromValue(preset.value)).toBe(m);
    }
  });

  it('a custom preset shows as selected for its duration', () => {
    const timer = readTimer(makeHass({ [`number.${S}_timer_duration`]: { state: '10.0' } }), S, NOW);
    expect(selectedPreset(timer, 0, timerPresets([5, 10]))).toBe(10);
    expect(selectedPreset(timer, 0)).toBeUndefined();
  });

  it('validates the option', () => {
    expect(timerPresetsError(undefined)).toBeUndefined();
    expect(timerPresetsError([])).toBeUndefined();
    expect(timerPresetsError([5, 10, 60])).toBeUndefined();
    expect(timerPresetsError([0])).toMatch(/1 to 60/);
    expect(timerPresetsError([1, 2, 3, 4, 5, 6, 7])).toMatch(/at most 6/);
    expect(timerPresetsError([5, 5])).toMatch(/twice/);
    expect(timerPresetsError({})).toMatch(/list of minutes/);
  });
});

describe('which banks', () => {
  it('finds the active bank and the timer bank', () => {
    expect(activeBankNumber(makeHass({ [`number.${S}_active_bank`]: { state: '2.0' } }), S)).toBe(2);
    expect(activeBankNumber(makeHass({ [`number.${S}_active_bank`]: { state: 'unknown' } }), S)).toBeUndefined();
    expect(activeBankNumber(makeHass({ [`number.${S}_active_bank`]: { state: '7' } }), S)).toBeUndefined();
    expect(timerBankNumber(makeHass(), S)).toBe(4);
    expect(timerBankNumber(makeHass({ [`text.${S}_bank_2_entity`]: { state: ' Timer ' } }), S)).toBe(2);
    expect(timerBankNumber(makeHass({ [`text.${S}_bank_4_entity`]: { state: '' } }), S)).toBeUndefined();
  });

  it('lists banks in order, without the empty ones when asked', () => {
    const hass = makeHass({ [`text.${S}_bank_3_entity`]: { state: 'unknown' } });
    expect(banksToShow(hass, S, 'all', false)).toEqual([1, 2, 3, 4]);
    expect(banksToShow(hass, S, 'all', true)).toEqual([1, 2, 4]);
    expect(banksToShow(hass, S, [4, 3, 1, 1], true)).toEqual([1, 4]);
  });
});
