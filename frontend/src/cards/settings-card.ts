// <pivot-settings-card>: Control Mode, device volume and the behaviour switches.
import { css, html, nothing, type TemplateResult } from 'lit';
import { callService, throttle, toggleEntity } from '../actions';
import { ALL_ROWS, BEHAVIOUR_ROWS, DEVICE_ROWS, TOGGLE_TEXT, UNSET_STATES, deviceIds, type SettingsRow, type ToggleKey } from '../const';
import { listPivotDevices } from '../discovery';
import '../slider';
import { tokens } from '../styles';
import type { HomeAssistant } from '../types';
import { PivotCardBase, type PivotCardConfig } from './base';

export interface SettingsCardConfig extends PivotCardConfig {
  rows?: SettingsRow[];
  headings?: boolean;
}

export class PivotSettingsCard extends PivotCardBase<SettingsCardConfig> {
  static override styles = [
    tokens,
    css`
      .wrap {
        display: flex;
        flex-direction: column;
        gap: 8px;
      }
      .heading {
        padding: 1px;
        font-size: 22px;
        font-weight: 400;
        line-height: normal;
      }
      .srow {
        display: block;
        height: 50px;
        border: 1px solid transparent;
      }
      .srow.dependent-off {
        opacity: 0.3;
        pointer-events: none;
      }
      .srow .stitle,
      .srow .sdesc {
        position: absolute;
        left: 0;
        right: 53px;
      }
      .srow .stitle {
        top: 5.3px;
      }
      .srow .sdesc {
        top: 25.3px;
        color: var(--pv-description);
      }
      .srow .toggle {
        position: absolute;
        right: 0;
        top: 8.5px;
      }
      .volume {
        height: 72px;
      }
      .volume pivot-slider {
        margin-top: 10px;
        height: 5px;
      }
      .volume.unavailable pivot-slider,
      .srow.unavailable {
        opacity: 0.5;
      }
    `,
  ];

  private _sendVolume = throttle((entityId: string, value: number) => this._setVolume(entityId, value), 200);
  private _lastVolume?: number;

  static getConfigElement(): HTMLElement {
    const el = document.createElement('pivot-card-editor') as HTMLElement & { kind: string };
    el.kind = 'settings';
    return el;
  }

  static getStubConfig(hass: HomeAssistant): Record<string, unknown> {
    return { device: listPivotDevices(hass)[0]?.suffix ?? '' };
  }

  protected override validate(config: SettingsCardConfig): void {
    if (config.rows !== undefined) {
      if (!Array.isArray(config.rows)) throw new Error('rows must be a list');
      const bad = config.rows.filter((r) => !ALL_ROWS.includes(r));
      if (bad.length) throw new Error(`Unknown rows: ${bad.join(', ')}. Use ${ALL_ROWS.join(', ')}.`);
    }
  }

  getCardSize(): number {
    return 6;
  }

  getGridOptions() {
    return { columns: 12, rows: 'auto', min_columns: 6 };
  }

  private get _rows(): SettingsRow[] {
    return this._config?.rows?.length ? this._config.rows : ALL_ROWS;
  }

  private _mediaPlayer(): string | undefined {
    const device = this.device;
    const id = device ? this.hass?.states[deviceIds(device.suffix).mediaPlayerText]?.state : undefined;
    return id && id.includes('.') && !UNSET_STATES.has(id) ? id : undefined;
  }

  protected watchedIds(): (string | undefined)[] {
    const device = this.device;
    if (!device) return [];
    const ids = deviceIds(device.suffix);
    return [
      ...(['control_mode', 'announcements', 'mute_announcements', 'show_control_value', 'dim_when_idle'] as ToggleKey[]).map(ids.toggle),
      ids.mediaPlayerText,
      this._mediaPlayer(),
    ];
  }

  protected override render() {
    const device = this.device;
    if (!this.hass || !this._config) return nothing;
    if (!device) return this.renderProblem();
    const rows = this._rows;
    const headings = this._config.headings !== false;
    const parts: TemplateResult[] = [];
    if (headings) {
      const deviceRows = rows.filter((r) => DEVICE_ROWS.includes(r));
      const behaviourRows = rows.filter((r) => BEHAVIOUR_ROWS.includes(r));
      if (deviceRows.length) parts.push(html`<div class="heading">Device</div>`, ...deviceRows.map((r) => this._row(r)));
      if (behaviourRows.length) parts.push(html`<div class="heading">Behaviour</div>`, ...behaviourRows.map((r) => this._row(r)));
    } else {
      parts.push(...rows.map((r) => this._row(r)));
    }
    return html`<div class="wrap pv-ready">${parts}</div>`;
  }

  private _row(row: SettingsRow): TemplateResult {
    return row === 'volume' ? this._volume() : this._toggle(row);
  }

  private _toggle(key: ToggleKey): TemplateResult {
    const ids = deviceIds(this.device!.suffix);
    const entityId = ids.toggle(key);
    const on = this.hass!.states[entityId]?.state === 'on';
    // Dimming only applies while the value is shown on the ring.
    const blocked = key === 'dim_when_idle' && this.hass!.states[ids.toggle('show_control_value')]?.state !== 'on';
    const state = this.hass!.states[entityId]?.state;
    const missing = state === undefined || state === 'unavailable';
    const text = TOGGLE_TEXT[key];
    const toggle = () => this.hass && toggleEntity(this, this.hass, entityId);
    return html`<div
      class="srow tap ${blocked ? 'dependent-off' : ''} ${missing ? 'disabled unavailable' : ''}"
      role="switch"
      tabindex=${blocked || missing ? -1 : 0}
      aria-checked=${on ? 'true' : 'false'}
      aria-label=${text.title}
      style="--ha-ripple-color:${on ? 'var(--pv-ripple-on)' : 'var(--pv-ripple-off)'}"
      @pointerdown=${(e: PointerEvent) => this.holdStart(e, entityId)}
      @pointerup=${this.holdEnd}
      @pointerleave=${this.holdEnd}
      @pointercancel=${this.holdEnd}
      @contextmenu=${(e: Event) => e.preventDefault()}
      @click=${(e: Event) => this.tap(e, toggle)}
      @keydown=${(e: KeyboardEvent) => this.keyActivate(e, toggle)}
    >
      <ha-ripple></ha-ripple>
      <span class="stitle text">${text.title}</span>
      <span class="sdesc text">${text.description}</span>
      <span class="toggle ${on ? 'on' : ''}"><span class="knob"></span></span>
    </div>`;
  }

  private _volume(): TemplateResult {
    const player = this._mediaPlayer();
    const state = player ? this.hass!.states[player] : undefined;
    const usable = !!state && !UNSET_STATES.has(state.state);
    const level = Number(state?.attributes.volume_level);
    const value = Number.isFinite(level) ? level * 100 : 0;
    return html`<div class="volume ${usable ? '' : 'unavailable'}" title=${usable ? '' : 'The device media player is unavailable'}>
      <div class="text">Pivot Device Volume</div>
      <pivot-slider
        zero-cap
        .value=${value}
        .color=${'var(--pv-volume-fill)'}
        .trackColor=${'var(--pv-volume-track)'}
        .cap=${15}
        .label=${'Pivot device volume'}
        ?disabled=${!usable}
        @pivot-slide-start=${() => (this._lastVolume = undefined)}
        @pivot-slide=${(e: CustomEvent<{ value: number }>) => player && this._sendVolume(player, e.detail.value)}
        @pivot-slide-end=${(e: CustomEvent<{ value: number }>) => {
          this._sendVolume.cancel();
          if (player) this._setVolume(player, e.detail.value);
        }}
        @pivot-slide-cancel=${() => this._sendVolume.cancel()}
      ></pivot-slider>
    </div>`;
  }

  private _setVolume(entityId: string, value: number): void {
    if (!this.hass || value === this._lastVolume) return;
    this._lastVolume = value;
    callService(this, this.hass, 'media_player', 'volume_set', { entity_id: entityId, volume_level: Math.round(value) / 100 });
  }

  override disconnectedCallback(): void {
    super.disconnectedCallback();
    this._sendVolume.cancel();
  }
}

if (!customElements.get('pivot-settings-card')) customElements.define('pivot-settings-card', PivotSettingsCard);
