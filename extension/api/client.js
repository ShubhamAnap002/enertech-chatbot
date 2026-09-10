const DEFAULT_API = "http://127.0.0.1:8000";

export async function getApiBase() {
  const { apiBase } = await chrome.storage.local.get({ apiBase: DEFAULT_API });
  return apiBase || DEFAULT_API;
}

export async function getAuth() {
  return chrome.storage.local.get({
    accessToken: null,
    tenantId: null,
    deviceId: null,
    plan: null,
    entitlements: {},
    configVersion: 0,
    config: null,
  });
}

export async function api(path, { method = "GET", body, auth = true } = {}) {
  const base = await getApiBase();
  const headers = { "Content-Type": "application/json" };
  if (auth) {
    const { accessToken } = await getAuth();
    if (accessToken) headers.Authorization = `Bearer ${accessToken}`;
  }
  const res = await fetch(`${base}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const err = new Error(data.detail ? JSON.stringify(data.detail) : res.statusText);
    err.status = res.status;
    err.data = data;
    throw err;
  }
  return data;
}
