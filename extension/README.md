# Engyne Chrome Extension (Manifest V3)

Load unpacked from this folder in `chrome://extensions`.

## Flow

1. Admin generates setup key.
2. Open popup → enter setup key → Pair.
3. Open Settings → configure rules → **Save Training**.
4. On IndiaMART buy-lead pages, Start automation.
5. BUY/SKIP decisions run locally; events post to backend.

## Notes

- No secrets in the extension.
- Setup key is pairing-only.
- Prefer SKIP when DOM is uncertain.
- Does not store IndiaMART passwords or bypass platform security.
