import { afterEach, describe, expect, it } from 'vitest';
import '../src/index';
import type { HomeAssistant } from '../src/types';
import { S, makeHass } from './hass';

type Card = HTMLElement & { hass?: HomeAssistant; setConfig(c: Record<string, unknown>): void; updateComplete: Promise<boolean> };

async function mount(tag: string, config: Record<string, unknown>, hass = makeHass()) {
  const el = document.createElement(tag) as Card;
  el.setConfig({ type: `custom:${tag}`, device: S, ...config });
  el.hass = hass;
  document.body.append(el);
  await el.updateComplete;
  return { el, hass, root: el.shadowRoot! };
}

const text = (root: ShadowRoot, sel: string) => root.querySelector(sel)?.textContent?.replace(/\s+/g, ' ').trim();

afterEach(() => {
  document.body.innerHTML = '';
});

describe('pivot-bank-card', () => {
  it('renders a light bank like the template: name, value, bar, mirror and announce rows', async () => {
    const { root } = await mount('pivot-bank-card', { bank: 1 });
    expect(text(root, '.head .label')).toBe('Bank 1');
    expect(text(root, '.name')).toBe('Desk Lamp');
    expect(text(root, '.value')).toBe('50%');
    expect(root.querySelector('pivot-slider')).not.toBeNull();
    expect(root.querySelector('[aria-label="Mirror Light Colour"]')).not.toBeNull();
    expect(root.querySelector('[aria-label="Announce Value"]')).not.toBeNull();
    expect(root.querySelector('ha-card')!.classList.contains('active')).toBe(true);
  });

  it('a passive switch bank has no bar and no announce row', async () => {
    const { root } = await mount('pivot-bank-card', { bank: 2 });
    expect(text(root, '.value')).toBe('Off');
    expect(root.querySelector('pivot-slider')).toBeNull();
    expect(root.querySelector('[aria-label="Announce Value"]')).toBeNull();
  });

  it('tapping an inactive bank makes it active', async () => {
    const { root, hass } = await mount('pivot-bank-card', { bank: 3 });
    (root.querySelector('ha-card') as HTMLElement).click();
    expect(hass.calls).toEqual([{ domain: 'number', service: 'set_value', data: { entity_id: `number.${S}_active_bank`, value: 3 } }]);
  });

  it('tapping a toggle row toggles its switch, not the bank', async () => {
    const { root, hass } = await mount('pivot-bank-card', { bank: 1 });
    (root.querySelector('[aria-label="Announce Value"]') as HTMLElement).click();
    expect(hass.calls).toEqual([{ domain: 'switch', service: 'toggle', data: { entity_id: `switch.${S}_bank_1_announce_value` } }]);
  });

  it('announce rows are inert while announcements are muted', async () => {
    const { root } = await mount('pivot-bank-card', { bank: 1 }, makeHass({ [`switch.${S}_mute_announcements`]: { state: 'on' } }));
    expect(root.querySelector('[aria-label="Announce Value"]')!.classList.contains('muted')).toBe(true);
  });

  it('the name opens more-info for the bound entity', async () => {
    const { root } = await mount('pivot-bank-card', { bank: 1 });
    const seen: string[] = [];
    window.addEventListener('hass-more-info', (e) => seen.push((e as CustomEvent).detail.entityId), { once: true });
    (root.querySelector('.name-row') as HTMLElement).click();
    expect(seen).toEqual(['light.desk_lamp']);
  });

  it('the timer bank shows controls, presets and the silent switch found on the ESPHome device', async () => {
    const { root, hass } = await mount('pivot-bank-card', { bank: 4 });
    expect(text(root, '.value')).toBe('25 mins');
    expect([...root.querySelectorAll('.preset')].map((p) => p.textContent!.trim())).toEqual(['15m', '30m', '45m', '60m']);
    expect(root.querySelector('[aria-label="Silent Timer"]')).not.toBeNull();
    (root.querySelector('[aria-label="Start timer"]') as HTMLElement).click();
    await Promise.resolve();
    expect(hass.calls).toEqual([{ domain: 'pivot', service: 'timer_toggle', data: { device: S, bank: 4 } }]);
  });

  it('a preset on an inactive timer bank sets the duration directly', async () => {
    const { root, hass } = await mount('pivot-bank-card', { bank: 4 });
    (root.querySelectorAll('.preset')[1] as HTMLElement).click();
    expect(hass.calls).toEqual([
      { domain: 'number', service: 'set_value', data: { entity_id: `number.${S}_timer_duration`, value: 30 } },
      { domain: 'number', service: 'set_value', data: { entity_id: `number.${S}_bank_4_value`, value: 50 } },
    ]);
  });

  it('a preset on the active timer bank goes through the bank value, like the knob', async () => {
    const { root, hass } = await mount('pivot-bank-card', { bank: 4 }, makeHass({ [`number.${S}_active_bank`]: { state: '4' } }));
    (root.querySelectorAll('.preset')[3] as HTMLElement).click();
    expect(hass.calls).toEqual([{ domain: 'number', service: 'set_value', data: { entity_id: `number.${S}_bank_4_value`, value: 100 } }]);
  });

  it('explains disabled timer entities instead of showing dead controls', async () => {
    const { root } = await mount('pivot-bank-card', { bank: 4 }, makeHass({ [`select.${S}_timer_state`]: null }));
    expect(root.querySelector('.strip')).toBeNull();
    expect(text(root, '.notice')).toMatch(/Timer entities are disabled/);
  });

  it('control mode off dims the card and locks the bar', async () => {
    const { root } = await mount('pivot-bank-card', { bank: 1 }, makeHass({ [`switch.${S}_control_mode`]: { state: 'off' } }));
    expect(root.querySelector('ha-card')!.classList.contains('control-off')).toBe(true);
    expect((root.querySelector('pivot-slider') as HTMLElement & { disabled: boolean }).disabled).toBe(true);
  });

  it('rejects a bank outside 1–4', () => {
    const el = document.createElement('pivot-bank-card') as Card;
    expect(() => el.setConfig({ type: 'custom:pivot-bank-card', device: S, bank: 5 })).toThrow(/bank/);
  });

  it('says so when the device does not exist', async () => {
    const { root } = await mount('pivot-bank-card', { device: 'nope', bank: 1 });
    expect(text(root, '.pv-problem')).toMatch(/No Pivot device “nope”/);
  });
});

describe('pivot-status-card', () => {
  it('shows the title and the active bank', async () => {
    const { root } = await mount('pivot-status-card', {});
    expect(text(root, '.title')).toBe('Desk Pivot');
    expect(text(root, '.status')).toBe('Bank 1 - Desk Lamp');
  });
  it('says when control mode is off', async () => {
    const { root } = await mount('pivot-status-card', { name: 'Desk' }, makeHass({ [`switch.${S}_control_mode`]: { state: 'off' } }));
    expect(text(root, '.title')).toBe('Desk');
    expect(text(root, '.status')).toBe('Control mode off');
  });
});

describe('pivot-settings-card', () => {
  it('lists the rows under their headings with the template wording', async () => {
    const { root } = await mount('pivot-settings-card', {});
    expect([...root.querySelectorAll('.heading')].map((h) => h.textContent)).toEqual(['Device', 'Behaviour']);
    expect([...root.querySelectorAll('.stitle')].map((h) => h.textContent)).toEqual([
      'Control Mode', 'System Announcements', 'Mute Announcements', 'Display Persistent Value', 'Dim Gauge LEDs While Idle',
    ]);
  });
  it('dims "Dim Gauge LEDs" while the value is not shown', async () => {
    const { root } = await mount('pivot-settings-card', {}, makeHass({ [`switch.${S}_show_control_value`]: { state: 'off' } }));
    expect(root.querySelector('[aria-label="Dim Gauge LEDs While Idle"]')!.classList.contains('dependent-off')).toBe(true);
  });
  it('honours a custom row list without headings', async () => {
    const { root } = await mount('pivot-settings-card', { rows: ['mute_announcements', 'volume'], headings: false });
    expect(root.querySelectorAll('.heading').length).toBe(0);
    expect(root.querySelectorAll('.srow').length).toBe(1);
    expect(root.querySelector('.volume')).not.toBeNull();
  });
  it('rejects unknown rows', () => {
    const el = document.createElement('pivot-settings-card') as Card;
    expect(() => el.setConfig({ type: 'custom:pivot-settings-card', device: S, rows: ['nope'] })).toThrow(/Unknown rows/);
  });
});

describe('pivot-device-card', () => {
  it('composes the status, four banks and the settings', async () => {
    const { root } = await mount('pivot-device-card', {});
    expect(root.querySelectorAll('pivot-bank-card').length).toBe(4);
    expect(root.querySelector('pivot-status-card')).not.toBeNull();
    expect(root.querySelector('pivot-settings-card')).not.toBeNull();
  });
  it('can drop the settings and the status', async () => {
    const { root } = await mount('pivot-device-card', { show_settings: false, show_status: false });
    expect(root.querySelector('pivot-settings-card')).toBeNull();
    expect(root.querySelector('pivot-status-card')).toBeNull();
  });
});

describe('card picker', () => {
  it('registers all four cards once', () => {
    const types = (window.customCards ?? []).map((c) => c.type);
    expect(types.filter((t) => t.startsWith('pivot-')).sort()).toEqual(['pivot-bank-card', 'pivot-device-card', 'pivot-settings-card', 'pivot-status-card']);
  });
  it('stub configs pick the first device', () => {
    const Ctor = customElements.get('pivot-device-card') as unknown as { getStubConfig(h: HomeAssistant): { device: string } };
    expect(Ctor.getStubConfig(makeHass()).device).toBe(S);
  });
});
