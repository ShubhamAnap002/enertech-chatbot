const DEFAULT_CONFIG = {
  keywords: [],
  locations: [],
  restricted_keywords: [],
  categories: [],
  quantity: { min: null, max: null },
  capacity: { min: null, max: null, unit: "kVA" },
  minimum_order_value: null,
  require_verified_buyer: false,
  scheduler: {
    enabled: false,
    buying_hours: { start: "09:00", end: "18:00" },
    daily_limit: 50,
    cooldown_seconds: 30,
  },
  auto_buy: false,
  auto_refresh: { enabled: false, interval_seconds: 30 },
  scoring_weights: {
    keyword: 30,
    location: 20,
    capacity: 20,
    quantity: 10,
    category: 10,
    verified: 10,
  },
  advanced_rules: false,
};

export function getDefaultConfig() {
  return structuredClone(DEFAULT_CONFIG);
}

export async function loadLocalConfig() {
  const { config, configVersion } = await chrome.storage.local.get({
    config: null,
    configVersion: 0,
  });
  return { config: config || getDefaultConfig(), configVersion: configVersion || 0 };
}

export async function saveLocalConfig(config, version) {
  await chrome.storage.local.set({ config, configVersion: version, updatedAt: Date.now() });
}

export function validateConfig(config) {
  const errors = [];
  const interval = config?.auto_refresh?.interval_seconds;
  if (config?.auto_refresh?.enabled) {
    if (!interval || interval < 15 || interval > 300) {
      errors.push("Auto refresh interval must be between 15 and 300 seconds");
    }
  }
  return errors;
}
