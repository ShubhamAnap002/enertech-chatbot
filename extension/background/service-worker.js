import { api } from "../api/client.js";
import { loadLocalConfig } from "../storage/config.js";

async function heartbeat() {
  const auth = await chrome.storage.local.get({ paired: false, deviceId: null, configVersion: 0, running: false });
  if (!auth.paired || !auth.deviceId) return;
  try {
    await api("/api/extension/heartbeat", {
      method: "POST",
      body: {
        device_id: auth.deviceId,
        extension_version: chrome.runtime.getManifest().version,
        state: auth.running ? "running" : "idle",
        config_version: auth.configVersion || 0,
      },
    });
  } catch (e) {
    console.warn("heartbeat failed", e.message);
  }
}

async function syncConfig() {
  const local = await loadLocalConfig();
  try {
    const remote = await api("/api/extension/config");
    if (remote.version && remote.version !== local.configVersion) {
      await chrome.storage.local.set({ config: remote.config, configVersion: remote.version });
    }
  } catch {
    /* ignore */
  }
}

function scheduleRefreshAlarm() {
  chrome.storage.local.get({ config: null, running: false }, (data) => {
    chrome.alarms.clear("auto-refresh");
    const interval = data.config?.auto_refresh?.interval_seconds || 30;
    if (data.running && data.config?.auto_refresh?.enabled) {
      chrome.alarms.create("auto-refresh", { periodInMinutes: Math.max(0.25, interval / 60) });
    }
  });
}

chrome.runtime.onInstalled.addListener(() => {
  chrome.alarms.create("heartbeat", { periodInMinutes: 5 });
});

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === "heartbeat") heartbeat();
  if (alarm.name === "auto-refresh") {
    chrome.tabs.query({ url: "https://*.indiamart.com/*" }, (tabs) => {
      for (const tab of tabs) {
        chrome.tabs.sendMessage(tab.id, { type: "REFRESH_SCAN" }).catch(() => {});
      }
    });
  }
});

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg.type === "START") {
    chrome.storage.local.set({ running: true }, () => {
      scheduleRefreshAlarm();
      chrome.tabs.query({ url: "https://*.indiamart.com/*" }, (tabs) => {
        for (const tab of tabs) chrome.tabs.sendMessage(tab.id, { type: "START_SCAN" }).catch(() => {});
      });
    });
  }
  if (msg.type === "STOP") {
    chrome.storage.local.set({ running: false }, () => scheduleRefreshAlarm());
  }
  if (msg.type === "CONFIG_UPDATED") scheduleRefreshAlarm();
  if (msg.type === "LEAD_EVENT") {
    api("/api/extension/lead-event", { method: "POST", body: msg.payload })
      .then((r) => sendResponse(r))
      .catch((e) => sendResponse({ ok: false, error: e.message }));
    return true;
  }
  if (msg.type === "GET_RUNTIME") {
    chrome.storage.local.get({ boughtToday: 0, lastBuyAt: 0, running: false, config: null }, sendResponse);
    return true;
  }
});

heartbeat();
syncConfig();
scheduleRefreshAlarm();
