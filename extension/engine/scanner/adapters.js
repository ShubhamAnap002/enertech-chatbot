/** IndiaMART DOM adapters — keep selectors localized here. */

export const SELECTORS = {
  leadCard: [
    ".bl-list .bl-list__card",
    ".bl_lstng",
    "[data-lead-id]",
    ".lead-card",
    ".buylead-card",
  ],
  title: [".bl-title", ".title", "h2", "h3", ".prod-name"],
  quantity: [".qty", ".quantity", "[data-qty]"],
  capacity: [".capacity", "[data-capacity]"],
  location: [".loc", ".location", ".city", "[data-location]"],
};

export function queryFirst(root, selectors) {
  for (const sel of selectors) {
    const el = root.querySelector(sel);
    if (el) return el;
  }
  return null;
}

export function findLeadContainers(doc = document) {
  for (const sel of SELECTORS.leadCard) {
    const nodes = Array.from(doc.querySelectorAll(sel));
    if (nodes.length) return nodes;
  }
  return [];
}
