// What every Pivot card shares: finding its device, re-rendering only when an
// entity it shows changes, the theme check, and press-and-hold for more-info.
import { LitElement, html, type PropertyValues, type TemplateResult } from 'lit';
import { haptic, moreInfo } from '../actions';
import { DOCS_URL } from '../const';
import { findPivotDevice, listPivotDevices, type PivotDevice } from '../discovery';
import type { HomeAssistant, LovelaceCardConfig } from '../types';

export interface PivotCardConfig extends LovelaceCardConfig {
  device?: string;
}

const HOLD_MS = 500;

function luminance(color: string): number | undefined {
  const c = color.trim().toLowerCase();
  let rgb: number[] | undefined;
  const hex = /^#([0-9a-f]{3}|[0-9a-f]{6})$/.exec(c);
  if (hex) {
    const h = hex[1].length === 3 ? [...hex[1]].map((x) => x + x).join('') : hex[1];
    rgb = [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16));
  } else {
    const m = /^rgba?\(([^)]+)\)$/.exec(c);
    if (m) rgb = m[1].split(/[ ,/]+/).slice(0, 3).map(Number);
    else if (c === 'white') rgb = [255, 255, 255];
    else if (c === 'black') rgb = [0, 0, 0];
  }
  if (!rgb || rgb.some((v) => !Number.isFinite(v))) return undefined;
  return (0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]) / 255;
}

export abstract class PivotCardBase<C extends PivotCardConfig> extends LitElement {
  static override properties = {
    hass: { attribute: false },
    _config: { state: true },
  };

  declare hass?: HomeAssistant;
  declare _config?: C;

  private _deviceKey?: unknown[];
  private _deviceCache?: PivotDevice;
  private _holdTimer?: ReturnType<typeof setTimeout>;
  private _held = false;
  private _themeChecked?: unknown;

  /** Throws for configs Home Assistant should reject outright. */
  protected validate(_config: C): void {}

  setConfig(config: C): void {
    if (!config || typeof config !== 'object') throw new Error('Invalid configuration');
    this.validate(config);
    this._config = config;
  }

  /** Lets a parent card hand a config down as a property. */
  set config(config: C) {
    this.setConfig(config);
  }

  get device(): PivotDevice | undefined {
    const key = [this.hass?.entities, this.hass?.devices, this._config?.device, this.hass?.states];
    const same = this._deviceKey && key.slice(0, 3).every((k, i) => k === this._deviceKey![i]);
    // A device found through the registry stays valid until the registry changes.
    if (same && this._deviceCache?.deviceId) return this._deviceCache;
    this._deviceKey = key;
    this._deviceCache = findPivotDevice(this.hass, this._config?.device);
    return this._deviceCache;
  }

  /** Entity IDs whose state this card renders. */
  protected abstract watchedIds(): (string | undefined)[];

  protected override shouldUpdate(changed: PropertyValues): boolean {
    if (!changed.has('hass') || changed.size > 1) return true;
    const old = changed.get('hass') as HomeAssistant | undefined;
    const hass = this.hass;
    if (!old || !hass) return true;
    if (old.entities !== hass.entities || old.devices !== hass.devices || old.services !== hass.services || old.themes !== hass.themes) {
      return true;
    }
    return this.watchedIds().some((id) => id && old.states[id] !== hass.states[id]);
  }

  protected override updated(changed: PropertyValues): void {
    super.updated(changed);
    if (this.hass && this._themeChecked !== this.hass.themes) {
      this._themeChecked = this.hass.themes;
      this._checkTheme();
    }
  }

  private _checkTheme(): void {
    const style = getComputedStyle(this);
    const bg =
      style.getPropertyValue('--ha-card-background').trim() ||
      style.getPropertyValue('--card-background-color').trim() ||
      style.getPropertyValue('--primary-background-color').trim();
    const lum = bg ? luminance(bg) : undefined;
    const light = lum !== undefined && lum > 0.55;
    if (light !== this.hasAttribute('light')) {
      this.toggleAttribute('light', light);
      this.requestUpdate();
    }
  }

  /** The message shown instead of a card when it cannot find its device. */
  protected renderProblem(): TemplateResult {
    const devices = listPivotDevices(this.hass);
    const wanted = this._config?.device;
    const text = !devices.length
      ? 'No Pivot devices found. Add one under Settings → Devices & services → Pivot.'
      : wanted
        ? `No Pivot device “${wanted}”. Choose one in the card editor.`
        : 'Choose a Pivot device in the card editor.';
    return html`<ha-card class="pv-problem pv-error" style="display:block;padding:16px;font-size:14px;line-height:1.4">
      ${text} <a href=${DOCS_URL} target="_blank" rel="noreferrer" style="color:var(--primary-color)">Pivot dashboard docs</a>
    </ha-card>`;
  }

  // Press and hold opens more-info; a plain tap runs the action.
  protected holdStart(e: PointerEvent, entityId: string | undefined): void {
    if (e.pointerType === 'mouse' && e.button !== 0) return;
    this._held = false;
    clearTimeout(this._holdTimer);
    if (!entityId) return;
    this._holdTimer = setTimeout(() => {
      this._held = true;
      haptic(this);
      moreInfo(this, entityId);
    }, HOLD_MS);
  }

  protected holdEnd(): void {
    clearTimeout(this._holdTimer);
  }

  /** Wraps a tap handler so it is skipped after a hold. */
  protected tap(e: Event, action: () => void): void {
    e.stopPropagation();
    if (this._held) {
      this._held = false;
      return;
    }
    haptic(this);
    action();
  }

  protected keyActivate(e: KeyboardEvent, action: () => void): void {
    if (e.key !== 'Enter' && e.key !== ' ') return;
    e.preventDefault();
    e.stopPropagation();
    action();
  }

  override disconnectedCallback(): void {
    super.disconnectedCallback();
    clearTimeout(this._holdTimer);
  }
}
