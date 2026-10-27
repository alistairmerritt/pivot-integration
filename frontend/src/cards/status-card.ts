// <pivot-status-card>: the device name and the "● Bank 1 - Desk Lamp" line.
import { css, html, nothing } from 'lit';
import { moreInfo } from '../actions';
import { deviceIds } from '../const';
import { listPivotDevices } from '../discovery';
import { ICONS, icon } from '../icons';
import { activeBankNumber, bankName, legibleOnLight, readBank } from '../logic';
import { tokens } from '../styles';
import type { HomeAssistant } from '../types';
import { PivotCardBase, type PivotCardConfig } from './base';
import { defineElement } from '../register';

export interface StatusCardConfig extends PivotCardConfig {
  name?: string;
  show_title?: boolean;
  /** The 0.0.93 name for show_title, still read. */
  show_name?: boolean;
  show_active_bank?: boolean;
}

export class PivotStatusCard extends PivotCardBase<StatusCardConfig> {
  static override styles = [
    tokens,
    css`
      .wrap {
        display: block;
      }
      .title {
        padding: 1px;
        font-size: 45px;
        font-weight: 500;
        line-height: normal;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
      .title + .status {
        margin-top: 16px;
      }
      .status {
        display: flex;
        align-items: center;
        height: 30px;
        max-width: 100%;
        width: max-content;
      }
      .sdot {
        display: flex;
        flex: none;
        align-items: center;
        justify-content: center;
        width: 20px;
        height: 20px;
      }
      .sdot svg {
        width: 15px;
        height: 15px;
      }
      .status .text {
        margin-left: 10px;
        color: var(--pv-status-text);
      }
    `,
  ];

  static getConfigElement(): HTMLElement {
    const el = document.createElement('pivot-card-editor') as HTMLElement & { kind: string };
    el.kind = 'status';
    return el;
  }

  static getStubConfig(hass: HomeAssistant): Record<string, unknown> {
    return { device: listPivotDevices(hass)[0]?.suffix ?? '' };
  }

  private get _showTitle(): boolean {
    return this._config?.show_title !== false && this._config?.show_name !== false;
  }

  private get _showActiveBank(): boolean {
    return this._config?.show_active_bank !== false;
  }

  getCardSize(): number {
    return (this._showTitle ? 1 : 0) + (this._showActiveBank ? 1 : 0);
  }

  getGridOptions() {
    return { columns: 'full', rows: 'auto' };
  }

  protected watchedIds(): (string | undefined)[] {
    const device = this.device;
    if (!device || !this.hass) return [];
    const ids = deviceIds(device.suffix);
    const n = activeBankNumber(this.hass, device.suffix);
    const bank = n !== undefined ? ids.bank(n) : undefined;
    const bound = bank ? this.hass.states[bank.entity]?.state : undefined;
    return [ids.activeBank, ids.toggle('control_mode'), bank?.entity, bank?.color, bound && bound.includes('.') ? bound : undefined];
  }

  protected override render() {
    const device = this.device;
    if (!this.hass || !this._config) return nothing;
    if (!device) return this.renderProblem();
    const ids = deviceIds(device.suffix);
    const controlOn = this.hass.states[ids.toggle('control_mode')]?.state === 'on';
    const n = activeBankNumber(this.hass, device.suffix);
    let text = 'Control mode off';
    let color = 'var(--pv-muted)';
    if (controlOn) {
      if (n !== undefined) {
        const bank = readBank(this.hass, device.suffix, n);
        text = `Bank ${n} - ${bankName(bank)}`;
        color = this.hasAttribute('light') ? legibleOnLight(bank.color) : bank.color;
      } else {
        text = 'Active bank unavailable';
      }
    }
    const title = this._config.name?.trim() || device.name;
    return html`<div class="wrap pv-ready">
      ${this._showTitle ? html`<div class="title">${title}</div>` : nothing}
      ${this._showActiveBank
        ? html`<div
            class="status tap"
            role="button"
            tabindex="0"
            @click=${(e: Event) => this.tap(e, () => moreInfo(this, ids.activeBank))}
            @keydown=${(e: KeyboardEvent) => this.keyActivate(e, () => moreInfo(this, ids.activeBank))}
          >
            <ha-ripple></ha-ripple>
            <span class="sdot" style="color:${color}">${icon(ICONS.circle)}</span>
            <span class="text">${text}</span>
          </div>`
        : nothing}
    </div>`;
  }
}

defineElement('pivot-status-card', PivotStatusCard);
