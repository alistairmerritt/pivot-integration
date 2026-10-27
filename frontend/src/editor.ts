// <pivot-card-editor>: the visual editor for all four cards. Uses Home
// Assistant's ha-form; if that cannot be loaded, falls back to plain controls.
import { LitElement, css, html, nothing, type TemplateResult } from 'lit';
import { fire } from './actions';
import { ALL_ROWS, TOGGLE_TEXT, type SettingsRow } from './const';
import { listPivotDevices } from './discovery';
import type { HomeAssistant, LovelaceCardConfig } from './types';

export type EditorKind = 'device' | 'bank' | 'status' | 'settings';

const ROW_LABELS: Record<SettingsRow, string> = {
  control_mode: TOGGLE_TEXT.control_mode.title,
  volume: 'Pivot Device Volume',
  announcements: TOGGLE_TEXT.announcements.title,
  mute_announcements: TOGGLE_TEXT.mute_announcements.title,
  show_control_value: TOGGLE_TEXT.show_control_value.title,
  dim_when_idle: TOGGLE_TEXT.dim_when_idle.title,
};

const LABELS: Record<string, string> = {
  device: 'Pivot device',
  bank: 'Bank',
  name: 'Title (optional)',
  show_status: 'Show title and active bank',
  show_settings: 'Show device and behaviour settings',
  show_name: 'Show title',
  rows: 'Rows',
  headings: 'Show "Device" and "Behaviour" headings',
  timer_silent_entity: 'Timer silent switch (optional, found automatically)',
};

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

  private _schema() {
    const devices = this._devices;
    const deviceOptions = devices.map((d) => ({ value: d.suffix, label: d.name === d.suffix ? d.suffix : `${d.name} (${d.suffix})` }));
    const current = this._config?.device as string | undefined;
    if (current && !devices.some((d) => d.suffix === current)) deviceOptions.push({ value: current, label: `${current} (not found)` });
    const schema: Record<string, unknown>[] = [
      { name: 'device', required: true, selector: { select: { mode: 'dropdown', options: deviceOptions } } },
    ];
    if (this.kind === 'bank') {
      schema.push({ name: 'bank', required: true, selector: { select: { mode: 'dropdown', options: ['1', '2', '3', '4'].map((v) => ({ value: v, label: `Bank ${v}` })) } } });
    }
    if (this.kind === 'device' || this.kind === 'status') schema.push({ name: 'name', selector: { text: {} } });
    if (this.kind === 'device') {
      schema.push({ name: 'show_status', selector: { boolean: {} } }, { name: 'show_settings', selector: { boolean: {} } });
    }
    if (this.kind === 'status') schema.push({ name: 'show_name', selector: { boolean: {} } });
    if (this.kind === 'settings') {
      schema.push(
        { name: 'rows', selector: { select: { multiple: true, mode: 'list', options: ALL_ROWS.map((r) => ({ value: r, label: ROW_LABELS[r] })) } } },
        { name: 'headings', selector: { boolean: {} } },
      );
    }
    if (this.kind === 'device' || this.kind === 'bank') {
      schema.push({ name: 'timer_silent_entity', selector: { entity: { domain: 'switch' } } });
    }
    return schema;
  }

  /** Form data: the config with defaults made explicit for the toggles. */
  private _data(): Record<string, unknown> {
    const c = this._config ?? { type: '' };
    return {
      ...c,
      bank: c.bank !== undefined ? String(c.bank) : '1',
      show_status: c.show_status !== false,
      show_settings: c.show_settings !== false,
      show_name: c.show_name !== false,
      headings: c.headings !== false,
      rows: Array.isArray(c.rows) && c.rows.length ? c.rows : [...ALL_ROWS],
    };
  }

  /** Writes back a tidy config: defaults and empty optional fields are left out. */
  private _commit(data: Record<string, unknown>): void {
    const next: LovelaceCardConfig = { type: this._config?.type ?? `custom:pivot-${this.kind}-card`, device: data.device ?? '' };
    if (this.kind === 'bank') next.bank = Number(data.bank ?? 1);
    if ((this.kind === 'device' || this.kind === 'status') && typeof data.name === 'string' && data.name.trim()) next.name = data.name;
    if (this.kind === 'device') {
      if (data.show_status === false) next.show_status = false;
      if (data.show_settings === false) next.show_settings = false;
    }
    if (this.kind === 'status' && data.show_name === false) next.show_name = false;
    if (this.kind === 'settings') {
      const rows = (Array.isArray(data.rows) ? data.rows : []) as SettingsRow[];
      const ordered = ALL_ROWS.filter((r) => rows.includes(r));
      if (ordered.length && ordered.length !== ALL_ROWS.length) next.rows = ordered;
      if (data.headings === false) next.headings = false;
    }
    if ((this.kind === 'device' || this.kind === 'bank') && typeof data.timer_silent_entity === 'string' && data.timer_silent_entity) {
      next.timer_silent_entity = data.timer_silent_entity;
    }
    // Keep anything this editor does not manage (grid_options, visibility, ...).
    for (const [key, value] of Object.entries(this._config ?? {})) {
      if (!(key in next) && !['device', 'bank', 'name', 'show_status', 'show_settings', 'show_name', 'rows', 'headings', 'timer_silent_entity'].includes(key)) {
        next[key] = value;
      }
    }
    this._config = next;
    fire(this, 'config-changed', { config: next });
  }

  protected override render(): TemplateResult | typeof nothing {
    if (!this.hass || !this._config) return nothing;
    const empty = !this._devices.length
      ? html`<p class="hint">No Pivot devices found. Add one under Settings → Devices &amp; services → Pivot.</p>`
      : nothing;
    if (this._haForm) {
      return html`${empty}<ha-form
          .hass=${this.hass}
          .data=${this._data()}
          .schema=${this._schema()}
          .computeLabel=${(s: { name: string }) => LABELS[s.name] ?? s.name}
          @value-changed=${(e: CustomEvent<{ value: Record<string, unknown> }>) => {
            e.stopPropagation();
            this._commit(e.detail.value);
          }}
        ></ha-form>`;
    }
    return html`${empty}${this._renderFallback()}`;
  }

  private _renderFallback(): TemplateResult {
    const data = this._data();
    const set = (key: string, value: unknown) => this._commit({ ...data, [key]: value });
    const check = (key: string) =>
      html`<label class="check"
        ><input type="checkbox" .checked=${data[key] !== false} @change=${(e: Event) => set(key, (e.target as HTMLInputElement).checked)} />${LABELS[key]}</label
      >`;
    return html`<div class="fallback">
      <label
        >${LABELS.device}
        <select @change=${(e: Event) => set('device', (e.target as HTMLSelectElement).value)}>
          <option value="" ?selected=${!data.device}>Choose…</option>
          ${this._devices.map((d) => html`<option value=${d.suffix} ?selected=${d.suffix === data.device}>${d.name} (${d.suffix})</option>`)}
        </select></label
      >
      ${this.kind === 'bank'
        ? html`<label
            >${LABELS.bank}
            <select @change=${(e: Event) => set('bank', (e.target as HTMLSelectElement).value)}>
              ${['1', '2', '3', '4'].map((v) => html`<option value=${v} ?selected=${v === data.bank}>Bank ${v}</option>`)}
            </select></label
          >`
        : nothing}
      ${this.kind === 'device' || this.kind === 'status'
        ? html`<label
            >${LABELS.name}<input type="text" .value=${(data.name as string) ?? ''} @change=${(e: Event) => set('name', (e.target as HTMLInputElement).value)}
          /></label>`
        : nothing}
      ${this.kind === 'device' ? html`${check('show_status')}${check('show_settings')}` : nothing}
      ${this.kind === 'status' ? check('show_name') : nothing}
      ${this.kind === 'settings' ? check('headings') : nothing}
    </div>`;
  }
}

if (!customElements.get('pivot-card-editor')) customElements.define('pivot-card-editor', PivotCardEditor);
