// The cards must not define themselves before Home Assistant's app has
// swapped in its scoped element registry, or every card shows
// "Custom element doesn't exist".
import { afterEach, describe, expect, it, vi } from 'vitest';

afterEach(() => {
  document.body.innerHTML = '';
  vi.resetModules();
});

describe('defineElement', () => {
  it('on a Home Assistant page, waits for the app before defining', async () => {
    document.body.append(document.createElement('home-assistant'));
    const { defineElement } = await import('../src/register');
    defineElement('pv-test-wait', class extends HTMLElement {});
    await Promise.resolve();
    expect(customElements.get('pv-test-wait')).toBeUndefined();
    customElements.define('home-assistant', class extends HTMLElement {});
    await customElements.whenDefined('pv-test-wait');
    expect(customElements.get('pv-test-wait')).toBeDefined();
  });

  it('anywhere else, defines straight away', async () => {
    const { defineElement } = await import('../src/register');
    defineElement('pv-test-now', class extends HTMLElement {});
    expect(customElements.get('pv-test-now')).toBeDefined();
  });

  it('never defines the same element twice', async () => {
    const { defineElement } = await import('../src/register');
    class A extends HTMLElement {}
    defineElement('pv-test-once', A);
    expect(() => defineElement('pv-test-once', class extends HTMLElement {})).not.toThrow();
    expect(customElements.get('pv-test-once')).toBe(A);
  });
});
