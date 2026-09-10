from pathlib import Path

p = Path(".env")
for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
    s = line.strip()
    if not s or s.startswith("#"):
        continue
    if "=" not in s:
        print(f"L{i}: INVALID_LINE")
        continue
    k, v = s.split("=", 1)
    v = v.strip().strip('"').strip("'")
    sensitive = any(x in k.upper() for x in ("KEY", "PASSWORD", "SECRET", "URL", "DATABASE", "TOKEN"))
    if not v:
        print(f"L{i}: {k}= EMPTY")
    elif sensitive:
        print(f"L{i}: {k}= filled len={len(v)} prefix={v[:18]!r}")
    else:
        print(f"L{i}: {k}= {v[:60]}")
