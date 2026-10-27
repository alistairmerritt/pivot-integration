// Shared styles. Measurements are the ones the button-card templates render
// (checked against the live dashboard), so the cards land on the same pixels.
import { css } from 'lit';

/**
 * Colour tokens. Override any --pivot-* variable from a theme.
 * Neutrals are white or black over the card, never solid greys, so they sit
 * right on see-through cards and background images. On a solid #1c1c1e card
 * they come out as the button-card templates' greys (#545454, #171717, ...).
 */
export const tokens = css`
  :host {
    --pv-text: var(--primary-text-color, #f2f2f7);
    --pv-muted: var(--pivot-muted-color, rgba(255, 255, 255, 0.25));
    --pv-description: var(--pivot-description-color, rgba(255, 255, 255, 0.5));
    --pv-status-text: var(--pivot-status-text-color, #ffffff);
    --pv-toggle-track: var(--pivot-toggle-track-color, rgba(0, 0, 0, 0.3));
    --pv-toggle-edge: var(--pivot-toggle-edge-color, rgba(255, 255, 255, 0.08));
    --pv-toggle-off: var(--pivot-toggle-off-color, rgba(255, 255, 255, 0.26));
    --pv-toggle-on: var(--pivot-toggle-on-color, #ffffff);
    --pv-strip: var(--pivot-timer-strip-color, rgba(0, 0, 0, 0.18));
    --pv-button: var(--pivot-button-color, rgba(255, 255, 255, 0.26));
    --pv-button-idle: var(--pivot-button-idle-color, rgba(255, 255, 255, 0.08));
    --pv-preset: var(--pivot-preset-color, rgba(255, 255, 255, 0.7));
    --pv-preset-selected: var(--pivot-preset-selected-color, #ffffff);
    --pv-dimmed-icon: var(--pivot-dimmed-icon-color, rgba(255, 255, 255, 0.3));
    --pv-active-border: var(--pivot-active-border-color, rgba(255, 255, 255, 0.27));
    --pv-volume-track: var(--pivot-volume-track-color, rgba(255, 255, 255, 0.3));
    --pv-volume-fill: var(--pivot-volume-fill-color, #ffffff);
    --pv-value-font: var(--pivot-value-font-family, 'SF Pro Rounded', ui-rounded, system-ui, sans-serif);
    --pv-ripple-on: var(--state-switch-active-color, var(--state-active-color, var(--amber-color, #ffc107)));
    --pv-ripple-off: var(--state-switch-inactive-color, var(--state-inactive-color, var(--grey-color, #9e9e9e)));
    --ha-ripple-hover-opacity: 0.04;
    --ha-ripple-pressed-opacity: 0.12;
    --ha-ripple-color: var(--pv-text);
    display: block;
    color: var(--pv-text);
    -webkit-tap-highlight-color: transparent;
  }
  /* Light themes: the palette above is tuned for dark cards. */
  :host([light]) {
    --pv-muted: var(--pivot-muted-color, rgba(0, 0, 0, 0.45));
    --pv-description: var(--pivot-description-color, rgba(0, 0, 0, 0.55));
    --pv-status-text: var(--pivot-status-text-color, var(--primary-text-color, #212121));
    --pv-toggle-track: var(--pivot-toggle-track-color, rgba(0, 0, 0, 0.1));
    --pv-toggle-edge: var(--pivot-toggle-edge-color, transparent);
    --pv-toggle-off: var(--pivot-toggle-off-color, rgba(0, 0, 0, 0.38));
    --pv-toggle-on: var(--pivot-toggle-on-color, var(--primary-text-color, #212121));
    --pv-strip: var(--pivot-timer-strip-color, rgba(0, 0, 0, 0.05));
    --pv-button: var(--pivot-button-color, rgba(0, 0, 0, 0.14));
    --pv-button-idle: var(--pivot-button-idle-color, rgba(0, 0, 0, 0.06));
    --pv-preset: var(--pivot-preset-color, rgba(0, 0, 0, 0.7));
    --pv-preset-selected: var(--pivot-preset-selected-color, var(--primary-text-color, #212121));
    --pv-dimmed-icon: var(--pivot-dimmed-icon-color, rgba(0, 0, 0, 0.3));
    --pv-active-border: var(--pivot-active-border-color, rgba(0, 0, 0, 0.25));
    --pv-volume-track: var(--pivot-volume-track-color, rgba(0, 0, 0, 0.15));
    --pv-volume-fill: var(--pivot-volume-fill-color, var(--primary-text-color, #212121));
  }
  * {
    box-sizing: border-box;
  }
  svg {
    display: block;
    width: 100%;
    height: 100%;
    fill: currentColor;
  }
  button {
    font: inherit;
    color: inherit;
    background: none;
    border: 0;
    margin: 0;
    padding: 0;
    text-align: inherit;
    -webkit-tap-highlight-color: transparent;
  }
  button:focus-visible,
  [role='switch']:focus-visible,
  [role='button']:focus-visible {
    outline: 2px solid var(--primary-color, #03a9f4);
    outline-offset: -2px;
  }
  .tap {
    position: relative;
    cursor: pointer;
  }
  .text {
    font-size: 14px;
    font-weight: 400;
    line-height: normal;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  /* The on/off switch: a 45x27 track and a 21px knob with an even 3px gap all round. */
  .toggle {
    position: relative;
    flex: none;
    width: 45px;
    height: 27px;
    border-radius: 25px;
    background: var(--pv-toggle-track);
    /* The edge keeps the track visible where the dark fill meets a black page. */
    box-shadow: inset 0 0 0 1px var(--pv-toggle-edge);
  }
  .toggle .knob {
    position: absolute;
    top: 3px;
    left: 3px;
    width: 21px;
    height: 21px;
    border-radius: 50%;
    background: var(--pv-toggle-off);
    transition: left 0.15s ease, background-color 0.15s ease;
  }
  .toggle.on .knob {
    left: 21px;
    background: var(--pv-toggle-on);
  }
  .disabled {
    pointer-events: none;
  }
  @media (prefers-reduced-motion: reduce) {
    .toggle .knob {
      transition: none;
    }
  }
`;
