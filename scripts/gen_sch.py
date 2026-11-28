"""Write the hierarchical schematic from design.py: a root sheet with one sheet per block.
Every pin gets a global label with its net name; no wires. Run from the repo root:
    python3 scripts/gen_sch.py
"""
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(__file__))
from sexpr import parse, dump  # noqa: E402
import design  # noqa: E402

PROJECT = "chilichip-console"
NS = uuid.UUID("0f3b2a52-5d0e-4a51-a5e8-3c8d2f6b7a10")
ROOT = str(uuid.uuid5(NS, "root"))
DATE = "2026-11-27"
REV = "v0.1.0"
STOCK = "/usr/share/kicad/symbols/"
G = 1.27
_libs = {}


def uid(*k):
    return f'"{uuid.uuid5(NS, "/".join(k))}"'


def snap(v):
    return round(round(v / G) * G, 2)


def libsym(lib_id):
    lib, name = lib_id.split(":")
    path = f"{design.LOCAL}.kicad_sym" if lib == design.LOCAL else STOCK + lib + ".kicad_sym"
    if path not in _libs:
        _libs[path] = parse(open(path).read())
    for e in _libs[path]:
        if isinstance(e, list) and e[0] == "symbol" and e[1] == f'"{name}"':
            if any(isinstance(a, list) and a[0] == "extends" for a in e):
                raise SystemExit(f"{lib_id} extends another symbol; use the parent")
            s = [x for x in e]
            s[1] = f'"{lib_id}"'
            return s
    raise SystemExit(f"no symbol {lib_id}")


def pins(sym):
    """{number: (x, y, angle)}; for stacked pins only the first one at a spot."""
    out, seen = {}, {}
    def walk(x):
        for e in x:
            if isinstance(e, list):
                if e[0] == "pin":
                    at = next(a for a in e if isinstance(a, list) and a[0] == "at")
                    num = next(a for a in e if isinstance(a, list) and a[0] == "number")[1].strip('"')
                    key = (at[1], at[2])
                    out[num] = (float(at[1]), float(at[2]), float(at[3]), key in seen)
                    seen.setdefault(key, num)
                else:
                    walk(e)
    walk(sym)
    return out


def prop(name, val, x, y, hide=False, just=None):
    eff = ["effects", ["font", ["size", "1.27", "1.27"]]]
    if just:
        eff.append(["justify", just])
    if hide:
        eff.append(["hide", "yes"])
    return ["property", f'"{name}"', f'"{val}"', ["at", f"{x:g}", f"{y:g}", "0"], eff]


def label_len(net):
    return 1.0 * len(net) + 3.0


def footprint_box(pp, nets):
    """Extent of the symbol plus its labels, relative to the symbol origin (sheet coords, y down)."""
    x0 = y0 = 1e9
    x1 = y1 = -1e9
    for num, (px, py, ang, _) in pp.items():
        x, y = px, -py
        n = nets.get(num)
        ll = label_len(n) if n else 1.5
        a = int(ang)
        ex = {0: x - ll, 180: x + ll}.get(a, x)
        ey = {90: y + ll, 270: y - ll}.get(a, y)
        x0, x1 = min(x0, x, ex), max(x1, x, ex)
        y0, y1 = min(y0, y, ey), max(y1, y, ey)
    return x0 - 4, y0 - 6, x1 + 4, y1 + 6


def sheet(key, title, parts, page):
    sheet_uuid = str(uuid.uuid5(NS, "sheet/" + key))
    path = f"/{ROOT}/{sheet_uuid}"
    libsyms, used, items = [], set(), []
    boxes = []
    for p in parts:
        sym = libsym(p[1])
        if p[1] not in used:
            used.add(p[1])
            libsyms.append(sym)
        boxes.append((p, sym, pins(sym)))
    # row packing on a 1.27 mm grid
    for paper, (W, H) in (("A3", (420, 297)), ("A2", (594, 420)), ("A1", (841, 594))):
        x, y, row_h, placed, ok = 15.0, 25.0, 0.0, [], True
        for p, sym, pp in boxes:
            bx0, by0, bx1, by1 = footprint_box(pp, p[5])
            w, h = bx1 - bx0, by1 - by0
            if x + w > W - 15:
                x, y, row_h = 15.0, y + row_h + 5, 0.0
            if y + h > H - 45:
                ok = False
                break
            placed.append((p, sym, pp, snap(x - bx0), snap(y - by0)))
            x += w + 5
            row_h = max(row_h, h)
        if ok:
            break
    for (ref, lib_id, val, fp, lcsc, nets), sym, pp, sx, sy in placed:
        power = ref.startswith("#")
        inst = ["symbol", ["lib_id", f'"{lib_id}"'], ["at", f"{sx:g}", f"{sy:g}", "0"], ["unit", "1"],
                ["exclude_from_sim", "no"], ["in_bom", "no" if power or ref.startswith("TP") or ref in design.NO_BOM else "yes"],
                ["on_board", "no" if power else "yes"], ["dnp", "no"], ["uuid", uid(key, ref)],
                prop("Reference", ref, sx, sy - 3.81, power), prop("Value", val, sx, sy + 3.81),
                prop("Footprint", fp, sx, sy, True), prop("Datasheet", "", sx, sy, True),
                prop("Description", "", sx, sy, True)]
        if not power:
            inst.append(prop("LCSC", lcsc, sx, sy, True))
        for num in pp:
            inst.append(["pin", f'"{num}"', ["uuid", uid(key, ref, "pin", num)]])
        inst.append(["instances", ["project", f'"{PROJECT}"', ["path", f'"{path}"', ["reference", f'"{ref}"'], ["unit", "1"]]]])
        items.append(inst)
        for num, (px, py, ang, stacked) in pp.items():
            if num not in nets:
                raise SystemExit(f"{ref} pin {num} has no net")
            if stacked:
                continue
            net = nets[num]
            cx, cy = round(sx + px, 2), round(sy - py, 2)
            if net is None:
                items.append(["no_connect", ["at", f"{cx:g}", f"{cy:g}"], ["uuid", uid(key, ref, "nc", num)]])
                continue
            rot = {0: 180, 180: 0, 90: 270, 270: 90}[int(ang)]
            just = "right" if rot in (180, 270) else "left"
            items.append(["global_label", f'"{net}"', ["shape", "passive"], ["at", f"{cx:g}", f"{cy:g}", str(rot)],
                          ["fields_autoplaced", "yes"],
                          ["effects", ["font", ["size", "1.27", "1.27"]], ["justify", just]],
                          ["uuid", uid(key, ref, "lbl", num)]])
    doc = ["kicad_sch", ["version", "20260306"], ["generator", '"eeschema"'], ["generator_version", '"10.0"'],
           ["uuid", f'"{sheet_uuid}"'], ["paper", f'"{paper}"'],
           ["title_block", ["title", f'"CHILICHIP CONSOLE BOARD: {title}"'], ["date", f'"{DATE}"'], ["rev", f'"{REV}"'],
            ["company", '"chilichip"'], ["comment", "1", '"Generated by scripts/gen_sch.py from scripts/design.py"']],
           ["lib_symbols"] + libsyms] + items + [["embedded_fonts", "no"]]
    open(f"{key}.kicad_sch", "w").write(dump(doc) + "\n")
    return sheet_uuid, paper


def main():
    flags = [(f"#FLG{i + 1:02d}", "power:PWR_FLAG", "PWR_FLAG", "", "", {"1": n}) for i, n in enumerate(design.FLAGS)]
    sheets = list(design.SHEETS)
    k, name, title, parts = sheets[1]
    sheets[1] = (k, name, title, parts + flags)
    root_items = []
    for i, (key, name, title, parts) in enumerate(sheets):
        su, paper = sheet(key, title, parts, i + 2)
        x, y = 25.4 + (i % 4) * 63.5, 50.8 + (i // 4) * 50.8
        root_items.append(["sheet", ["at", f"{x:g}", f"{y:g}"], ["size", "50.8", "25.4"], ["exclude_from_sim", "no"],
                           ["in_bom", "yes"], ["on_board", "yes"], ["dnp", "no"], ["fields_autoplaced", "yes"],
                           ["stroke", ["width", "0.1524"], ["type", "solid"]], ["fill", ["color", "0", "0", "0", "0.0000"]],
                           ["uuid", f'"{su}"'],
                           ["property", '"Sheetname"', f'"{name}"', ["at", f"{x:g}", f"{y - 0.71:g}", "0"],
                            ["effects", ["font", ["size", "1.27", "1.27"]], ["justify", "left", "bottom"]]],
                           ["property", '"Sheetfile"', f'"{key}.kicad_sch"', ["at", f"{x:g}", f"{y + 26.01:g}", "0"],
                            ["effects", ["font", ["size", "1.27", "1.27"]], ["justify", "left", "top"]]],
                           ["instances", ["project", f'"{PROJECT}"', ["path", f'"/{ROOT}"', ["page", f'"{i + 2}"']]]]])
        print(f"{key}: {len(parts)} parts on {paper}")
    note = ("One board with everything the modules had: RP2350A, 16 MB flash, USB-C, LiPo charger, 3.3 V buck-boost, "
            "2.0 inch TFT, I2S amplifier, RM2 radio, IMU, RTC, haptics and GBA rubber-dome buttons. "
            "GPIO map as main board v4.")
    root = ["kicad_sch", ["version", "20260306"], ["generator", '"eeschema"'], ["generator_version", '"10.0"'],
            ["uuid", f'"{ROOT}"'], ["paper", '"A4"'],
            ["title_block", ["title", '"CHILICHIP CONSOLE BOARD"'], ["date", f'"{DATE}"'], ["rev", f'"{REV}"'],
             ["company", '"chilichip"'], ["comment", "1", '"Generated by scripts/gen_sch.py from scripts/design.py"']],
            ["lib_symbols"],
            ["text", f'"{note}"', ["exclude_from_sim", "no"], ["at", "25.4", "30.48", "0"],
             ["effects", ["font", ["size", "1.27", "1.27"]], ["justify", "left", "bottom"]], ["uuid", uid("note")]]
            ] + root_items + [["sheet_instances", ["path", '"/"', ["page", '"1"']]], ["embedded_fonts", "no"]]
    open(f"{PROJECT}.kicad_sch", "w").write(dump(root) + "\n")


main()
