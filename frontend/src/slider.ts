// <pivot-slider>: the value bar. Draws like the my-slider-v2 seekbar the
// button-card templates used (a pill fill that runs `cap` px past the value,
// on a pill track), and handles mouse, touch and keyboard input.
//
// Events (bubbling, composed):
//   pivot-slide-start                 a drag or key press began
//   pivot-slide       { value }       value while dragging (every move)
//   pivot-slide-end   { value }       final value
//   pivot-slide-cancel                touch turned into a page scroll

import { LitElement, css, html, nothing, type PropertyValues } from 'lit';
import { fire } from './actions';

const HOLD_MS = 4000;
const TOUCH_SLOP = 4;

export class PivotSlider extends LitElement {
  static override properties = {
    value: { type: Number },
    color: {},
    trackColor: { attribute: 'track-color' },
    cap: { type: Number },
    disabled: { type: Boolean, reflect: true },
    hideFill: { type: Boolean, attribute: 'hide-fill' },
    zeroCap: { type: Boolean, attribute: 'zero-cap' },
    label: {},
    _shown: { state: true },
  };

  declare value: number;
  declare color: string;
  declare trackColor: string;
  declare cap: number;
  declare disabled: boolean;
  declare hideFill: boolean;
  /** Draw the cap even at 0, as the volume slider always did. */
  declare zeroCap: boolean;
  declare label: string;
  declare _shown: number | undefined;

  private _pointer?: number;
  private _startX = 0;
  private _moved = false;
  private _isTouch = false;
  private _holdTimer?: ReturnType<typeof setTimeout>;

  constructor() {
    super();
    this.value = 0;
    this.color = '#ffffff';
    this.trackColor = 'rgba(255,255,255,0.3)';
    this.cap = 15;
    this.disabled = false;
    this.hideFill = false;
    this.zeroCap = false;
    this.label = '';
    this._shown = undefined;
  }

  static override styles = css`
    :host {
      display: block;
      position: relative;
      height: 23px;
      touch-action: pan-y;
      -webkit-tap-highlight-color: transparent;
      outline: none;
      cursor: pointer;
    }
    :host([disabled]) {
      cursor: inherit;
    }
    :host(:focus-visible) .track {
      outline: 2px solid var(--primary-color, #03a9f4);
      outline-offset: 2px;
    }
    /* Inset 1px like the ha-card border around my-slider-v2, so bars land on the same pixels. */
    .track {
      position: absolute;
      left: 1px;
      right: 1px;
      top: 1px;
      height: 100%;
      border-radius: 99px;
      overflow: hidden;
    }
    .fill {
      position: absolute;
      left: 0;
      top: 0;
      bottom: 0;
      border-radius: 99px;
    }
  `;

  /** The value on screen: the drag position, then the last sent value until the state catches up. */
  get shownValue(): number {
    return this._shown ?? this.value;
  }

  protected override willUpdate(changed: PropertyValues): void {
    if (changed.has('value') && this._pointer === undefined && this._shown !== undefined) {
      if (Math.abs(this._shown - this.value) < 0.5) this._release();
    }
  }

  override disconnectedCallback(): void {
    super.disconnectedCallback();
    clearTimeout(this._holdTimer);
  }

  protected override render() {
    const v = Math.min(100, Math.max(0, this.shownValue));
    const fill = (v > 0 || this.zeroCap) && !this.hideFill;
    return html`<div class="track" style="background:${this.trackColor}">
      ${fill
        ? html`<div class="fill" style="background:${this.color};width:min(100%, calc(${v}% + ${this.cap}px))"></div>`
        : nothing}
    </div>`;
  }

  protected override firstUpdated(): void {
    this.setAttribute('role', 'slider');
    this.setAttribute('aria-valuemin', '0');
    this.setAttribute('aria-valuemax', '100');
    this.addEventListener('pointerdown', this._down);
    this.addEventListener('pointermove', this._move);
    this.addEventListener('pointerup', this._up);
    this.addEventListener('pointercancel', this._cancel);
    this.addEventListener('lostpointercapture', this._lost);
    this.addEventListener('keydown', this._key);
    this.addEventListener('click', (e) => e.stopPropagation());
  }

  protected override updated(): void {
    this.setAttribute('aria-valuenow', String(Math.round(this.shownValue)));
    if (this.label) this.setAttribute('aria-label', this.label);
    this.setAttribute('aria-disabled', String(this.disabled));
    this.tabIndex = this.disabled ? -1 : 0;
  }

  private _valueAt(clientX: number): number {
    const track = this.renderRoot.querySelector('.track') as HTMLElement | null;
    const rect = (track ?? this).getBoundingClientRect();
    const usable = Math.max(1, rect.width - this.cap);
    const v = ((clientX - rect.left - this.cap / 2) / usable) * 100;
    return Math.round(Math.min(100, Math.max(0, v)));
  }

  private _hold(value: number): void {
    this._shown = value;
    clearTimeout(this._holdTimer);
    this._holdTimer = setTimeout(() => this._release(), HOLD_MS);
  }

  private _release(): void {
    clearTimeout(this._holdTimer);
    this._shown = undefined;
  }

  private _down = (e: PointerEvent) => {
    if (this.disabled) {
      fire(this, 'pivot-slide-blocked');
      return;
    }
    if (e.pointerType === 'mouse' && e.button !== 0) return;
    e.stopPropagation();
    this._pointer = e.pointerId;
    this._startX = e.clientX;
    this._moved = false;
    this._isTouch = e.pointerType !== 'mouse';
    try {
      this.setPointerCapture(e.pointerId);
    } catch {
      /* capture is best effort */
    }
    fire(this, 'pivot-slide-start');
    if (!this._isTouch) {
      // A mouse press moves the bar at once (seekbar behaviour).
      this._moved = true;
      this._hold(this._valueAt(e.clientX));
      fire(this, 'pivot-slide', { value: this._shown });
    }
  };

  private _move = (e: PointerEvent) => {
    if (e.pointerId !== this._pointer) return;
    if (!this._moved && Math.abs(e.clientX - this._startX) < TOUCH_SLOP) return;
    this._moved = true;
    const v = this._valueAt(e.clientX);
    if (v === this._shown) return;
    this._hold(v);
    fire(this, 'pivot-slide', { value: v });
  };

  private _up = (e: PointerEvent) => {
    if (e.pointerId !== this._pointer) return;
    this._pointer = undefined;
    const v = this._valueAt(e.clientX);
    this._hold(v);
    fire(this, 'pivot-slide-end', { value: v });
  };

  private _cancel = (e: PointerEvent) => {
    if (e.pointerId !== this._pointer) return;
    this._pointer = undefined;
    // The browser took the touch for scrolling: undo, never send.
    this._release();
    fire(this, 'pivot-slide-cancel');
  };

  private _lost = (e: PointerEvent) => {
    if (e.pointerId === this._pointer) this._cancel(e);
  };

  private _key = (e: KeyboardEvent) => {
    if (this.disabled) return;
    const steps: Record<string, number> = { ArrowRight: 1, ArrowUp: 1, ArrowLeft: -1, ArrowDown: -1, PageUp: 10, PageDown: -10 };
    let v: number;
    if (e.key in steps) v = this.shownValue + steps[e.key];
    else if (e.key === 'Home') v = 0;
    else if (e.key === 'End') v = 100;
    else return;
    e.preventDefault();
    v = Math.round(Math.min(100, Math.max(0, v)));
    fire(this, 'pivot-slide-start');
    this._hold(v);
    fire(this, 'pivot-slide-end', { value: v });
  };
}

if (!customElements.get('pivot-slider')) customElements.define('pivot-slider', PivotSlider);
