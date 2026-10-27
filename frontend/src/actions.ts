// Service calls and the events Home Assistant's frontend listens for.
import type { HomeAssistant } from './types';

export function fire(node: EventTarget, type: string, detail?: unknown): void {
  node.dispatchEvent(new CustomEvent(type, { detail, bubbles: true, composed: true }));
}

export const moreInfo = (node: EventTarget, entityId: string) => fire(node, 'hass-more-info', { entityId });

/** Light haptic tap in the companion apps. */
export const haptic = (node: EventTarget) => fire(node, 'haptic', 'light');

/** Calls a service; a failure becomes a toast instead of an unhandled rejection. */
export async function callService(
  node: EventTarget,
  hass: HomeAssistant,
  domain: string,
  service: string,
  data: Record<string, unknown>,
): Promise<boolean> {
  try {
    await hass.callService(domain, service, data);
    return true;
  } catch (err) {
    const message = (err as { message?: string })?.message ?? String(err);
    console.warn(`Pivot: ${domain}.${service} failed`, err);
    fire(node, 'hass-notification', { message: `Pivot: ${message}` });
    return false;
  }
}

export const toggleEntity = (node: EventTarget, hass: HomeAssistant, entityId: string) =>
  callService(node, hass, entityId.split('.')[0], 'toggle', { entity_id: entityId });

export const hasService = (hass: HomeAssistant, domain: string, service: string) =>
  !!hass.services?.[domain]?.[service];

export interface Throttled<T extends unknown[]> {
  (...args: T): void;
  cancel(): void;
  flush(): void;
}

/** Leading and trailing throttle. */
export function throttle<T extends unknown[]>(fn: (...args: T) => void, ms: number): Throttled<T> {
  let last = 0;
  let timer: ReturnType<typeof setTimeout> | undefined;
  let pending: T | undefined;
  const run = () => {
    last = Date.now();
    timer = undefined;
    const args = pending;
    pending = undefined;
    if (args) fn(...args);
  };
  const throttled = ((...args: T) => {
    pending = args;
    const wait = ms - (Date.now() - last);
    if (wait <= 0) {
      if (timer) clearTimeout(timer);
      run();
    } else if (!timer) {
      timer = setTimeout(run, wait);
    }
  }) as Throttled<T>;
  throttled.cancel = () => {
    if (timer) clearTimeout(timer);
    timer = undefined;
    pending = undefined;
  };
  throttled.flush = () => {
    if (!pending) return;
    if (timer) clearTimeout(timer);
    run();
  };
  return throttled;
}
