// <pivot-device-card>: the whole Pivot dashboard for one device. Title and
// status on top, banks on the left, settings on the right, collapsing to one
// column where a sections view would. Options choose which banks show, trim
// the bank cards, and move or drop the settings.
import { css, html, nothing } from 'lit';
import { repeat } from 'lit/directives/repeat.js';
import { ALL_ROWS, NUM_BANKS, type BankChoice, type BanksOption, type SettingsRow } from '../const';
import { listPivotDevices } from '../discovery';
import { banksToShow, timerPresetsError } from '../logic';
import { tokens } from '../styles';
import type { HomeAssistant } from '../types';
import { PivotCardBase, type PivotCardConfig } from './base';
import type { BankCardConfig } from './bank-card';
import { defineElement } from '../register';
import type { SettingsCardConfig } from './settings-card';
import type { StatusCardConfig } from './status-card';
import './bank-card';
import './settings-card';
import './status-card';

export interface DeviceCardConfig extends PivotCardConfig {
  name?: string;
  show_title?: boolean;
  show_active_bank?: boolean;
  /** The 0.0.93 option: false hid the title and the active bank together. */
  show_status?: boolean;
  banks?: BanksOption;
  hide_unassigned?: boolean;
  bank_columns?: 1 | 2;
  show_edit?: boolean;
  show_bank_options?: boolean;
  timer_presets?: number[];
  show_silent_timer?: boolean;
  timer_silent_entity?: string;
  show_settings?: boolean;
  settings_rows?: SettingsRow[];
  settings_headings?: boolean;
  settings_background?: boolean;
  settings_position?: 'beside' | 'below';
}

type Children = {
  status: StatusCardConfig;
  banks: Record<string, BankCardConfig>;
  settings: SettingsCardConfig;
};

export class PivotDeviceCard extends PivotCardBase<DeviceCardConfig> {
  static override styles = [
    tokens,
    css`
      :host {
        container-type: inline-size;
      }
      .cols {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        column-gap: 32px;
        row-gap: 24px;
        align-items: start;
      }
      pivot-status-card + .cols {
        margin-top: 24px;
      }
      .cols.single {
        grid-template-columns: minmax(0, 1fr);
      }
      /* Each column used to be a layout-card: 4px padding plus 4px 4px 8px card
         margins, so cards sit 8px in (12px at the bottom)... */
      .col {
        display: flex;
        flex-direction: column;
        gap: 8px;
        padding: 8px 8px 12px;
        min-width: 0;
      }
      /* ...and on phones layout-card drops the side margins. */
      @media (max-width: 500px) {
        .col {
          padding-left: 4px;
          padding-right: 4px;
        }
      }
      /* Two 320px columns no longer fit: stack like a sections view. */
      @container (max-width: 671px) {
        .cols {
          grid-template-columns: minmax(0, 1fr);
        }
      }
      .col.banks {
        container: pivot-banks / inline-size;
      }
      .bank-list {
        display: flex;
        flex-direction: column;
        gap: 8px;
      }
      /* Two banks per row once each can be about 300px wide. */
      @container pivot-banks (min-width: 608px) {
        .bank-list.two {
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          align-items: start;
        }
      }
      .empty {
        padding: 4px 2px;
        font-size: 14px;
        line-height: 1.4;
        color: var(--pv-description);
      }
    `,
  ];

  private _children?: Children;

  static getConfigElement(): HTMLElement {
    const el = document.createElement('pivot-card-editor') as HTMLElement & { kind: string };
    el.kind = 'device';
    return el;
  }

  static getStubConfig(hass: HomeAssistant): Record<string, unknown> {
    return { device: listPivotDevices(hass)[0]?.suffix ?? '' };
  }

  protected override validate(config: DeviceCardConfig): void {
    const banks = config.banks;
    if (banks !== undefined && banks !== 'all' && banks !== 'active' && banks !== 'timer') {
      if (!Array.isArray(banks) || banks.some((n) => !Number.isInteger(n) || n < 1 || n > NUM_BANKS)) {
        throw new Error('banks must be all, active, timer or a list of bank numbers, like [1, 2]');
      }
    }
    if (config.bank_columns !== undefined && config.bank_columns !== 1 && config.bank_columns !== 2) {
      throw new Error('bank_columns must be 1 or 2');
    }
    if (config.settings_position !== undefined && config.settings_position !== 'beside' && config.settings_position !== 'below') {
      throw new Error('settings_position must be beside or below');
    }
    if (config.settings_rows !== undefined) {
      if (!Array.isArray(config.settings_rows)) throw new Error('settings_rows must be a list');
      const bad = config.settings_rows.filter((r) => !ALL_ROWS.includes(r));
      if (bad.length) throw new Error(`Unknown settings_rows: ${bad.join(', ')}. Use ${ALL_ROWS.join(', ')}.`);
    }
    const presets = timerPresetsError(config.timer_presets);
    if (presets) throw new Error(presets);
  }

  override setConfig(config: DeviceCardConfig): void {
    super.setConfig(config);
    const device = config.device;
    const legacyHidden = config.show_status === false;
    // The bank options every bank card gets, written only when set.
    const shared: Partial<BankCardConfig> = {};
    for (const key of ['show_edit', 'show_bank_options', 'timer_presets', 'show_silent_timer', 'timer_silent_entity'] as const) {
      if (config[key] !== undefined && config[key] !== '') (shared as Record<string, unknown>)[key] = config[key];
    }
    const bank = (choice: BankChoice): BankCardConfig => ({ type: 'custom:pivot-bank-card', device, bank: choice, ...shared });
    // Built once per config, so the child cards only re-render when their entities change.
    this._children = {
      status: {
        type: 'custom:pivot-status-card',
        device,
        ...(config.name !== undefined ? { name: config.name } : {}),
        show_title: !legacyHidden && config.show_title !== false,
        show_active_bank: !legacyHidden && config.show_active_bank !== false,
      },
      banks: { 1: bank(1), 2: bank(2), 3: bank(3), 4: bank(4), active: bank('active'), timer: bank('timer') },
      settings: {
        type: 'custom:pivot-settings-card',
        device,
        ...(config.settings_rows ? { rows: config.settings_rows } : {}),
        ...(config.settings_headings === false ? { headings: false } : {}),
        ...(config.settings_background ? { background: true } : {}),
      },
    };
  }

  private get _showStatus(): boolean {
    const s = this._children?.status;
    return !!s && (s.show_title !== false || s.show_active_bank !== false);
  }

  private get _showSettings(): boolean {
    return this._config?.show_settings !== false && (this._config?.settings_rows ?? ALL_ROWS).length > 0;
  }

  /** The bank cards to draw, in order. */
  private _bankConfigs(): BankCardConfig[] {
    const c = this._config;
    const device = this.device;
    if (!c || !device || !this.hass || !this._children) return [];
    const mode = c.banks ?? 'all';
    if (mode === 'active' || mode === 'timer') return [this._children.banks[mode]];
    return banksToShow(this.hass, device.suffix, mode, !!c.hide_unassigned).map((n) => this._children!.banks[n]);
  }

  getCardSize(): number {
    const banks = this._config?.banks;
    // The banks actually drawn when the device is known; otherwise the most there could be.
    const count = this.hass && this.device
      ? this._bankConfigs().length
      : banks === 'active' || banks === 'timer' ? 1 : Array.isArray(banks) ? new Set(banks).size : NUM_BANKS;
    const status = this._showStatus ? 2 : 0;
    if (!this._showSettings) return status + count * 4;
    const beside = this._config?.settings_position !== 'below';
    return status + (beside ? Math.max(count * 4, 7) : count * 4 + 7);
  }

  getGridOptions() {
    return { columns: 'full', rows: 'auto' };
  }

  // The child cards watch their own entities; this card only lays them out.
  protected watchedIds(): (string | undefined)[] {
    return [];
  }

  protected override render() {
    if (!this.hass || !this._config || !this._children) return nothing;
    if (!this.device) return this.renderProblem();
    const c = this._children;
    const banks = this._bankConfigs();
    const showSettings = this._showSettings;
    const stacked = !showSettings || this._config.settings_position === 'below';
    const twoPerRow = this._config.bank_columns === 2 && banks.length > 1;
    const chosenNone = Array.isArray(this._config.banks) && this._config.banks.length === 0;
    return html`
      ${this._showStatus ? html`<pivot-status-card .hass=${this.hass} .config=${c.status}></pivot-status-card>` : nothing}
      <div class="cols pv-ready ${stacked ? 'single' : ''}">
        <div class="col banks">
          <div class="bank-list ${twoPerRow ? 'two' : ''}">
            ${banks.length
              ? repeat(
                  banks,
                  (b) => String(b.bank),
                  (b) => html`<pivot-bank-card .hass=${this.hass} .config=${b}></pivot-bank-card>`,
                )
              : html`<div class="empty">
                  ${chosenNone ? 'No banks chosen. Pick some in the card editor.' : 'None of the banks has anything assigned yet.'}
                </div>`}
          </div>
        </div>
        ${showSettings
          ? html`<div class="col settings"><pivot-settings-card .hass=${this.hass} .config=${c.settings}></pivot-settings-card></div>`
          : nothing}
      </div>
    `;
  }

  /** Hand every hass update down; the children decide whether to re-render. */
  protected override shouldUpdate(): boolean {
    return true;
  }
}

defineElement('pivot-device-card', PivotDeviceCard);
