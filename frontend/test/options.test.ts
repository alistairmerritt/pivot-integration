// The card options added in 0.0.95: which banks show, how bank cards are
// trimmed, timer presets, and where the settings go.
import { afterEach, describe, expect, it } from 'vitest';
import '../src/index';
import type { HomeAssistant } from '../src/types';
import { S, makeHass } from './hass';

type Card = HTMLElement & { hass?: HomeAssistant; setConfig(c: Record<string, unknown>): void; updateComplete: Promise<boolean> };
type Child = Card & { _config: Record<string, unknown> };

async function mount(tag: string, config: Record<string, unknown>, hass = makeHass()) {
  const el = document.createElement(tag) as Card;
  el.setConfig({ type: `custom:${tag}`, device: S, ...config });
  el.hass = hass;
  document.body.append(el);
  await el.updateComplete;
  return { el, hass, root: el.shadowRoot! };
}

async function rehass(el: Card, hass: HomeAssistant) {
  el.hass = hass;
  await el.updateComplete;
}

const text = (root: ShadowRoot, sel: string) => root.querySelector(sel)?.textContent?.replace(/\s+/g, ' ').trim();
const bankCards = (root: ShadowRoot) => [...root.querySelectorAll('pivot-bank-card')] as Child[];
const rejects = (tag: string, config: Record<string, unknown>) => () =>
  (document.createElement(tag) as Card).setConfig({ type: `custom:${tag}`, device: S, ...config });

afterEach(() => {
  document.body.innerHTML = '';
});

describe('bank card: which bank', () => {
  it('bank: active shows the bank the dial is on, and follows it', async () => {
    const { el, root } = await mount('pivot-bank-card', { bank: 'active' });
    expect(text(root, '.head .label')).toBe('Bank 1');
    expect(text(root, '.name')).toBe('Desk Lamp');
    await rehass(el, makeHass({ [`number.${S}_active_bank`]: { state: '3.0' } }));
    expect(text(root, '.head .label')).toBe('Bank 3');
    expect(text(root, '.name')).toBe('Speaker Volume');
    expect(root.querySelector('ha-card')!.classList.contains('active')).toBe(true);
  });

  it('bank: timer finds the timer bank, wherever it is', async () => {
    const { el, root } = await mount('pivot-bank-card', { bank: 'timer' });
    expect(text(root, '.head .label')).toBe('Bank 4');
    await rehass(el, makeHass({ [`text.${S}_bank_4_entity`]: { state: 'light.desk_lamp' }, [`text.${S}_bank_2_entity`]: { state: 'timer' } }));
    expect(text(root, '.head .label')).toBe('Bank 2');
    expect(text(root, '.name')).toBe('Timer');
  });

  it('says so when no bank is the timer', async () => {
    const { root } = await mount('pivot-bank-card', { bank: 'timer' }, makeHass({ [`text.${S}_bank_4_entity`]: { state: '' } }));
    expect(text(root, '.notice')).toMatch(/No bank on Desk Pivot is set to Timer/);
  });

  it('says so when the active bank is unreadable', async () => {
    const { root } = await mount('pivot-bank-card', { bank: 'active' }, makeHass({ [`number.${S}_active_bank`]: { state: 'unavailable' } }));
    expect(text(root, '.notice')).toMatch(/isn’t reporting its active bank/);
  });

  it('a drag on an active-bank card never lands on the bank the dial moved to', async () => {
    const { el, root, hass } = await mount('pivot-bank-card', { bank: 'active' });
    const slider = () => root.querySelector('pivot-slider')!;
    slider().dispatchEvent(new CustomEvent('pivot-slide-start', { bubbles: true, composed: true }));
    await rehass(el, Object.assign(makeHass({ [`number.${S}_active_bank`]: { state: '3.0' } }), { calls: hass.calls, callService: hass.callService }));
    slider().dispatchEvent(new CustomEvent('pivot-slide-end', { detail: { value: 70 }, bubbles: true, composed: true }));
    expect(hass.calls.some((c) => c.data.entity_id === `number.${S}_bank_3_value`)).toBe(false);
  });

  it('during a drag the card stays on its bank, then catches up with the dial', async () => {
    const { el, root, hass } = await mount('pivot-bank-card', { bank: 'active' });
    const slider = () => root.querySelector('pivot-slider')!;
    slider().dispatchEvent(new CustomEvent('pivot-slide-start', { bubbles: true, composed: true }));
    await rehass(el, Object.assign(makeHass({ [`number.${S}_active_bank`]: { state: '4.0' } }), { calls: hass.calls, callService: hass.callService }));
    expect(text(root, '.head .label')).toBe('Bank 1');
    expect(root.querySelector('.strip')).toBeNull();
    slider().dispatchEvent(new CustomEvent('pivot-slide-end', { detail: { value: 70 }, bubbles: true, composed: true }));
    await el.updateComplete;
    // The light drag never became a timer duration, and nothing went to bank 4.
    expect(hass.calls.filter((c) => /timer_duration|bank_4/.test(String(c.data.entity_id)))).toEqual([]);
    expect(text(root, '.head .label')).toBe('Bank 4');
  });

  it('rejects anything else', () => {
    expect(rejects('pivot-bank-card', { bank: 'first' })).toThrow(/bank must be 1, 2, 3, 4, active or timer/);
    expect(rejects('pivot-bank-card', { bank: 0 })).toThrow(/bank must/);
  });
});

describe('bank card: what it shows', () => {
  it('show_edit: false drops EDIT ENTITY', async () => {
    const { root } = await mount('pivot-bank-card', { bank: 1, show_edit: false });
    expect(root.querySelector('.edit')).toBeNull();
    expect(text(root, '.head .label')).toBe('Bank 1');
  });

  it('show_bank_options: false drops Mirror Light Colour and Announce Value but keeps Silent Timer', async () => {
    const light = await mount('pivot-bank-card', { bank: 1, show_bank_options: false });
    expect(light.root.querySelector('[aria-label="Mirror Light Colour"]')).toBeNull();
    expect(light.root.querySelector('[aria-label="Announce Value"]')).toBeNull();
    const timer = await mount('pivot-bank-card', { bank: 4, show_bank_options: false });
    expect(timer.root.querySelector('[aria-label="Silent Timer"]')).not.toBeNull();
  });

  it('show_silent_timer: false drops the Silent Timer row', async () => {
    const { root } = await mount('pivot-bank-card', { bank: 4, show_silent_timer: false });
    expect(root.querySelector('[aria-label="Silent Timer"]')).toBeNull();
    expect(root.querySelector('.strip')).not.toBeNull();
  });
});

describe('bank card: timer presets', () => {
  it('draws the chosen presets and sizes the strip for them', async () => {
    const { root } = await mount('pivot-bank-card', { bank: 4, timer_presets: [5, 10, 25] });
    expect([...root.querySelectorAll('.preset')].map((p) => p.textContent!.trim())).toEqual(['5m', '10m', '25m']);
    expect((root.querySelector('.strip') as HTMLElement).getAttribute('style')).toContain('--pv-presets:3');
    expect(root.querySelector('.preset.selected')!.textContent!.trim()).toBe('25m');
  });

  it('a custom preset writes the minutes and the gauge value that means them', async () => {
    const { root, hass } = await mount('pivot-bank-card', { bank: 4, timer_presets: [10] });
    (root.querySelector('.preset') as HTMLElement).click();
    expect(hass.calls).toEqual([
      { domain: 'number', service: 'set_value', data: { entity_id: `number.${S}_timer_duration`, value: 10 } },
      { domain: 'number', service: 'set_value', data: { entity_id: `number.${S}_bank_4_value`, value: 15 } },
    ]);
  });

  it('no presets leaves play and cancel sharing the strip', async () => {
    const { root } = await mount('pivot-bank-card', { bank: 4, timer_presets: [] });
    expect(root.querySelector('.preset')).toBeNull();
    expect(root.querySelector('.strip')!.classList.contains('no-presets')).toBe(true);
  });

  it('rejects presets it cannot honour', () => {
    expect(rejects('pivot-bank-card', { bank: 4, timer_presets: [0] })).toThrow(/1 to 60/);
    expect(rejects('pivot-bank-card', { bank: 4, timer_presets: [61] })).toThrow(/1 to 60/);
    expect(rejects('pivot-bank-card', { bank: 4, timer_presets: [2.5] })).toThrow(/whole minutes/);
    expect(rejects('pivot-bank-card', { bank: 4, timer_presets: [1, 2, 3, 4, 5, 6, 7] })).toThrow(/at most 6/);
    expect(rejects('pivot-bank-card', { bank: 4, timer_presets: [5, 5] })).toThrow(/twice/);
    expect(rejects('pivot-bank-card', { bank: 4, timer_presets: '15, 30' })).toThrow(/list of minutes/);
  });
});

describe('status card', () => {
  it('can hide the title or the active bank line', async () => {
    const noTitle = await mount('pivot-status-card', { show_title: false });
    expect(noTitle.root.querySelector('.title')).toBeNull();
    expect(text(noTitle.root, '.status')).toBe('Bank 1 - Desk Lamp');
    const noLine = await mount('pivot-status-card', { show_active_bank: false });
    expect(text(noLine.root, '.title')).toBe('Desk Pivot');
    expect(noLine.root.querySelector('.status')).toBeNull();
  });

  it('still reads the 0.0.93 show_name', async () => {
    const { root } = await mount('pivot-status-card', { show_name: false });
    expect(root.querySelector('.title')).toBeNull();
  });

  it('an empty title falls back to the device name', async () => {
    const { root } = await mount('pivot-status-card', { name: '  ' });
    expect(text(root, '.title')).toBe('Desk Pivot');
  });
});

describe('settings card', () => {
  it('background: true draws the rows on a card', async () => {
    const { root } = await mount('pivot-settings-card', { background: true });
    expect(root.querySelector('.wrap')!.classList.contains('boxed')).toBe(true);
  });

  it('an empty row list says so instead of showing everything', async () => {
    const { root } = await mount('pivot-settings-card', { rows: [] });
    expect(root.querySelector('.srow')).toBeNull();
    expect(text(root, '.empty')).toMatch(/No settings chosen/);
  });
});

describe('device card: banks', () => {
  it('banks: a list shows only those banks, in order', async () => {
    const { root } = await mount('pivot-device-card', { banks: [3, 1] });
    expect(bankCards(root).map((b) => b._config.bank)).toEqual([1, 3]);
  });

  it('hide_unassigned drops banks with nothing assigned', async () => {
    const { root } = await mount('pivot-device-card', { hide_unassigned: true }, makeHass({ [`text.${S}_bank_2_entity`]: { state: '' } }));
    expect(bankCards(root).map((b) => b._config.bank)).toEqual([1, 3, 4]);
  });

  it('a bank that gets assigned appears without a reload', async () => {
    const { el, root } = await mount('pivot-device-card', { hide_unassigned: true }, makeHass({ [`text.${S}_bank_2_entity`]: { state: '' } }));
    await rehass(el, makeHass());
    expect(bankCards(root).length).toBe(4);
  });

  it('banks: active and banks: timer show one bank card that follows', async () => {
    const active = await mount('pivot-device-card', { banks: 'active' });
    expect(bankCards(active.root).map((b) => b._config.bank)).toEqual(['active']);
    const timer = await mount('pivot-device-card', { banks: 'timer' });
    expect(bankCards(timer.root).map((b) => b._config.bank)).toEqual(['timer']);
  });

  it('reports its real height to masonry layouts', async () => {
    const { el } = await mount('pivot-device-card', { hide_unassigned: true, show_settings: false }, makeHass({ [`text.${S}_bank_2_entity`]: { state: '' } }));
    expect((el as unknown as { getCardSize(): number }).getCardSize()).toBe(2 + 3 * 4);
    const dup = await mount('pivot-device-card', { banks: [1, 1, 2], show_settings: false });
    expect((dup.el as unknown as { getCardSize(): number }).getCardSize()).toBe(2 + 2 * 4);
  });

  it('an empty list says so', async () => {
    const { root } = await mount('pivot-device-card', { banks: [] });
    expect(bankCards(root).length).toBe(0);
    expect(text(root, '.empty')).toMatch(/No banks chosen/);
  });

  it('bank_columns: 2 asks for two banks per row', async () => {
    const { root } = await mount('pivot-device-card', { bank_columns: 2 });
    expect(root.querySelector('.bank-list')!.classList.contains('two')).toBe(true);
  });

  it('passes the bank options to every bank card', async () => {
    const { root } = await mount('pivot-device-card', { show_edit: false, show_bank_options: false, timer_presets: [5], show_silent_timer: false });
    for (const b of bankCards(root)) {
      expect(b._config).toMatchObject({ show_edit: false, show_bank_options: false, timer_presets: [5], show_silent_timer: false });
    }
  });

  it('rejects bank options it cannot honour', () => {
    expect(rejects('pivot-device-card', { banks: [5] })).toThrow(/banks must be/);
    expect(rejects('pivot-device-card', { banks: 'some' })).toThrow(/banks must be/);
    expect(rejects('pivot-device-card', { bank_columns: 3 })).toThrow(/bank_columns/);
    expect(rejects('pivot-device-card', { timer_presets: [90] })).toThrow(/1 to 60/);
  });
});

describe('device card: title and settings', () => {
  it('title and active bank can be hidden separately', async () => {
    const { root } = await mount('pivot-device-card', { show_title: false });
    const status = root.querySelector('pivot-status-card') as Child;
    expect(status._config).toMatchObject({ show_title: false, show_active_bank: true });
    const none = await mount('pivot-device-card', { show_title: false, show_active_bank: false });
    expect(none.root.querySelector('pivot-status-card')).toBeNull();
  });

  it('settings sit beside the banks by default, or below', async () => {
    const beside = await mount('pivot-device-card', {});
    expect(beside.root.querySelector('.cols')!.classList.contains('single')).toBe(false);
    const below = await mount('pivot-device-card', { settings_position: 'below' });
    expect(below.root.querySelector('.cols')!.classList.contains('single')).toBe(true);
    expect(below.root.querySelector('pivot-settings-card')).not.toBeNull();
  });

  it('hands rows, headings and background to the settings card', async () => {
    const { root } = await mount('pivot-device-card', { settings_rows: ['control_mode'], settings_headings: false, settings_background: true });
    const settings = root.querySelector('pivot-settings-card') as Child;
    expect(settings._config).toMatchObject({ rows: ['control_mode'], headings: false, background: true });
  });

  it('no settings rows means no settings column', async () => {
    const { root } = await mount('pivot-device-card', { settings_rows: [] });
    expect(root.querySelector('pivot-settings-card')).toBeNull();
    expect(root.querySelector('.cols')!.classList.contains('single')).toBe(true);
  });

  it('rejects settings options it cannot honour', () => {
    expect(rejects('pivot-device-card', { settings_position: 'left' })).toThrow(/settings_position/);
    expect(rejects('pivot-device-card', { settings_rows: ['nope'] })).toThrow(/Unknown settings_rows/);
  });
});
