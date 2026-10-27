// Entity IDs, labels and rules shared by the cards. Entity IDs are pinned by
// the integration (const.py) as <platform>.<suffix>_<key>; the firmware relies
// on them, so they never vary.

export const NUM_BANKS = 4;
export const DOCS_URL = 'https://alistairmerritt.github.io/pivot/dashboard/';
export const TIMER_DOCS_URL = 'https://alistairmerritt.github.io/pivot/timer/';

/** Matches the integration's BANK_COLORS_HEX, used when a colour entity is unreadable. */
export const DEFAULT_BANK_COLORS = ['#2889FF', '#FF7D19', '#97FF3D', '#C800FF'];

/** Domains whose knob value can be announced (announcements.py ANNOUNCEABLE_DOMAINS). */
export const ANNOUNCEABLE_DOMAINS = new Set(['light', 'fan', 'climate', 'media_player', 'cover', 'number', 'input_number']);

export const UNSET_STATES = new Set(['', 'unknown', 'unavailable', 'none']);

export type ToggleKey = 'control_mode' | 'announcements' | 'mute_announcements' | 'show_control_value' | 'dim_when_idle';
export type SettingsRow = ToggleKey | 'volume';

export const DEVICE_ROWS: SettingsRow[] = ['control_mode', 'volume'];
export const BEHAVIOUR_ROWS: SettingsRow[] = ['announcements', 'mute_announcements', 'show_control_value', 'dim_when_idle'];
export const ALL_ROWS: SettingsRow[] = [...DEVICE_ROWS, ...BEHAVIOUR_ROWS];

export const TOGGLE_TEXT: Record<ToggleKey, { title: string; description: string }> = {
  control_mode: { title: 'Control Mode', description: 'Enable or disable Pivot control' },
  announcements: { title: 'System Announcements', description: 'Announce bank changes and triple-press via voice' },
  mute_announcements: { title: 'Mute Announcements', description: 'Silence all spoken announcements temporarily' },
  show_control_value: { title: 'Display Persistent Value', description: 'Keep current value visible on the LED ring when idle' },
  dim_when_idle: { title: 'Dim Gauge LEDs While Idle', description: 'Reduce LED brightness when not interacting with dial' },
};

/** Timer presets: the bank value the knob path needs (24 -> 15 min, etc.) and the minutes it means. */
export const TIMER_PRESETS = [
  { minutes: 15, value: 24, label: '15m' },
  { minutes: 30, value: 50, label: '30m' },
  { minutes: 45, value: 75, label: '45m' },
  { minutes: 60, value: 100, label: '60m' },
];

export interface BankIds {
  entity: string;
  value: string;
  passive: string;
  color: string;
  colorLight: string;
  mirror: string;
  announce: string;
}

export interface DeviceIds {
  activeBank: string;
  mediaPlayerText: string;
  timerState: string;
  timerDuration: string;
  timerEnd: string;
  toggle(key: ToggleKey): string;
  bank(n: number): BankIds;
}

export function deviceIds(suffix: string): DeviceIds {
  return {
    activeBank: `number.${suffix}_active_bank`,
    mediaPlayerText: `text.${suffix}_media_player_entity`,
    timerState: `select.${suffix}_timer_state`,
    timerDuration: `number.${suffix}_timer_duration`,
    timerEnd: `text.${suffix}_timer_end`,
    toggle: (key) => `switch.${suffix}_${key}`,
    bank: (n) => ({
      entity: `text.${suffix}_bank_${n}_entity`,
      value: `number.${suffix}_bank_${n}_value`,
      passive: `binary_sensor.${suffix}_bank_${n}_passive`,
      color: `text.${suffix}_bank_${n}_color`,
      colorLight: `light.${suffix}_bank_${n}_color_light`,
      mirror: `switch.${suffix}_bank_${n}_mirror_light`,
      announce: `switch.${suffix}_bank_${n}_announce_value`,
    }),
  };
}
