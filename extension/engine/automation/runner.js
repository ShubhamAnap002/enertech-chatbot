import { evaluateLead } from "../rules/engine.js";

const processed = new Set();

export function resetProcessed() {
  processed.clear();
}

export function decide(lead, config, runtime) {
  if (processed.has(lead.raw_text_hash || lead.lead_id)) {
    return { decision: "SKIP", score: 0, reasons: ["Duplicate lead"], rule_results: { duplicate: true } };
  }
  const result = evaluateLead(lead, config, runtime);
  processed.add(lead.raw_text_hash || lead.lead_id);
  return result;
}
