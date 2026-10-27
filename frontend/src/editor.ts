// <pivot-card-editor>: the visual editor for all four cards. Uses Home
// Assistant's ha-form; if that cannot be loaded, draws the same fields with
// plain controls. The form works on a flat copy of the options (toForm) and
// writes back a tidy config that leaves out every default (fromForm).
import { mdiCogOutline, mdiKnob, mdiTimerOutline } from '@mdi/js';
import { LitElement, css, html, nothing, type TemplateResult } from 'lit';
import { fire } from './actions';
import { ALL_ROWS, DEFAULT_TIMER_MINUTES, MAX_TIMER_PRESETS, NUM_BANKS, TOGGLE_TEXT, type SettingsRow } from './const';

export { parseTimerPresets as parsePresets };
import { listPivotDevices } from './discovery';
import { bankName, parseTimerPresets, readBank } from './logic';
import { defineElement } from './register';
import type { HomeAssistant, LovelaceCardConfig } from './types';

export type EditorKind = 'device' | 'bank' | 'status' | 'settings';
type FormData = Record<string, unknown>;

/** The slice of Home Assistant's ha-form schema the editor uses. */
export interface FormSchema {
  name: string;
  type?: 'expandable';
  title?: string;
  iconPath?: string;
  expanded?: boolean;
  flatten?: boolean;
  required?: boolean;
  disabled?: boolean;
  selector?: Record<string, Record<string, unknown>>;
  schema?: FormSchema[];
}

const ROW_LABELS: Record<SettingsRow, string> = {
  control_mode: TOGGLE_TEXT.control_mode.title,
  volume: 'Pivot Device Volume',
  announcements: TOGGLE_TEXT.announcements.title,
  mute_announcements: TOGGLE_TEXT.mute_announcements.title,
  show_control_value: TOGGLE_TEXT.show_control_value.title,
  dim_when_idle: TOGGLE_TEXT.dim_when_idle.title,
};

const HEADINGS_LABEL = 'Show "Device" and "Behaviour" headings';
const BACKGROUND_LABEL = 'Put settings on a card background';
const LABELS: Record<string, string> = {
  device: 'Pivot device',
  bank: 'Bank',
  name: 'Title (optional)',
  show_title: 'Show title',
  show_active_bank: 'Show active bank',
  banks_mode: 'Banks to show',
  banks_chosen: 'Which banks',
  hide_unassigned: 'Hide banks with nothing assigned',
  bank_columns: 'Banks per row',
  show_edit: 'Show EDIT ENTITY',
  show_bank_options: 'Show Mirror Light Colour and Announce Value',
  timer_presets: 'Timer presets (minutes)',
  show_silent_timer: 'Show Silent Timer',
  timer_silent_entity: 'Timer silent switch (optional, found automatically)',
  show_settings: 'Show device and behaviour settings',
  settings_rows: 'Settings to show',
  rows: 'Settings to show',
  settings_headings: HEADINGS_LABEL,
  headings: HEADINGS_LABEL,
  settings_background: BACKGROUND_LABEL,
  background: BACKGROUND_LABEL,
  settings_position: 'Position',
};

const HELPERS: Record<string, string> = {
  bank: 'The active bank follows the dial. The timer bank finds whichever bank is the timer.',
  bank_columns: 'Two per row needs about 610 px for the banks. Narrower, they stack.',
  timer_presets: `Up to ${MAX_TIMER_PRESETS}, each 1 to 60 minutes. Remove them all to keep just play and cancel.`,
  show_settings: 'Turn off to put them somewhere else with the Pivot settings card.',
};

/** Suggestions in the presets picker; any whole minute from 1 to 60 can be typed. */
const PRESET_SUGGESTIONS = [1, 2, 3, 5, 10, 15, 20, 25, 30, 40, 45, 50, 60];

/** Options each kind of card owns: anything else in the config (grid_options, visibility, ...) is kept as it is. */
const MANAGED: Record<EditorKind, string[]> = {
  device: [
    'device', 'name', 'show_title', 'show_active_bank', 'show_status', 'banks', 'hide_unassigned', 'bank_columns',
    'show_edit', 'show_bank_options', 'timer_presets', 'show_silent_timer', 'timer_silent_entity',
    'show_settings', 'settings_rows', 'settings_headings', 'settings_background', 'settings_position',
  ],
  bank: ['device', 'bank', 'show_edit', 'show_bank_options', 'timer_presets', 'show_silent_timer', 'timer_silent_entity'],
  status: ['device', 'name', 'show_title', 'show_name', 'show_active_bank'],
  settings: ['device', 'rows', 'headings', 'background'],
};

const sameList = (a: readonly unknown[], b: readonly unknown[]) => a.length === b.length && a.every((x, i) => x === b[i]);

/** The config as flat form fields, with every default filled in. */
export function toForm(kind: EditorKind, config: LovelaceCardConfig): FormData {
  const c = config as Record<string, unknown>;
  const bankOptions = {
    show_edit: c.show_edit !== false,
    show_bank_options: c.show_bank_options !== false,
    timer_presets: (Array.isArray(c.timer_presets) ? c.timer_presets : DEFAULT_TIMER_MINUTES).map(String),
    show_silent_timer: c.show_silent_timer !== false,
    timer_silent_entity: c.timer_silent_entity ?? '',
  };
  const device = c.device ?? '';
  if (kind === 'device') {
    const statusOn = c.show_status !== false;
    return {
      device,
      show_title: statusOn && c.show_title !== false,
      name: c.name ?? '',
      show_active_bank: statusOn && c.show_active_bank !== false,
      banks_mode: Array.isArray(c.banks) ? 'choose' : (c.banks ?? 'all'),
      banks_chosen: Array.isArray(c.banks) ? c.banks.map(String) : ['1', '2', '3', '4'],
      hide_unassigned: c.hide_unassigned === true,
      bank_columns: String(c.bank_columns ?? 1),
      ...bankOptions,
      show_settings: c.show_settings !== false,
      settings_rows: Array.isArray(c.settings_rows) ? c.settings_rows : [...ALL_ROWS],
      settings_headings: c.settings_headings !== false,
      settings_background: c.settings_background === true,
      settings_position: c.settings_position ?? 'beside',
    };
  }
  if (kind === 'bank') return { device, bank: String(c.bank ?? 1), ...bankOptions };
  if (kind === 'status') {
    return { device, show_title: c.show_title !== false && c.show_name !== false, name: c.name ?? '', show_active_bank: c.show_active_bank !== false };
  }
  return { device, rows: Array.isArray(c.rows) ? c.rows : [...ALL_ROWS], headings: c.headings !== false, background: c.background === true };
}

/** The form fields back as a card config: defaults left out, unknown keys kept. */
export function fromForm(kind: EditorKind, data: FormData, previous: LovelaceCardConfig | undefined): LovelaceCardConfig {
  const next: LovelaceCardConfig = { type: previous?.type ?? `custom:pivot-${kind}-card`, device: data.device ?? '' };
  const off = (key: string) => {
    if (data[key] === false) next[key] = false;
  };
  const on = (key: string) => {
    if (data[key] === true) next[key] = true;
  };
  // Stored as typed: trimming here would eat the space after a word while
  // it is being typed. The cards trim when they draw it.
  const text = (key: string) => {
    const value = typeof data[key] === 'string' ? (data[key] as string) : '';
    if (value.trim()) next[key] = value;
  };
  // A hand-written row order survives the editor: rows keep their place and
  // newly ticked ones go on the end. A list in the usual order stays in it.
  const rows = (key: string, value: unknown) => {
    const chosen = Array.isArray(value) ? (value as SettingsRow[]) : [];
    const before = Array.isArray(previous?.[key]) ? (previous![key] as SettingsRow[]) : ALL_ROWS;
    const custom = !sameList(before, ALL_ROWS.filter((r) => before.includes(r)));
    const list = custom
      ? [...before.filter((r) => chosen.includes(r)), ...ALL_ROWS.filter((r) => chosen.includes(r) && !before.includes(r))]
      : ALL_ROWS.filter((r) => chosen.includes(r));
    if (!sameList(list, ALL_ROWS)) next[key] = list;
  };
  const bankOptions = () => {
    off('show_edit');
    off('show_bank_options');
    const presets = parseTimerPresets(data.timer_presets);
    if (!sameList(presets, DEFAULT_TIMER_MINUTES)) next.timer_presets = presets;
    off('show_silent_timer');
    text('timer_silent_entity');
  };

  if (kind === 'device') {
    off('show_title');
    text('name');
    off('show_active_bank');
    const mode = data.banks_mode;
    if (mode === 'choose') {
      const chosen = (Array.isArray(data.banks_chosen) ? data.banks_chosen : []).map(Number).filter((n) => n >= 1 && n <= NUM_BANKS);
      next.banks = [...new Set(chosen)].sort((a, b) => a - b);
    } else if (mode === 'active' || mode === 'timer') {
      next.banks = mode;
    }
    if (mode !== 'active' && mode !== 'timer') {
      on('hide_unassigned');
      if (String(data.bank_columns) === '2') next.bank_columns = 2;
    }
    bankOptions();
    off('show_settings');
    rows('settings_rows', data.settings_rows);
    off('settings_headings');
    on('settings_background');
    if (data.settings_position === 'below') next.settings_position = 'below';
  } else if (kind === 'bank') {
    const bank = String(data.bank ?? '1');
    next.bank = /^[1-4]$/.test(bank) ? Number(bank) : bank;
    bankOptions();
  } else if (kind === 'status') {
    off('show_title');
    text('name');
    off('show_active_bank');
  } else {
    rows('rows', data.rows);
    off('headings');
    on('background');
  }
  for (const [key, value] of Object.entries(previous ?? {})) {
    if (!(key in next) && !MANAGED[kind].includes(key)) next[key] = value;
  }
  return next;
}

const boolean = (name: string, extra: Partial<FormSchema> = {}): FormSchema => ({ name, selector: { boolean: {} }, ...extra });
const radios = (name: string, options: { value: string; label: string }[]): FormSchema => ({ name, selector: { select: { mode: 'list', options } } });
const checklist = (name: string, options: { value: string; label: string }[]): FormSchema => ({
  name,
  selector: { select: { multiple: true, mode: 'list', options } },
});
const section = (title: string, iconPath: string, schema: FormSchema[], expanded = false): FormSchema => ({
  name: '',
  type: 'expandable',
  flatten: true,
  title,
  iconPath,
  expanded,
  schema,
});
const rowOptions = () => ALL_ROWS.map((r) => ({ value: r, label: ROW_LABELS[r] }));

let haFormReady: Promise<boolean> | undefined;

/** ha-form is lazy-loaded by Home Assistant; nudge it by opening a built-in card's editor. */
function ensureHaForm(): Promise<boolean> {
  if (customElements.get('ha-form')) return Promise.resolve(true);
  haFormReady ??= (async () => {
    try {
      const helpers = await window.loadCardHelpers?.();
      const card = helpers?.createCardElement({ type: 'entities', entities: [] }) as
        | (HTMLElement & { constructor: { getConfigElement?: () => Promise<unknown> } })
        | undefined;
      await card?.constructor.getConfigElement?.();
    } catch {
      /* fall through to the timeout */
    }
    return Promise.race([
      customElements.whenDefined('ha-form').then(() => true),
      new Promise<boolean>((resolve) => setTimeout(() => resolve(!!customElements.get('ha-form')), 3000)),
    ]);
  })();
  return haFormReady;
}

export class PivotCardEditor extends LitElement {
  static override properties = {
    hass: { attribute: false },
    kind: {},
    _config: { state: true },
    _haForm: { state: true },
  };

  declare hass?: HomeAssistant;
  declare kind: EditorKind;
  declare _config?: LovelaceCardConfig;
  declare _haForm?: boolean;

  constructor() {
    super();
    this.kind = 'device';
  }

  static override styles = css`
    .fallback {
      display: grid;
      gap: 12px;
    }
    fieldset {
      display: grid;
      gap: 10px;
      margin: 0;
      padding: 10px 12px 12px;
      border: 1px solid var(--divider-color, #444);
      border-radius: 12px;
    }
    legend {
      padding: 0 4px;
      font-weight: 500;
    }
    label {
      display: grid;
      gap: 4px;
      font-size: 14px;
    }
    label.check {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .group {
      display: grid;
      gap: 4px;
      font-size: 14px;
    }
    select,
    input[type='text'] {
      font: inherit;
      padding: 8px;
      border-radius: 6px;
      border: 1px solid var(--divider-color, #ccc);
      background: var(--card-background-color, transparent);
      color: var(--primary-text-color);
    }
    .hint {
      font-size: 13px;
      color: var(--secondary-text-color);
    }
  `;

  setConfig(config: LovelaceCardConfig): void {
    this._config = config;
  }

  override connectedCallback(): void {
    super.connectedCallback();
    ensureHaForm().then((ok) => (this._haForm = ok));
  }

  private get _devices() {
    return listPivotDevices(this.hass);
  }

  /** "Bank 1 · Desk Lamp", so banks can be picked by what they control. */
  private _bankOptions(): { value: string; label: string }[] {
    const suffix = this._config?.device as string | undefined;
    const known = !!suffix && !!this.hass && this._devices.some((d) => d.suffix === suffix);
    return [1, 2, 3, 4].map((n) => ({
      value: String(n),
      label: known ? `Bank ${n} · ${bankName(readBank(this.hass!, suffix!, n))}` : `Bank ${n}`,
    }));
  }

  _schema(data: FormData): FormSchema[] {
    const devices = this._devices;
    const deviceOptions = devices.map((d) => ({ value: d.suffix, label: d.name === d.suffix ? d.suffix : `${d.name} (${d.suffix})` }));
    const current = data.device as string | undefined;
    if (current && !devices.some((d) => d.suffix === current)) deviceOptions.push({ value: current, label: `${current} (not found)` });
    const schema: FormSchema[] = [{ name: 'device', required: true, selector: { select: { mode: 'dropdown', options: deviceOptions } } }];
    const title = [boolean('show_title'), { name: 'name', disabled: data.show_title === false, selector: { text: {} } }, boolean('show_active_bank')];
    const bankLooks = [boolean('show_edit'), boolean('show_bank_options')];
    const timer = section('Timer', mdiTimerOutline, [
      {
        name: 'timer_presets',
        selector: {
          select: { multiple: true, custom_value: true, options: PRESET_SUGGESTIONS.map((m) => ({ value: String(m), label: `${m} min` })) },
        },
      },
      boolean('show_silent_timer'),
      { name: 'timer_silent_entity', selector: { entity: { domain: 'switch' } } },
    ]);

    if (this.kind === 'device') {
      const listed = data.banks_mode === 'all' || data.banks_mode === 'choose';
      const banks = section(
        'Banks',
        mdiKnob,
        [
          radios('banks_mode', [
            { value: 'all', label: 'All four' },
            { value: 'choose', label: 'Choose banks' },
            { value: 'active', label: 'Only the active bank (follows the dial)' },
            { value: 'timer', label: 'Only the timer bank' },
          ]),
          ...(data.banks_mode === 'choose' ? [checklist('banks_chosen', this._bankOptions())] : []),
          ...(listed
            ? [boolean('hide_unassigned'), radios('bank_columns', [{ value: '1', label: 'One' }, { value: '2', label: 'Two' }])]
            : []),
          ...bankLooks,
        ],
        true,
      );
      const settings = section('Settings', mdiCogOutline, [
        boolean('show_settings'),
        ...(data.show_settings !== false
          ? [
              checklist('settings_rows', rowOptions()),
              boolean('settings_headings'),
              boolean('settings_background'),
              radios('settings_position', [
                { value: 'beside', label: 'Beside the banks when there’s room' },
                { value: 'below', label: 'Below the banks' },
              ]),
            ]
          : []),
      ]);
      schema.push(...title, banks, timer, settings);
    } else if (this.kind === 'bank') {
      schema.push(
        {
          name: 'bank',
          required: true,
          selector: {
            select: {
              mode: 'dropdown',
              options: [
                ...this._bankOptions(),
                { value: 'active', label: 'The active bank (follows the dial)' },
                { value: 'timer', label: 'The timer bank' },
              ],
            },
          },
        },
        ...bankLooks,
        timer,
      );
    } else if (this.kind === 'status') {
      schema.push(...title);
    } else {
      schema.push(checklist('rows', rowOptions()), boolean('headings'), boolean('background'));
    }
    return schema;
  }

  private _commit(data: FormData): void {
    const next = fromForm(this.kind, data, this._config);
    this._config = next;
    fire(this, 'config-changed', { config: next });
  }

  protected override render(): TemplateResult | typeof nothing {
    if (!this.hass || !this._config) return nothing;
    const empty = !this._devices.length
      ? html`<p class="hint">No Pivot devices found. Add one under Settings → Devices &amp; services → Pivot.</p>`
      : nothing;
    const data = toForm(this.kind, this._config);
    const schema = this._schema(data);
    if (this._haForm) {
      return html`${empty}<ha-form
          .hass=${this.hass}
          .data=${data}
          .schema=${schema}
          .computeLabel=${(s: FormSchema) => LABELS[s.name] ?? s.title ?? s.name}
          .computeHelper=${(s: FormSchema) => HELPERS[s.name]}
          @value-changed=${(e: CustomEvent<{ value: FormData }>) => {
            e.stopPropagation();
            this._commit(e.detail.value);
          }}
        ></ha-form>`;
    }
    return html`${empty}<div class="fallback">${schema.map((s) => this._renderFallback(s, data))}</div>`;
  }

  /** The same fields with plain controls, for when ha-form is unavailable. */
  private _renderFallback(item: FormSchema, data: FormData): TemplateResult {
    if (item.type === 'expandable') {
      return html`<fieldset>
        <legend>${item.title}</legend>
        ${(item.schema ?? []).map((s) => this._renderFallback(s, data))}
      </fieldset>`;
    }
    const set = (value: unknown) => this._commit({ ...data, [item.name]: value });
    const label = LABELS[item.name] ?? item.name;
    const helper = HELPERS[item.name] ? html`<span class="hint">${HELPERS[item.name]}</span>` : nothing;
    const selector = item.selector ?? {};
    if ('boolean' in selector) {
      return html`<label class="check"
        ><input type="checkbox" .checked=${data[item.name] !== false} @change=${(e: Event) => set((e.target as HTMLInputElement).checked)} />${label}</label
      >`;
    }
    if ('text' in selector || 'entity' in selector) {
      return html`<label
        >${label}<input
          type="text"
          .value=${(data[item.name] as string) ?? ''}
          ?disabled=${item.disabled}
          @change=${(e: Event) => set((e.target as HTMLInputElement).value)}
      /></label>`;
    }
    const select = selector.select as { multiple?: boolean; custom_value?: boolean; mode?: string; options: { value: string; label: string }[] };
    const value = data[item.name];
    if (select.multiple && select.custom_value) {
      return html`<label
        >${label}<input
          type="text"
          .value=${(Array.isArray(value) ? value : []).join(', ')}
          @change=${(e: Event) => set((e.target as HTMLInputElement).value.split(','))}
        />${helper}</label
      >`;
    }
    if (select.multiple) {
      const list = Array.isArray(value) ? (value as string[]) : [];
      return html`<div class="group">
        ${label}
        ${select.options.map(
          (o) => html`<label class="check"
            ><input
              type="checkbox"
              .checked=${list.includes(o.value)}
              @change=${(e: Event) => set((e.target as HTMLInputElement).checked ? [...list, o.value] : list.filter((v) => v !== o.value))}
            />${o.label}</label
          >`,
        )}
      </div>`;
    }
    return html`<label
      >${label}
      <select @change=${(e: Event) => set((e.target as HTMLSelectElement).value)}>
        ${item.name === 'device' && !value ? html`<option value="" selected>Choose…</option>` : nothing}
        ${select.options.map((o) => html`<option value=${o.value} ?selected=${o.value === String(value)}>${o.label}</option>`)}
      </select>
      ${helper}</label
    >`;
  }
}

defineElement('pivot-card-editor', PivotCardEditor);
