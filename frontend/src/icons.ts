// The few Material Design Icons the cards draw, inlined so nothing depends on
// Home Assistant's icon loading.
import { mdiCircle, mdiClose, mdiPalette, mdiPause, mdiPencil, mdiPlay, mdiRefresh, mdiVolumeHigh, mdiVolumeMute } from '@mdi/js';
import { html } from 'lit';

export const ICONS = {
  circle: mdiCircle,
  close: mdiClose,
  palette: mdiPalette,
  pause: mdiPause,
  pencil: mdiPencil,
  play: mdiPlay,
  refresh: mdiRefresh,
  volumeHigh: mdiVolumeHigh,
  volumeMute: mdiVolumeMute,
};

export const icon = (path: string) =>
  html`<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d=${path}></path></svg>`;
