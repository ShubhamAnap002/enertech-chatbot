export async function ensureDeviceId() {
  const stored = await chrome.storage.local.get({ deviceId: null });
  if (stored.deviceId) return stored.deviceId;
  const deviceId = crypto.randomUUID();
  await chrome.storage.local.set({ deviceId });
  return deviceId;
}

export async function savePairing(result) {
  await chrome.storage.local.set({
    accessToken: result.access_token,
    tenantId: result.tenant_id,
    deviceId: result.device_id,
    plan: result.plan,
    entitlements: result.entitlements,
    configVersion: result.config_version,
    paired: true,
  });
}

export async function clearAuth() {
  await chrome.storage.local.remove([
    "accessToken",
    "tenantId",
    "plan",
    "entitlements",
    "paired",
  ]);
}
