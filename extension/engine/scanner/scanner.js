import { findLeadContainers, queryFirst, SELECTORS } from "./adapters.js";

function textOf(el) {
  return (el?.textContent || "").replace(/\s+/g, " ").trim();
}

function hashText(s) {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return (h >>> 0).toString(16);
}

function parseQuantity(raw) {
  if (!raw) return { quantity: null, unit: null };
  const m = raw.match(/(\d+(?:\.\d+)?)\s*([A-Za-z]+)?/);
  if (!m) return { quantity: null, unit: null };
  return { quantity: Number(m[1]), unit: m[2] || "Piece" };
}

function parseCapacity(raw) {
  if (!raw) return { capacity: null, capacity_unit: null };
  const m = raw.match(/(\d+(?:\.\d+)?)\s*(kVA|KVA|kw|KW|hp|HP)?/i);
  if (!m) return { capacity: null, capacity_unit: null };
  return { capacity: Number(m[1]), capacity_unit: m[2] || "kVA" };
}

/**
 * Extract visible lead fields only. Do not invent missing data.
 * If structure cannot be identified confidently, return [].
 */
export function scanLeads(doc = document) {
  const cards = findLeadContainers(doc);
  if (!cards.length) return { ok: false, reason: "unsupported_page_or_dom", leads: [] };

  const leads = [];
  for (const card of cards) {
    const titleEl = queryFirst(card, SELECTORS.title);
    const title = textOf(titleEl);
    if (!title) continue;
    const qtyRaw = textOf(queryFirst(card, SELECTORS.quantity));
    const capRaw = textOf(queryFirst(card, SELECTORS.capacity));
    const location = textOf(queryFirst(card, SELECTORS.location));
    const { quantity, unit } = parseQuantity(qtyRaw);
    const { capacity, capacity_unit } = parseCapacity(capRaw || title);
    const raw = `${title}|${qtyRaw}|${capRaw}|${location}`;
    const raw_text_hash = hashText(raw);
    const lead_id = card.getAttribute("data-lead-id") || raw_text_hash;
    leads.push({
      lead_id,
      title,
      quantity,
      unit,
      capacity,
      capacity_unit,
      location: location || null,
      raw_text_hash,
      element: card,
    });
  }
  return { ok: true, leads };
}
