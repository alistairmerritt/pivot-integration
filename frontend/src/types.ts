// The slice of Home Assistant's frontend types the cards use.

export interface HassEntity {
  entity_id: string;
  state: string;
  attributes: Record<string, any>;
  last_changed: string;
  last_updated: string;
}

export interface EntityRegistryDisplayEntry {
  entity_id: string;
  device_id?: string;
  platform?: string;
  name?: string | null;
}

export interface DeviceRegistryEntry {
  id: string;
  name: string | null;
  name_by_user: string | null;
  identifiers?: [string, string][];
  manufacturer?: string | null;
}

export interface HomeAssistant {
  states: Record<string, HassEntity>;
  entities?: Record<string, EntityRegistryDisplayEntry>;
  devices?: Record<string, DeviceRegistryEntry>;
  services?: Record<string, Record<string, unknown>>;
  themes?: unknown;
  callService(
    domain: string,
    service: string,
    data?: Record<string, unknown>,
    target?: Record<string, unknown>,
  ): Promise<unknown>;
}

export interface LovelaceCardConfig {
  type: string;
  [key: string]: unknown;
}

declare global {
  const __PIVOT_VERSION__: string;
  interface Window {
    customCards?: { type: string; name: string; description?: string; preview?: boolean; documentationURL?: string }[];
    loadCardHelpers?: () => Promise<{ createCardElement(config: LovelaceCardConfig): HTMLElement }>;
  }
}
