// Pure rules behind the cards: what a bank shows and which rows appear.
// Ported from the button-card templates (docs: assets/dashboard-example.yaml),
// with the fixes listed in the 0.0.93 changelog.

import { ANNOUNCEABLE_DOMAINS, DEFAULT_BANK_COLORS, TIMER_PRESETS, UNSET_STATES, deviceIds, type BankIds } from './const';
import type { HassEntity, HomeAssistant } from './types';

export function num(value: string | undefined, fallback: number): number {
  const n = value === undefined ? NaN : parseFloat(value);
  return Number.isFinite(n) ? n : fallback;
}

const clamp = (v: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, v));

/** On a light card a near-white bank colour disappears; mix it toward grey for display. */
export function legibleOnLight(hex: string): string {
  const rgb = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16));
  const lum = (0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]) / 255;
  if (lum <= 0.82) return hex;
  return '#' + rgb.map((c) => Math.round(c * 0.45 + 0x70 * 0.55).toString(16).padStart(2, '0')).join('');
}

export function validHex(value: string | undefined): string | undefined {
  return value && /^#[0-9a-f]{6}$/i.test(value.trim()) ? value.trim() : undefined;
}

export interface BankView {
  n: number;
  ids: BankIds;
  /** The raw bank assignment (an entity ID, "timer", or empty). */
  raw: string;
  isTimer: boolean;
  entityId?: string;
  domain: string;
  bound?: HassEntity;
  value: number;
  passive: boolean;
  color: string;
  active: boolean;
  controlOn: boolean;
}

export function readBank(hass: HomeAssistant, suffix: string, n: number): BankView {
  const dev = deviceIds(suffix);
  const ids = dev.bank(n);
  const raw = (hass.states[ids.entity]?.state ?? '').trim();
  const isTimer = raw.toLowerCase() === 'timer';
  const entityId = !isTimer && raw.includes('.') && !UNSET_STATES.has(raw.toLowerCase()) ? raw : undefined;
  return {
    n,
    ids,
    raw,
    isTimer,
    entityId,
    domain: entityId ? entityId.split('.')[0] : '',
    bound: entityId ? hass.states[entityId] : undefined,
    value: clamp(num(hass.states[ids.value]?.state, 0), 0, 100),
    passive: hass.states[ids.passive]?.state === 'on',
    color: validHex(hass.states[ids.color]?.state) ?? DEFAULT_BANK_COLORS[n - 1],
    active: Math.round(num(hass.states[dev.activeBank]?.state, NaN)) === n,
    controlOn: hass.states[dev.toggle('control_mode')]?.state === 'on',
  };
}

/** The bound entity exists and has a usable state (the timer always counts). */
export function isLive(bank: BankView): boolean {
  if (bank.isTimer) return true;
  return !!bank.bound && !UNSET_STATES.has(bank.bound.state);
}

export function bankName(bank: BankView): string {
  if (bank.isTimer) return 'Timer';
  if (bank.entityId) return bank.bound?.attributes.friendly_name || bank.entityId;
  return 'No entity assigned';
}

export const showMirror = (bank: BankView) => bank.domain === 'light';
export const showAnnounce = (bank: BankView) => ANNOUNCEABLE_DOMAINS.has(bank.domain) && !bank.passive;
export const showSlider = (bank: BankView) => !bank.passive && (bank.isTimer || !!bank.entityId);

// ── Timer ──────────────────────────────────────────────────────────────────

export interface TimerView {
  /** The timer entities exist (they are disabled by default). */
  enabled: boolean;
  state: string;
  durationMin?: number;
  remainingSecs?: number;
}

export function readTimer(hass: HomeAssistant, suffix: string, nowMs: number): TimerView {
  const ids = deviceIds(suffix);
  const st = hass.states[ids.timerState];
  if (!st) return { enabled: false, state: 'idle' };
  const duration = num(hass.states[ids.timerDuration]?.state, NaN);
  const end = hass.states[ids.timerEnd]?.state ?? '';
  let remainingSecs: number | undefined;
  if (st.state === 'running' && /^\d{4}-\d{2}-\d{2}T/.test(end)) {
    remainingSecs = Math.max(0, Math.round((Date.parse(end) - nowMs) / 1000));
  } else if (st.state === 'paused' && /^P\d+$/.test(end)) {
    remainingSecs = parseInt(end.slice(1), 10);
  }
  return { enabled: true, state: st.state, durationMin: Number.isFinite(duration) ? duration : undefined, remainingSecs };
}

export function formatClock(totalSecs: number): string {
  const secs = Math.max(0, Math.floor(totalSecs));
  const h = Math.floor(secs / 3600);
  const m = Math.floor((secs % 3600) / 60);
  const s = String(secs % 60).padStart(2, '0');
  return h > 0 ? `${h}:${String(m).padStart(2, '0')}:${s}` : `${m}:${s}`;
}

const mins = (m: number) => `${m} ${m === 1 ? 'min' : 'mins'}`;

/** Python's round(): halves go to the even neighbour (round(30.5) == 30). */
function roundHalfEven(x: number): number {
  const r = Math.round(x);
  return Math.abs(x % 1) === 0.5 && r % 2 !== 0 ? r - 1 : r;
}

/** Minutes the integration derives from a knob value (bank_control.py, same arithmetic). */
export function minutesFromValue(value: number): number {
  return clamp(roundHalfEven(1 + (value / 100.0) * (60 - 1)), 1, 60);
}

/** Bank value whose gauge matches a duration. */
export function valueFromMinutes(minutes: number): number {
  return clamp(((minutes - 1) / 59) * 100, 0, 100);
}

/** Legacy minutes for a bank value, used only when the timer entities are disabled. */
function legacyMinutes(value: number): number {
  const preset = TIMER_PRESETS.find((p) => p.value === Math.round(value));
  return preset ? preset.minutes : Math.round((value / 100) * 60);
}

export function timerLabel(timer: TimerView, bankValue: number): string {
  if (timer.state === 'alerting') return 'Timer Finished';
  if (timer.state === 'running' && timer.remainingSecs !== undefined) return formatClock(timer.remainingSecs);
  if (timer.state === 'paused' && timer.remainingSecs !== undefined) return `Paused – ${formatClock(timer.remainingSecs)}`;
  if (timer.enabled && timer.durationMin !== undefined) return mins(Math.round(timer.durationMin));
  return mins(legacyMinutes(bankValue));
}

/** Bar position for the timer bank: the time left while counting, the duration while idle. */
export function timerBarValue(timer: TimerView, bankValue: number): number {
  const total = timer.durationMin !== undefined ? timer.durationMin * 60 : undefined;
  if ((timer.state === 'running' || timer.state === 'paused') && timer.remainingSecs !== undefined && total) {
    // A voice timer can run longer than the stored duration; trust the gauge then.
    if (timer.remainingSecs <= total + 2) return clamp((timer.remainingSecs / total) * 100, 0, 100);
    return bankValue;
  }
  if (timer.state === 'idle' && timer.enabled && timer.durationMin !== undefined) return valueFromMinutes(timer.durationMin);
  return bankValue;
}

export function selectedPreset(timer: TimerView, bankValue: number): number | undefined {
  if (timer.state !== 'idle') return undefined;
  if (timer.enabled && timer.durationMin !== undefined) {
    return TIMER_PRESETS.find((p) => p.minutes === Math.round(timer.durationMin!))?.minutes;
  }
  return TIMER_PRESETS.find((p) => p.value === Math.round(bankValue))?.minutes;
}

// ── Value label ────────────────────────────────────────────────────────────

const COVER_STATES: Record<string, string> = { open: 'Open', closed: 'Closed', opening: 'Opening', closing: 'Closing' };

export function valueLabel(bank: BankView, timer: TimerView): string {
  if (bank.isTimer) return timerLabel(timer, bank.value);
  if (!isLive(bank)) return '';
  const state = bank.bound!.state;
  const rounded = Math.round(bank.value);
  if (bank.passive) {
    if (bank.domain === 'cover') return COVER_STATES[state] ?? '';
    if (state === 'on') return 'On';
    return bank.value === 0 ? 'Off' : 'On';
  }
  if (bank.domain === 'cover') {
    if (rounded === 0) return 'Closed';
    if (rounded === 100) return 'Open';
    return `${rounded}% Open`;
  }
  if (bank.domain === 'climate') {
    const temp = bank.bound!.attributes.temperature;
    return temp === undefined || temp === null || temp === '' ? '' : `${Math.round(Number(temp))}°`;
  }
  if (state === 'off') return 'Off';
  return rounded === 0 ? '' : `${rounded}%`;
}

/** The fill is hidden while the bound entity is off (the template's transparent progress). */
export function fillHidden(bank: BankView): boolean {
  return !bank.isTimer && bank.bound?.state === 'off';
}
