// Entry point: defines the Pivot cards and lists them in the card picker.
// Served by the integration (cards.py), so nothing needs adding to resources.
import { DOCS_URL } from './const';
import './editor';
import './cards/device-card';
import './cards/bank-card';
import './cards/status-card';
import './cards/settings-card';

const CARDS = [
  { type: 'pivot-device-card', name: 'Pivot', description: 'The whole Pivot dashboard for one dial: active bank, the four banks and its settings.' },
  { type: 'pivot-bank-card', name: 'Pivot bank', description: 'One Pivot bank: its entity, value, colour, toggles and timer controls.' },
  { type: 'pivot-status-card', name: 'Pivot status', description: 'A Pivot dial’s name and its active bank.' },
  { type: 'pivot-settings-card', name: 'Pivot settings', description: 'Control mode, device volume and announcement settings for a Pivot dial.' },
];

window.customCards = window.customCards || [];
for (const card of CARDS) {
  if (!window.customCards.some((c) => c.type === card.type)) {
    window.customCards.push({ ...card, preview: true, documentationURL: DOCS_URL });
  }
}

console.info(`%c PIVOT CARDS %c ${__PIVOT_VERSION__} `, 'color:#fff;background:#545454;border-radius:4px 0 0 4px;padding:2px 4px', 'color:#545454;background:#e0e0e0;border-radius:0 4px 4px 0;padding:2px 4px');
