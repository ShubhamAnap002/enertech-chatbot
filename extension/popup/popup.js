import { api } from "../api/client.js";
import { ensureDeviceId, savePairing } from "../auth/pairing.js";

const msg = document.getElementById("msg");
const pairSection = document.getElementById("pair-section");
const statusSection = document.getElementById("status-section");

async function refresh() {
  const data = await chrome.storage.local.get({ paired: false, plan: "", tenantId: "", running: false });
  if (data.paired) {
    pairSection.hidden = true;
    statusSection.hidden = false;
    document.getElementById("status-line").textContent = data.running ? "Automation running" : "Paired — idle";
    document.getElementById("plan-line").textContent = `Plan: ${data.plan || "—"} · Tenant: ${(data.tenantId || "").slice(0, 8)}…`;
  } else {
    pairSection.hidden = false;
    statusSection.hidden = true;
  }
}

document.getElementById("pair-btn").addEventListener("click", async () => {
  msg.textContent = "Pairing…";
  try {
    const setup_key = document.getElementById("setup-key").value.trim();
    const device_id = await ensureDeviceId();
    const result = await api("/api/extension/pair", {
      method: "POST",
      auth: false,
      body: { setup_key, device_id, extension_version: chrome.runtime.getManifest().version },
    });
    await savePairing(result);
    msg.textContent = "Paired successfully";
    await refresh();
  } catch (e) {
    msg.textContent = e.message || "Pairing failed";
  }
});

document.getElementById("start-btn").addEventListener("click", async () => {
  await chrome.storage.local.set({ running: true });
  chrome.runtime.sendMessage({ type: "START" });
  await refresh();
});

document.getElementById("stop-btn").addEventListener("click", async () => {
  await chrome.storage.local.set({ running: false });
  chrome.runtime.sendMessage({ type: "STOP" });
  await refresh();
});

document.getElementById("options-btn").addEventListener("click", () => {
  chrome.runtime.openOptionsPage();
});

refresh();
