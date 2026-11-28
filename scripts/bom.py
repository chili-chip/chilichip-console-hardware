"""Print the parts list from design.py as a Markdown table (for docs/parts.md).
    python3 scripts/bom.py > /tmp/bom.md
"""
import os
import sys
from collections import OrderedDict

sys.path.insert(0, os.path.dirname(__file__))
import design  # noqa: E402

rows = OrderedDict()
for key, name, title, parts in design.SHEETS:
    for ref, sym, val, fp, lcsc, _ in parts:
        if ref.startswith(("TP", "#")) or ref in design.NO_BOM:
            continue
        k = (name, val, fp.split(":")[1], lcsc)
        rows.setdefault(k, []).append(ref)

print("| Block | Refs | Qty | Value | Footprint | LCSC |")
print("|---|---|---|---|---|---|")
for (name, val, fp, lcsc), refs in rows.items():
    link = f"[{lcsc}](https://www.lcsc.com/product-detail/{lcsc}.html)" if lcsc else "to source"
    print(f"| {name} | {', '.join(refs)} | {len(refs)} | {val} | `{fp}` | {link} |")
