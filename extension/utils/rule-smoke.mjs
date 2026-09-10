// Engyne rule-engine smoke checks (Node)
import assert from "node:assert/strict";
import { evaluateLead } from "../engine/rules/engine.js";

const config = {
  keywords: ["solar", "inverter"],
  restricted_keywords: ["scrap"],
  locations: ["Pune"],
  capacity: { min: 5, max: 50 },
  quantity: { min: null, max: null },
  categories: [],
  require_verified_buyer: false,
  scheduler: { enabled: false, daily_limit: 50, cooldown_seconds: 0 },
  scoring_weights: { keyword: 30, location: 20, capacity: 20, quantity: 10, category: 10, verified: 10 },
};

const buy = evaluateLead(
  { title: "Solar Hybrid Inverter 10 kVA", location: "Pune", capacity: 10, quantity: 2 },
  config,
);
assert.equal(buy.decision, "BUY");
assert.ok(buy.score >= 40);

const skipRestricted = evaluateLead(
  { title: "Scrap inverter", location: "Pune", capacity: 10 },
  config,
);
assert.equal(skipRestricted.decision, "SKIP");

const skipLoc = evaluateLead(
  { title: "Solar Inverter", location: "Delhi", capacity: 10 },
  config,
);
assert.equal(skipLoc.decision, "SKIP");

console.log("extension rule tests ok");
