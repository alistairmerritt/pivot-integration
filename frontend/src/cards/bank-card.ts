// <pivot-bank-card>: one Pivot bank, drawn like the pivot_banks button-card template.
import { css, html, nothing, type PropertyValues, type TemplateResult } from 'lit';
import { callService, hasService, haptic, moreInfo, throttle, toggleEntity } from '../actions';
import { NUM_BANKS, TIMER_DOCS_URL, TIMER_PRESETS, deviceIds } from '../const';
import { ICONS, icon } from '../icons';
import {
  bankName,
  fillHidden,
  isLive,
  legibleOnLight,
  minutesFromValue,
  readBank,
  readTimer,
  selectedPreset,
  showAnnounce,
  showMirror,
  showSlider,
  timerBarValue,
  valueFromMinutes,
  valueLabel,
  type BankView,
  type TimerView,
} from '../logic';
import { listPivotDevices } from '../discovery';
import '../slider';
import { tokens } from '../styles';
import type { HomeAssistant } from '../types';
import { PivotCardBase, type PivotCardConfig } from './base';

export interface BankCardConfig extends PivotCardConfig {
  bank?: number;
  timer_silent_entity?: string;
}

const SEND_EVERY_MS = 200;
/** How long a value waits for its bank to become active before it is dropped. */
const ACTIVATE_WAIT_MS = 4000;
/** The Timer Control blueprint ignores a start within 3 s of a dismiss. */
const REPEAT_COOLDOWN_MS = 3300;
const REPEAT_GIVE_UP_MS = 15000;

export class PivotBankCard extends PivotCardBase<BankCardConfig> {
  static override styles = [
    tokens,
    css`
      ha-card.bank {
        position: relative;
        display: block;
        padding: 15px;
        border-radius: var(--pivot-card-radius, 20px);
        border: 1px solid transparent;
        box-shadow: none;
        text-align: left;
        overflow: hidden;
        cursor: pointer;
        background: var(--ha-card-background, var(--card-background-color, #1c1c1e));
        color: var(--pv-text);
      }
      ha-card.bank.active {
        border-color: var(--pv-active-border);
      }
      ha-card.bank.control-off {
        opacity: 0.4;
      }
      .head {
        display: flex;
        align-items: center;
        height: 30px;
        margin-top: -5px;
        border-radius: 10px;
      }
      .dot {
        display: flex;
        flex: none;
        align-items: center;
        justify-content: center;
        width: 20px;
        height: 20px;
        border-radius: 20px;
      }
      .dot svg {
        width: 15px;
        height: 15px;
      }
      .head .label {
        margin-left: 10px;
      }
      .edit {
        display: flex;
        flex: none;
        align-items: center;
        justify-content: flex-end;
        gap: 6.8px;
        width: 90px;
        height: 25px;
        margin-left: auto;
        color: var(--pv-muted);
        font-size: 10px;
        letter-spacing: 0.05em;
        line-height: normal;
        white-space: nowrap;
      }
      .edit svg {
        flex: none;
        width: 15px;
        height: 15px;
        margin-right: -0.3px;
      }
      .name-row {
        display: flex;
        align-items: center;
        gap: 4px;
        height: 40px;
        margin-top: 5px;
        border-radius: 10px;
      }
      .name,
      .value {
        font-size: 25px;
        font-weight: 400;
        line-height: normal;
        white-space: nowrap;
      }
      .name {
        flex: 1 1 auto;
        min-width: 0;
        overflow: hidden;
        text-overflow: ellipsis;
      }
      .value {
        flex: none;
        color: var(--pv-muted);
        font-family: var(--pv-value-font);
      }
      pivot-slider {
        margin-top: 10px;
        height: 23px;
      }
      .row {
        display: block;
        width: 100%;
        height: 50px;
        margin: 10px 0 -15px;
        border-radius: 10px;
      }
      .row.silent {
        margin-top: 5px;
      }
      .row.muted {
        opacity: 0.4;
        pointer-events: none;
      }
      .row.unavailable {
        opacity: 0.5;
      }
      .row .row-icon {
        position: absolute;
        left: 0;
        top: 10.5px;
        width: 20px;
        height: 20px;
        color: var(--pv-muted);
      }
      .row .row-label {
        position: absolute;
        left: 30px;
        right: 53px;
        top: 0;
        height: 39px;
        display: flex;
        align-items: center;
      }
      .row .toggle {
        position: absolute;
        right: 0;
        top: 8px;
      }
      .strip {
        position: relative;
        display: grid;
        grid-template-columns: 15% 15% repeat(4, minmax(0, 1fr));
        column-gap: 5px;
        height: 50px;
        margin-top: 20px;
        padding: 5px;
        border-radius: 10px;
        background: var(--pv-strip);
        cursor: default;
      }
      .strip.alerting {
        grid-template-columns: 1fr 1fr;
      }
      .tbtn {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
        height: 40px;
        min-width: 0;
        border-radius: 10px;
        cursor: pointer;
      }
      .tbtn.solid {
        background: var(--pv-button);
      }
      .tbtn.idle {
        background: var(--pv-button-idle);
      }
      .tbtn .ticon {
        width: 40%;
        max-width: 34px;
        aspect-ratio: 1;
      }
      .tbtn.idle .ticon {
        color: var(--pv-dimmed-icon);
      }
      .tbtn.word {
        font-size: 14px;
        line-height: normal;
      }
      .tbtn.word svg {
        width: 20px;
        height: 20px;
        flex: none;
      }
      .tbtn.word.solid {
        color: #ffffff;
      }
      .preset {
        font-size: 15px;
        line-height: normal;
        color: var(--pv-preset);
      }
      .preset.selected {
        background: var(--pv-button);
        color: var(--pv-preset-selected);
      }
      .preset.locked {
        color: var(--pv-dimmed-icon);
        pointer-events: none;
      }
      .notice {
        margin-top: 20px;
        font-size: 14px;
        line-height: 1.35;
        color: var(--pv-description);
        white-space: normal;
        cursor: default;
      }
      .notice a {
        color: inherit;
      }
    `,
  ];

  private _send = throttle((value: number) => this._writeValue(value), SEND_EVERY_MS);
  private _pending?: { value: number; until: number };
  /** The last value this drag sent, so the release does not repeat it. */
  private _lastSent?: number;
  private _ticker?: ReturnType<typeof setTimeout>;
  private _repeatUntil?: number;
  private _repeatTimer?: ReturnType<typeof setTimeout>;

  static getConfigElement(): HTMLElement {
    const el = document.createElement('pivot-card-editor') as HTMLElement & { kind: string };
    el.kind = 'bank';
    return el;
  }

  static getStubConfig(hass: HomeAssistant): Record<string, unknown> {
    return { device: listPivotDevices(hass)[0]?.suffix ?? '', bank: 1 };
  }

  protected override validate(config: BankCardConfig): void {
    const bank = Number(config.bank ?? 1);
    if (!Number.isInteger(bank) || bank < 1 || bank > NUM_BANKS) throw new Error('bank must be 1, 2, 3 or 4');
  }

  get bankNumber(): number {
    return Number(this._config?.bank ?? 1);
  }

  getCardSize(): number {
    return 4;
  }

  getGridOptions() {
    return { columns: 12, rows: 'auto', min_columns: 6 };
  }

  private get _silentEntity(): string | undefined {
    return this._config?.timer_silent_entity || this.device?.timerSilentEntity;
  }

  protected watchedIds(): (string | undefined)[] {
    const device = this.device;
    if (!device || !this.hass) return [];
    const ids = deviceIds(device.suffix);
    const b = ids.bank(this.bankNumber);
    const bound = this.hass.states[b.entity]?.state;
    return [
      b.entity, b.value, b.passive, b.color, b.mirror, b.announce,
      ids.activeBank, ids.toggle('control_mode'), ids.toggle('mute_announcements'),
      ids.timerState, ids.timerDuration, ids.timerEnd,
      bound && bound.includes('.') ? bound : undefined,
      this._silentEntity, 'script.pivot_timer_toggle',
    ];
  }

  // ── Rendering ──────────────────────────────────────────────────────────

  protected override render() {
    const device = this.device;
    if (!this.hass || !this._config) return nothing;
    if (!device) return this.renderProblem();
    const bank = readBank(this.hass, device.suffix, this.bankNumber);
    if (this.hasAttribute('light')) bank.color = legibleOnLight(bank.color);
    const timer = readTimer(this.hass, device.suffix, Date.now());
    const label = valueLabel(bank, timer);
    const nameTip = bank.entityId && !bank.isTimer ? bank.entityId : '';

    return html`<ha-card
      class="bank pv-ready ${bank.active ? 'active' : ''} ${bank.controlOn ? '' : 'control-off'}"
      data-measure="bank-card"
      @click=${this._activate}
    >
      <ha-ripple></ha-ripple>
      <div class="head tap" @click=${this._activate}>
        <ha-ripple></ha-ripple>
        <button
          class="dot tap"
          style="color:${bank.color}"
          aria-label="Bank ${bank.n} colour"
          @click=${(e: Event) => this.tap(e, () => moreInfo(this, bank.ids.colorLight))}
        >
          <ha-ripple></ha-ripple>${icon(ICONS.circle)}
        </button>
        <span class="label text">${`Bank ${bank.n}`}</span>
        <button class="edit tap" aria-label="Edit the bank ${bank.n} entity" @click=${(e: Event) => this.tap(e, () => moreInfo(this, bank.ids.entity))}>
          <ha-ripple></ha-ripple><span>EDIT ENTITY</span>${icon(ICONS.pencil)}
        </button>
      </div>
      <div class="name-row tap" title=${nameTip} @click=${(e: Event) => this._nameTap(e, bank)}>
        <ha-ripple></ha-ripple>
        <span class="name">${bankName(bank)}</span>${label ? html`<span class="value">${label}</span>` : nothing}
      </div>
      ${showSlider(bank) ? this._renderSlider(bank, timer) : nothing}
      ${bank.isTimer ? this._renderTimer(bank, timer) : nothing}
      ${showMirror(bank) ? this._renderRow(bank.ids.mirror, 'Mirror Light Colour', ICONS.palette) : nothing}
      ${showAnnounce(bank) ? this._renderRow(bank.ids.announce, 'Announce Value', ICONS.volumeHigh, this._muted) : nothing}
    </ha-card>`;
  }

  private get _muted(): boolean {
    const device = this.device;
    return !!device && this.hass?.states[deviceIds(device.suffix).toggle('mute_announcements')]?.state === 'on';
  }

  private _renderSlider(bank: BankView, timer: TimerView): TemplateResult {
    const timerBusy = bank.isTimer && timer.state !== 'idle';
    const readOnly = !bank.controlOn || timerBusy || !isLive(bank) || (bank.isTimer && !timer.enabled && !bank.active);
    const value = bank.isTimer ? timerBarValue(timer, bank.value) : bank.value;
    return html`<pivot-slider
      .value=${value}
      .color=${bank.color}
      .trackColor=${`${bank.color}33`}
      .cap=${15}
      .hideFill=${fillHidden(bank)}
      .label=${`${bankName(bank)} value`}
      ?disabled=${readOnly}
      @pivot-slide-start=${() => this._slideStart(bank)}
      @pivot-slide=${(e: CustomEvent<{ value: number }>) => this._slide(bank, e.detail.value)}
      @pivot-slide-end=${(e: CustomEvent<{ value: number }>) => this._slideEnd(bank, timer, e.detail.value)}
      @pivot-slide-cancel=${() => this._send.cancel()}
      @click=${(e: Event) => e.stopPropagation()}
    ></pivot-slider>`;
  }

  private _renderRow(entityId: string, title: string, path: string, muted = false, extraClass = ''): TemplateResult {
    const on = this.hass?.states[entityId]?.state === 'on';
    const state = this.hass?.states[entityId]?.state;
    const missing = state === undefined || state === 'unavailable';
    return html`<div
      class="row tap ${extraClass} ${muted ? 'muted' : ''} ${missing ? 'disabled unavailable' : ''}"
      role="switch"
      tabindex=${muted || missing ? -1 : 0}
      aria-checked=${on ? 'true' : 'false'}
      aria-label=${title}
      style="--ha-ripple-color:${on ? 'var(--pv-ripple-on)' : 'var(--pv-ripple-off)'}"
      @pointerdown=${(e: PointerEvent) => this.holdStart(e, entityId)}
      @pointerup=${this.holdEnd}
      @pointerleave=${this.holdEnd}
      @pointercancel=${this.holdEnd}
      @contextmenu=${(e: Event) => e.preventDefault()}
      @click=${(e: Event) => this.tap(e, () => this.hass && toggleEntity(this, this.hass, entityId))}
      @keydown=${(e: KeyboardEvent) => this.keyActivate(e, () => this.hass && toggleEntity(this, this.hass, entityId))}
    >
      <ha-ripple></ha-ripple>
      <span class="row-icon">${icon(path)}</span>
      <span class="row-label text">${title}</span>
      <span class="toggle ${on ? 'on' : ''}"><span class="knob"></span></span>
    </div>`;
  }

  private _renderTimer(bank: BankView, timer: TimerView): TemplateResult {
    const silent = this._silentEntity;
    const silentRow = silent ? this._renderRow(silent, 'Silent Timer', ICONS.volumeMute, false, 'silent') : nothing;
    if (!timer.enabled) {
      return html`<div class="notice" @click=${(e: Event) => e.stopPropagation()}>
          Timer entities are disabled. Enable them in the Pivot device settings to use the timer.
          <a href=${TIMER_DOCS_URL} target="_blank" rel="noreferrer">Timer setup</a>
        </div>
        ${silentRow}`;
    }
    if (timer.state === 'alerting') {
      return html`<div class="strip alerting tap" @click=${(e: Event) => e.stopPropagation()}>
          <button class="tbtn word solid tap" @click=${(e: Event) => this.tap(e, () => this._timerToggle(bank))}>
            <ha-ripple></ha-ripple>${icon(ICONS.close)}<span>Stop</span>
          </button>
          <button class="tbtn word idle tap" @click=${(e: Event) => this.tap(e, () => this._repeat(bank))}>
            <ha-ripple></ha-ripple>${icon(ICONS.refresh)}<span>Repeat</span>
          </button>
          <ha-ripple></ha-ripple>
        </div>
        ${silentRow}`;
    }
    const running = timer.state === 'running';
    const paused = timer.state === 'paused';
    const busy = running || paused;
    const selected = selectedPreset(timer, bank.value);
    // The strip's ripple goes last so its hover tint sits over the buttons, as before.
    return html`<div class="strip tap" @click=${(e: Event) => e.stopPropagation()}>
        <button
          class="tbtn solid tap"
          aria-label=${running ? 'Pause timer' : paused ? 'Resume timer' : 'Start timer'}
          @click=${(e: Event) => this.tap(e, () => this._timerToggle(bank))}
        >
          <ha-ripple></ha-ripple><span class="ticon">${icon(running ? ICONS.pause : ICONS.play)}</span>
        </button>
        <button
          class="tbtn tap ${busy ? 'solid' : 'idle'}"
          aria-label="Cancel timer"
          ?disabled=${!busy}
          @click=${(e: Event) => this.tap(e, () => busy && this._timerCancel(bank))}
        >
          <ha-ripple></ha-ripple><span class="ticon">${icon(paused ? ICONS.refresh : ICONS.close)}</span>
        </button>
        ${TIMER_PRESETS.map(
          (p) => html`<button
            class="tbtn preset tap ${selected === p.minutes ? 'selected' : ''} ${busy ? 'locked' : ''}"
            aria-pressed=${selected === p.minutes ? 'true' : 'false'}
            @click=${(e: Event) => this.tap(e, () => this._preset(bank, timer, p))}
          >
            <ha-ripple></ha-ripple>${p.label}
          </button>`,
        )}
        <ha-ripple></ha-ripple>
      </div>
      ${silentRow}`;
  }

  // ── Behaviour ──────────────────────────────────────────────────────────

  private _activate = (e?: Event) => {
    e?.stopPropagation();
    const device = this.device;
    if (!this.hass || !device) return;
    const bank = readBank(this.hass, device.suffix, this.bankNumber);
    if (bank.active) return;
    haptic(this);
    callService(this, this.hass, 'number', 'set_value', { entity_id: deviceIds(device.suffix).activeBank, value: bank.n });
  };

  private _nameTap(e: Event, bank: BankView): void {
    if (bank.isTimer) return this._activate(e);
    e.stopPropagation();
    moreInfo(this, bank.entityId ?? bank.ids.entity);
  }

  private _slideStart(bank: BankView): void {
    this._lastSent = undefined;
    // Dragging an inactive bank makes it the active bank first; the integration
    // only applies values written to the active bank (bank_control.py).
    if (!bank.isTimer && !bank.active) this._activate();
  }

  private _slide(bank: BankView, value: number): void {
    // Timer bars write once, on release: each write is announced as a duration.
    if (!bank.isTimer) this._send(value);
  }

  private _slideEnd(bank: BankView, timer: TimerView, value: number): void {
    this._send.cancel();
    if (bank.isTimer) this._writeTimer(bank, timer, value);
    else this._writeValue(value);
  }

  private _writeValue(value: number): void {
    const device = this.device;
    if (!this.hass || !device) return;
    const bank = readBank(this.hass, device.suffix, this.bankNumber);
    if (bank.active) {
      this._pending = undefined;
      if (value === this._lastSent) return;
      this._lastSent = value;
      callService(this, this.hass, 'number', 'set_value', { entity_id: bank.ids.value, value });
    } else {
      this._pending = { value, until: Date.now() + ACTIVATE_WAIT_MS };
    }
  }

  private _writeTimer(bank: BankView, timer: TimerView, value: number): void {
    if (!this.hass || timer.state !== 'idle') return;
    const minutes = minutesFromValue(value);
    this._setDuration(bank, timer, minutes, valueFromMinutes(minutes));
  }

  private _preset(bank: BankView, timer: TimerView, preset: (typeof TIMER_PRESETS)[number]): void {
    if (timer.state !== 'idle') return;
    this._setDuration(bank, timer, preset.minutes, preset.value);
  }

  /**
   * On the active timer bank, write the bank value: the integration turns it
   * into a duration and the device announces it, exactly like the knob. On an
   * inactive bank the integration ignores bank values, so set the duration
   * directly and keep the gauge in step.
   */
  private _setDuration(bank: BankView, timer: TimerView, minutes: number, bankValue: number): void {
    const device = this.device;
    if (!this.hass || !device) return;
    const value = Math.round(bankValue);
    if (bank.active) {
      callService(this, this.hass, 'number', 'set_value', { entity_id: bank.ids.value, value });
      return;
    }
    if (timer.enabled) {
      callService(this, this.hass, 'number', 'set_value', { entity_id: deviceIds(device.suffix).timerDuration, value: minutes });
    }
    callService(this, this.hass, 'number', 'set_value', { entity_id: bank.ids.value, value });
  }

  private async _timerToggle(bank: BankView): Promise<boolean> {
    const device = this.device;
    if (!this.hass || !device) return false;
    if (hasService(this.hass, 'pivot', 'timer_toggle')) {
      return callService(this, this.hass, 'pivot', 'timer_toggle', { device: device.suffix, bank: bank.n });
    }
    // Pivot older than 0.0.93: the script made from the Timer Toggle blueprint.
    return callService(this, this.hass, 'script', 'turn_on', {
      entity_id: 'script.pivot_timer_toggle',
      variables: { device_suffix: device.suffix, bank: bank.n },
    });
  }

  private _timerCancel(bank: BankView): void {
    const device = this.device;
    if (!this.hass || !device) return;
    if (hasService(this.hass, 'pivot', 'timer_cancel')) {
      callService(this, this.hass, 'pivot', 'timer_cancel', { device: device.suffix, bank: bank.n });
      return;
    }
    callService(this, this.hass, 'select', 'select_option', { entity_id: deviceIds(device.suffix).timerState, option: 'idle' });
  }

  /** Dismiss, then start the same timer again once the blueprint allows it. */
  private async _repeat(bank: BankView): Promise<void> {
    if (!(await this._timerToggle(bank))) return;
    this._repeatUntil = Date.now() + REPEAT_GIVE_UP_MS;
    const poll = () => {
      const device = this.device;
      if (!this._repeatUntil || !this.hass || !device || Date.now() > this._repeatUntil) {
        this._repeatUntil = undefined;
        return;
      }
      const st = this.hass.states[deviceIds(device.suffix).timerState];
      if (st?.state === 'idle' && Date.now() - Date.parse(st.last_changed) > REPEAT_COOLDOWN_MS) {
        this._repeatUntil = undefined;
        this._timerToggle(bank);
        return;
      }
      this._repeatTimer = setTimeout(poll, 250);
    };
    this._repeatTimer = setTimeout(poll, 250);
  }

  protected override updated(changed: PropertyValues): void {
    super.updated(changed);
    const device = this.device;
    if (!this.hass || !device) return;
    const bank = readBank(this.hass, device.suffix, this.bankNumber);
    // A value dragged on an inactive bank goes out once the bank is active.
    if (this._pending) {
      if (Date.now() > this._pending.until) this._pending = undefined;
      else if (bank.active) this._writeValue(this._pending.value);
    }
    // While the timer runs, re-render exactly when the shown second changes,
    // so the countdown never lags or skips a number.
    clearTimeout(this._ticker);
    this._ticker = undefined;
    const ids = deviceIds(device.suffix);
    const end = Date.parse(this.hass.states[ids.timerEnd]?.state ?? '');
    if (bank.isTimer && this.hass.states[ids.timerState]?.state === 'running' && Number.isFinite(end)) {
      const left = end - Date.now();
      if (left > -1000) {
        // Math.round flips the label when the time left crosses a half second.
        const wait = ((((left - 500) % 1000) + 1000) % 1000) + 5;
        this._ticker = setTimeout(() => this.requestUpdate(), wait);
      }
    }
  }

  override connectedCallback(): void {
    super.connectedCallback();
    if (this.hasUpdated) this.requestUpdate();
  }

  override disconnectedCallback(): void {
    super.disconnectedCallback();
    clearTimeout(this._ticker);
    this._ticker = undefined;
    clearTimeout(this._repeatTimer);
    this._repeatUntil = undefined;
    this._send.cancel();
  }
}

if (!customElements.get('pivot-bank-card')) customElements.define('pivot-bank-card', PivotBankCard);
