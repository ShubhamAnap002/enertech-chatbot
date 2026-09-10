import { api } from "../api/client.js";
import { getDefaultConfig, loadLocalConfig, saveLocalConfig, validateConfig } from "../storage/config.js";

function csv(value) {
  return (value || "")
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);
}

function fill(config) {
  document.getElementById("keywords").value = (config.keywords || []).join(", ");
  document.getElementById("restricted").value = (config.restricted_keywords || []).join(", ");
  document.getElementById("locations").value = (config.locations || []).join(", ");
  document.getElementById("cap-min").value = config.capacity?.min ?? "";
  document.getElementById("cap-max").value = config.capacity?.max ?? "";
  document.getElementById("daily-limit").value = config.scheduler?.daily_limit ?? 50;
  document.getElementById("hours-start").value = config.scheduler?.buying_hours?.start || "09:00";
  document.getElementById("hours-end").value = config.scheduler?.buying_hours?.end || "18:00";
  document.getElementById("refresh-interval").value = config.auto_refresh?.interval_seconds ?? 30;
  document.getElementById("auto-buy").checked = !!config.auto_buy;
  document.getElementById("auto-refresh").checked = !!config.auto_refresh?.enabled;
  document.getElementById("scheduler").checked = !!config.scheduler?.enabled;
}

function read() {
  const base = getDefaultConfig();
  return {
    ...base,
    keywords: csv(document.getElementById("keywords").value),
    restricted_keywords: csv(document.getElementById("restricted").value),
    locations: csv(document.getElementById("locations").value),
    capacity: {
      ...base.capacity,
      min: num(document.getElementById("cap-min").value),
      max: num(document.getElementById("cap-max").value),
    },
    scheduler: {
      ...base.scheduler,
      enabled: document.getElementById("scheduler").checked,
      daily_limit: num(document.getElementById("daily-limit").value) ?? 50,
      buying_hours: {
        start: document.getElementById("hours-start").value || "09:00",
        end: document.getElementById("hours-end").value || "18:00",
      },
    },
    auto_buy: document.getElementById("auto-buy").checked,
    auto_refresh: {
      enabled: document.getElementById("auto-refresh").checked,
      interval_seconds: num(document.getElementById("refresh-interval").value) ?? 30,
    },
  };
}

function num(v) {
  if (v === "" || v == null) return null;
  const n = Number(v);
  return Number.isFinite(n) ? n : null;
}

document.getElementById("save-btn").addEventListener("click", async () => {
  const msg = document.getElementById("save-msg");
  msg.textContent = "Saving…";
  const config = read();
  const errors = validateConfig(config);
  if (errors.length) {
    msg.textContent = errors.join("; ");
    return;
  }
  try {
    const saved = await api("/api/extension/config", { method: "PUT", body: { config } });
    await saveLocalConfig(saved.config, saved.version);
    msg.textContent = `Saved Training · version ${saved.version}`;
    chrome.runtime.sendMessage({ type: "CONFIG_UPDATED" });
  } catch (e) {
    msg.textContent = e.message || "Save failed";
  }
});

(async () => {
  const local = await loadLocalConfig();
  fill(local.config);
  try {
    const remote = await api("/api/extension/config");
    if (remote.version && remote.version !== local.configVersion) {
      await saveLocalConfig(remote.config || getDefaultConfig(), remote.version);
      fill(remote.config || getDefaultConfig());
    }
  } catch {
    // offline: keep local
  }
})();
