// <pivot-device-card>: the whole Pivot dashboard for one device. Title and
// status on top, banks on the left, settings on the right, collapsing to one
// column where a sections view would.
import { css, html, nothing } from 'lit';
import { listPivotDevices } from '../discovery';
import { tokens } from '../styles';
import type { HomeAssistant } from '../types';
import { PivotCardBase, type PivotCardConfig } from './base';
import type { BankCardConfig } from './bank-card';
import type { SettingsCardConfig } from './settings-card';
import type { StatusCardConfig } from './status-card';
import './bank-card';
import './settings-card';
import './status-card';

export interface DeviceCardConfig extends PivotCardConfig {
  name?: string;
  show_status?: boolean;
  show_settings?: boolean;
  timer_silent_entity?: string;
}

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
    `,
  ];

  private _children?: { status: StatusCardConfig; banks: BankCardConfig[]; settings: SettingsCardConfig };

  static getConfigElement(): HTMLElement {
    const el = document.createElement('pivot-card-editor') as HTMLElement & { kind: string };
    el.kind = 'device';
    return el;
  }

  static getStubConfig(hass: HomeAssistant): Record<string, unknown> {
    return { device: listPivotDevices(hass)[0]?.suffix ?? '' };
  }

  override setConfig(config: DeviceCardConfig): void {
    super.setConfig(config);
    const device = config.device;
    this._children = {
      status: { type: 'custom:pivot-status-card', device, ...(config.name !== undefined ? { name: config.name } : {}) },
      banks: [1, 2, 3, 4].map((bank) => ({
        type: 'custom:pivot-bank-card',
        device,
        bank,
        ...(config.timer_silent_entity ? { timer_silent_entity: config.timer_silent_entity } : {}),
      })),
      settings: { type: 'custom:pivot-settings-card', device },
    };
  }

  getCardSize(): number {
    return 20;
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
    const showSettings = this._config.show_settings !== false;
    return html`
      ${this._config.show_status === false ? nothing : html`<pivot-status-card .hass=${this.hass} .config=${c.status}></pivot-status-card>`}
      <div class="cols pv-ready ${showSettings ? '' : 'single'}">
        <div class="col banks">${c.banks.map((b) => html`<pivot-bank-card .hass=${this.hass} .config=${b}></pivot-bank-card>`)}</div>
        ${showSettings ? html`<div class="col settings"><pivot-settings-card .hass=${this.hass} .config=${c.settings}></pivot-settings-card></div>` : nothing}
      </div>
    `;
  }

  /** Hand every hass update down; the children decide whether to re-render. */
  protected override shouldUpdate(): boolean {
    return true;
  }
}

if (!customElements.get('pivot-device-card')) customElements.define('pivot-device-card', PivotDeviceCard);
