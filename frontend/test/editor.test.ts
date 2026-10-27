import { afterEach, describe, expect, it } from 'vitest';
import '../src/index';
import { fromForm, parsePresets, toForm, type EditorKind, type FormSchema, type PivotCardEditor } from '../src/editor';
import type { LovelaceCardConfig } from '../src/types';
import { S, makeHass } from './hass';

const roundTrip = (kind: EditorKind, config: Record<string, unknown>) => {
  const full = { type: `custom:pivot-${kind}-card`, device: S, ...config } as LovelaceCardConfig;
  return fromForm(kind, toForm(kind, full), full);
};
const edit = (kind: EditorKind, config: Record<string, unknown>, change: Record<string, unknown>) => {
  const full = { type: `custom:pivot-${kind}-card`, device: S, ...config } as LovelaceCardConfig;
  return fromForm(kind, { ...toForm(kind, full), ...change }, full);
};

function editor(kind: EditorKind, config: Record<string, unknown> = {}) {
  const el = document.createElement('pivot-card-editor') as PivotCardEditor;
  el.kind = kind;
  el.hass = makeHass();
  el.setConfig({ type: `custom:pivot-${kind}-card`, device: S, ...config });
  return el;
}
const names = (schema: FormSchema[]): string[] => schema.flatMap((s) => (s.type === 'expandable' ? names(s.schema ?? []) : [s.name]));

afterEach(() => {
  document.body.innerHTML = '';
});

describe('editor: writes only what differs from the defaults', () => {
  it('an untouched config stays minimal for every card', () => {
    for (const kind of ['device', 'status', 'settings'] as EditorKind[]) {
      expect(roundTrip(kind, {})).toEqual({ type: `custom:pivot-${kind}-card`, device: S });
    }
    expect(roundTrip('bank', { bank: 2 })).toEqual({ type: 'custom:pivot-bank-card', device: S, bank: 2 });
  });

  it('device card options come back as the documented keys', () => {
    expect(
      edit('device', {}, {
        show_title: false,
        name: ' Bedroom ',
        show_active_bank: false,
        banks_mode: 'choose',
        banks_chosen: ['3', '1'],
        hide_unassigned: true,
        bank_columns: '2',
        show_edit: false,
        show_bank_options: false,
        timer_presets: ['30', '5'],
        show_silent_timer: false,
        settings_rows: ['volume', 'control_mode'],
        settings_headings: false,
        settings_background: true,
        settings_position: 'below',
      }),
    ).toEqual({
      type: 'custom:pivot-device-card',
      device: S,
      show_title: false,
      name: 'Bedroom',
      show_active_bank: false,
      banks: [1, 3],
      hide_unassigned: true,
      bank_columns: 2,
      show_edit: false,
      show_bank_options: false,
      timer_presets: [5, 30],
      show_silent_timer: false,
      settings_rows: ['control_mode', 'volume'],
      settings_headings: false,
      settings_background: true,
      settings_position: 'below',
    });
  });

  it('a single followed bank drops the options that only apply to lists', () => {
    expect(edit('device', { hide_unassigned: true, bank_columns: 2 }, { banks_mode: 'active' })).toEqual({
      type: 'custom:pivot-device-card',
      device: S,
      banks: 'active',
    });
  });

  it('turning the settings off keeps the row choice for later', () => {
    expect(edit('device', { settings_rows: ['control_mode'] }, { show_settings: false })).toMatchObject({
      show_settings: false,
      settings_rows: ['control_mode'],
    });
  });

  it('removing every preset is kept as an empty list', () => {
    expect(edit('bank', { bank: 4 }, { timer_presets: [] })).toMatchObject({ timer_presets: [] });
  });

  it('the bank card keeps active and timer as words', () => {
    expect(edit('bank', {}, { bank: 'active' }).bank).toBe('active');
    expect(edit('bank', {}, { bank: 'timer' }).bank).toBe('timer');
    expect(edit('bank', {}, { bank: '3' }).bank).toBe(3);
  });

  it('the 0.0.93 keys are read and rewritten as the new ones', () => {
    expect(roundTrip('device', { show_status: false })).toEqual({
      type: 'custom:pivot-device-card',
      device: S,
      show_title: false,
      show_active_bank: false,
    });
    expect(roundTrip('status', { show_name: false })).toEqual({ type: 'custom:pivot-status-card', device: S, show_title: false });
  });

  it('keeps keys it does not manage', () => {
    expect(roundTrip('bank', { bank: 1, grid_options: { columns: 6 }, visibility: [] })).toMatchObject({
      grid_options: { columns: 6 },
      visibility: [],
    });
  });

  it('presets: whole minutes from 1 to 60, each once, sorted, at most six', () => {
    expect(parsePresets(['30', '5', 'abc', '5', '90', '0', '2.5', ' 12 '])).toEqual([5, 12, 30]);
    expect(parsePresets(['1', '2', '3', '4', '5', '6', '7'])).toEqual([1, 2, 3, 4, 5, 6]);
    expect(parsePresets(undefined)).toEqual([]);
  });
});

describe('editor: fields follow the choices', () => {
  it('the device card groups its options under Banks, Timer and Settings', () => {
    const el = editor('device');
    const schema = el._schema(toForm('device', el._config!));
    expect(schema.filter((s) => s.type === 'expandable').map((s) => s.title)).toEqual(['Banks', 'Timer', 'Settings']);
    expect(names(schema)).toEqual([
      'device', 'show_title', 'name', 'show_active_bank',
      'banks_mode', 'hide_unassigned', 'bank_columns', 'show_edit', 'show_bank_options',
      'timer_presets', 'show_silent_timer', 'timer_silent_entity',
      'show_settings', 'settings_rows', 'settings_headings', 'settings_background', 'settings_position',
    ]);
  });

  it('Choose banks adds the bank list, labelled with what each bank controls', () => {
    const el = editor('device', { banks: [1] });
    const schema = el._schema(toForm('device', el._config!));
    const chosen = schema.flatMap((s) => s.schema ?? []).find((s) => s.name === 'banks_chosen')!;
    const options = (chosen.selector!.select as { options: { label: string }[] }).options.map((o) => o.label);
    expect(options).toEqual(['Bank 1 · Desk Lamp', 'Bank 2 · Fan Heater', 'Bank 3 · Speaker Volume', 'Bank 4 · Timer']);
  });

  it('following one bank hides the list options; hiding settings hides their options', () => {
    const el = editor('device', { banks: 'timer', show_settings: false });
    const fields = names(el._schema(toForm('device', el._config!)));
    expect(fields).not.toContain('hide_unassigned');
    expect(fields).not.toContain('bank_columns');
    expect(fields).not.toContain('settings_rows');
    expect(fields).toContain('show_settings');
  });

  it('the title box is disabled, not removed, while the title is hidden', () => {
    const el = editor('status', { show_title: false });
    const name = el._schema(toForm('status', el._config!)).find((s) => s.name === 'name')!;
    expect(name.disabled).toBe(true);
  });

  it('the bank card offers the active and timer banks', () => {
    const el = editor('bank', { bank: 2 });
    const bank = el._schema(toForm('bank', el._config!)).find((s) => s.name === 'bank')!;
    expect((bank.selector!.select as { options: { value: string }[] }).options.map((o) => o.value)).toEqual(['1', '2', '3', '4', 'active', 'timer']);
  });
});

describe('editor: plain controls when ha-form is missing', () => {
  it('draws the same fields and writes a tidy config', async () => {
    const el = editor('device');
    document.body.append(el);
    el._haForm = false;
    await el.updateComplete;
    const root = el.shadowRoot!;
    expect([...root.querySelectorAll('legend')].map((l) => l.textContent)).toEqual(['Banks', 'Timer', 'Settings']);
    const changes: LovelaceCardConfig[] = [];
    el.addEventListener('config-changed', (e) => changes.push((e as CustomEvent).detail.config));
    const box = [...root.querySelectorAll('label.check')].find((l) => l.textContent!.includes('Show EDIT ENTITY'))!.querySelector('input')!;
    box.checked = false;
    box.dispatchEvent(new Event('change'));
    expect(changes).toEqual([{ type: 'custom:pivot-device-card', device: S, show_edit: false }]);
  });
});
