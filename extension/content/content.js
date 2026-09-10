(async () => {
  const { scanLeads } = await import(chrome.runtime.getURL("engine/scanner/scanner.js"));
  const { decide } = await import(chrome.runtime.getURL("engine/automation/runner.js"));

  async function getConfigAndRuntime() {
    return new Promise((resolve) => {
      chrome.runtime.sendMessage({ type: "GET_RUNTIME" }, (runtime) => {
        chrome.storage.local.get({ config: null, deviceId: null, running: false }, (local) => {
          resolve({ ...(runtime || {}), ...local });
        });
      });
    });
  }

  async function processPage() {
    const state = await getConfigAndRuntime();
    if (!state.running) return;
    const config = state.config;
    if (!config) return;

    const scanned = scanLeads(document);
    if (!scanned.ok) {
      console.info("Engyne: skip —", scanned.reason);
      return;
    }

    const runtime = {
      boughtToday: state.boughtToday || 0,
      lastBuyAt: state.lastBuyAt || 0,
    };

    for (const lead of scanned.leads) {
      const result = decide(lead, config, runtime);
      const action = result.decision === "BUY" ? (config.auto_buy ? "BOUGHT" : "MATCHED") : "SKIP";
      if (result.decision === "BUY" && config.auto_buy) {
        const btn = lead.element?.querySelector("button, a.btn, .buy-btn");
        if (btn && /buy|contact|consume/i.test(btn.textContent || "")) {
          try {
            btn.click();
            runtime.boughtToday += 1;
            runtime.lastBuyAt = Date.now();
            await chrome.storage.local.set({ boughtToday: runtime.boughtToday, lastBuyAt: runtime.lastBuyAt });
          } catch {
            /* ignore */
          }
        }
      }

      chrome.runtime.sendMessage({
        type: "LEAD_EVENT",
        payload: {
          device_id: state.deviceId,
          lead_hash: lead.raw_text_hash,
          title: lead.title,
          capacity: lead.capacity != null ? `${lead.capacity} ${lead.capacity_unit || ""}`.trim() : "",
          quantity: lead.quantity != null ? String(lead.quantity) : "",
          location: lead.location || "",
          score: result.score,
          action,
          reason: (result.reasons || []).join(" + "),
          rule_results: result.rule_results,
          event_timestamp: new Date().toISOString(),
        },
      });
    }
  }

  chrome.runtime.onMessage.addListener((msg) => {
    if (msg.type === "START_SCAN" || msg.type === "REFRESH_SCAN") {
      processPage();
    }
  });

  setTimeout(processPage, 1500);
})();
