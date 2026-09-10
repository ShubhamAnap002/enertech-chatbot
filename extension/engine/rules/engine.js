function includesAny(haystack, needles) {
  const h = (haystack || "").toLowerCase();
  return (needles || []).some((n) => n && h.includes(String(n).toLowerCase()));
}

function inRange(value, min, max) {
  if (value == null || Number.isNaN(value)) return null;
  if (min != null && value < min) return false;
  if (max != null && value > max) return false;
  return true;
}

function withinBuyingHours(hours, now = new Date()) {
  if (!hours?.start || !hours?.end) return true;
  const [sh, sm] = hours.start.split(":").map(Number);
  const [eh, em] = hours.end.split(":").map(Number);
  const mins = now.getHours() * 60 + now.getMinutes();
  const start = sh * 60 + sm;
  const end = eh * 60 + em;
  if (start <= end) return mins >= start && mins <= end;
  return mins >= start || mins <= end;
}

/**
 * Deterministic rule pipeline. Prefer SKIP when uncertain.
 */
export function evaluateLead(lead, config, runtime = {}) {
  const rule_results = {};
  const reasons = [];
  const weights = config.scoring_weights || {};
  let score = 0;

  const title = lead.title || "";

  if (includesAny(title, config.restricted_keywords)) {
    rule_results.restricted = { pass: false };
    return {
      decision: "SKIP",
      score: 0,
      reasons: ["Restricted keyword matched"],
      rule_results,
    };
  }
  rule_results.restricted = { pass: true };

  const kwHit = includesAny(title, config.keywords);
  rule_results.keyword = { pass: kwHit };
  if (!kwHit && (config.keywords || []).length) {
    return {
      decision: "SKIP",
      score: 0,
      reasons: ["No keyword match"],
      rule_results,
    };
  }
  if (kwHit) {
    score += weights.keyword ?? 30;
    reasons.push("Keyword matched");
  }

  const locHit =
    !(config.locations || []).length ||
    includesAny(lead.location || "", config.locations);
  rule_results.location = { pass: locHit };
  if (!locHit) {
    return {
      decision: "SKIP",
      score,
      reasons: ["Location not matched"],
      rule_results,
    };
  }
  if ((config.locations || []).length && locHit) {
    score += weights.location ?? 20;
    reasons.push("Location matched");
  }

  if ((config.categories || []).length) {
    const catHit = includesAny(title, config.categories);
    rule_results.category = { pass: catHit };
    if (!catHit) {
      return { decision: "SKIP", score, reasons: ["Category not matched"], rule_results };
    }
    score += weights.category ?? 10;
    reasons.push("Category matched");
  }

  const qtyCheck = inRange(lead.quantity, config.quantity?.min, config.quantity?.max);
  rule_results.quantity = { pass: qtyCheck !== false };
  if (qtyCheck === false) {
    return { decision: "SKIP", score, reasons: ["Quantity out of range"], rule_results };
  }
  if (qtyCheck === true) {
    score += weights.quantity ?? 10;
    reasons.push("Quantity matched");
  }

  const capCheck = inRange(lead.capacity, config.capacity?.min, config.capacity?.max);
  rule_results.capacity = { pass: capCheck !== false };
  if (capCheck === false) {
    return { decision: "SKIP", score, reasons: ["Capacity out of range"], rule_results };
  }
  if (capCheck === true) {
    score += weights.capacity ?? 20;
    reasons.push("Capacity matched");
  }

  if (config.require_verified_buyer && !lead.verified) {
    rule_results.verified = { pass: false };
    return { decision: "SKIP", score, reasons: ["Buyer verification required"], rule_results };
  }
  if (lead.verified) {
    score += weights.verified ?? 10;
    reasons.push("Buyer verified");
    rule_results.verified = { pass: true };
  }

  const sched = config.scheduler || {};
  if (sched.enabled && !withinBuyingHours(sched.buying_hours)) {
    rule_results.scheduler = { pass: false };
    return { decision: "SKIP", score, reasons: ["Outside buying hours"], rule_results };
  }
  rule_results.scheduler = { pass: true };

  const dailyLimit = sched.daily_limit ?? 50;
  if ((runtime.boughtToday || 0) >= dailyLimit) {
    rule_results.daily_limit = { pass: false };
    return { decision: "SKIP", score, reasons: ["Daily buy limit reached"], rule_results };
  }
  rule_results.daily_limit = { pass: true };

  if (runtime.lastBuyAt && sched.cooldown_seconds) {
    const elapsed = (Date.now() - runtime.lastBuyAt) / 1000;
    if (elapsed < sched.cooldown_seconds) {
      rule_results.cooldown = { pass: false };
      return { decision: "SKIP", score, reasons: ["Cooldown active"], rule_results };
    }
  }
  rule_results.cooldown = { pass: true };

  score = Math.min(100, Math.round(score));
  const decision = score >= 40 || kwHit ? "BUY" : "SKIP";
  if (decision === "BUY" && !reasons.length) reasons.push("Passed rule pipeline");
  return { decision, score, reasons, rule_results };
}
