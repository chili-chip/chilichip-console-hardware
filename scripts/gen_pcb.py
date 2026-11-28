"""Build the unrouted board from the schematic netlist and the placement below.
Run from the repo root after gen_sch.py:
    kicad-cli sch export netlist --format kicadsexpr -o /tmp/console.net chilichip-console.kicad_sch
    python3 scripts/gen_pcb.py /tmp/console.net
Coordinates are front-view mm from the board's top-left corner (x right, y down).
Back-side parts are given in the same front-view coordinates.
"""
import os
import sys

import pcbnew

sys.path.insert(0, os.path.dirname(__file__))
from sexpr import parse  # noqa: E402
from design import NO_BOM  # noqa: E402

OUT = "chilichip-console.kicad_pcb"
OX, OY = 100.0, 100.0
W, H, RC = 50.0, 83.9, 2.5          # same outline as main board v4 (vgc-zero-hardware PR #49)
STOCK = "/usr/share/kicad/footprints/"
LOCAL = "chilichip-console"

# ref: (x, y, rotation, side)
PLACE = {
    # --- front, under the 2.0" panel (panel 47.8 x 34.6 mm, x 1.1-48.9, y 5.7-40.3 in the casing). Parts here stay under 2.5 mm.
    # The panel's FPC tail folds back under the panel from its left edge into J3: keep x 0-14, y 12-23 clear.
    "J3": (15.55, 17.5, 270, "F"),
    "C30": (19.0, 9.3, 90, "F"), "C31": (21.0, 9.3, 90, "F"),
    "R30": (8.0, 28.0, 0, "F"), "Q2": (8.0, 31.5, 90, "F"), "R31": (11.0, 31.5, 90, "F"),
    "U1": (30.0, 19.0, 180, "F"),
    "U2": (33.0, 31.5, 0, "F"), "C1": (27.5, 33.5, 90, "F"), "R1": (27.5, 31.0, 90, "F"),
    "Y1": (31.0, 10.5, 0, "F"), "R2": (34.5, 10.0, 0, "F"), "C2": (27.8, 10.0, 90, "F"), "C3": (34.5, 11.6, 0, "F"),
    "L1": (25.5, 25.5, 90, "F"), "R3": (23.5, 23.0, 90, "F"), "C4": (23.5, 25.8, 90, "F"),
    "C5": (27.0, 28.0, 90, "F"), "C6": (23.5, 28.5, 90, "F"), "C7": (25.0, 28.5, 90, "F"),
    "C8": (34.8, 14.0, 0, "F"), "C9": (25.0, 14.0, 0, "F"),
    "C10": (24.5, 17.0, 90, "F"), "C11": (24.5, 20.0, 90, "F"), "C12": (35.5, 17.0, 90, "F"),
    "C13": (35.5, 20.0, 90, "F"), "C14": (35.5, 23.0, 90, "F"), "C15": (28.0, 14.0, 0, "F"), "C16": (32.0, 14.0, 0, "F"),
    "C17": (21.5, 20.0, 90, "F"),
    "R4": (29.5, 25.0, 90, "F"), "R5": (31.0, 25.0, 90, "F"),
    "U8": (42.5, 30.0, 0, "F"), "C60": (45.5, 29.0, 90, "F"), "C61": (45.5, 31.0, 90, "F"),
    "U9": (42.5, 24.0, 0, "F"), "C62": (45.5, 23.0, 90, "F"), "C63": (45.5, 25.0, 90, "F"), "R60": (39.5, 24.0, 90, "F"),
    "U10": (42.5, 35.5, 0, "F"), "C64": (38.5, 35.5, 90, "F"), "C65": (46.5, 35.0, 90, "F"), "C66": (47.2, 33.0, 90, "F"),
    "R61": (39.0, 28.0, 90, "F"), "R62": (39.0, 30.5, 90, "F"), "R63": (39.0, 33.0, 0, "F"),
    "D1": (8.0, 2.0, 0, "F"),  # charge LED above the panel, under a 1.6 mm light pipe in the shell, clear of the screw boss at (2.5, 2.5)
    # --- front, buttons (centres from the buttons module, same as the casing model)
    "SW10": (12.75, 65.1, 0, "F"), "SW11": (31.3, 72.0, 0, "F"), "SW12": (31.3, 56.5, 0, "F"), "SW13": (21.0, 46.1, 0, "F"),
    # --- back. Battery 502540 at x 1.8-41.8, y 58.2-83.2: nothing under it.
    "J1": (18.3, 4.8, 0, "B"), "R10": (11.5, 6.5, 90, "B"), "R11": (25.0, 7.0, 90, "B"),
    "U3": (18.3, 12.0, 0, "B"), "C20": (12.0, 11.0, 90, "B"),
    "U4": (8.0, 10.0, 0, "B"), "R12": (8.0, 13.5, 0, "B"), "C21": (4.0, 10.0, 90, "B"), "R13": (6.0, 4.0, 0, "B"),
    "D2": (9.0, 17.5, 0, "B"), "Q1": (15.0, 17.0, 0, "B"), "R14": (15.0, 14.0, 0, "B"),
    "U5": (8.0, 25.0, 0, "B"), "L2": (8.0, 29.0, 0, "B"), "C22": (4.0, 24.5, 90, "B"), "C23": (4.0, 27.5, 90, "B"),
    "C24": (12.0, 24.0, 90, "B"), "C25": (12.0, 27.5, 90, "B"),
    "R15": (22.0, 22.0, 90, "B"), "R16": (20.5, 22.0, 90, "B"), "R17": (22.0, 26.0, 90, "B"), "R18": (20.5, 26.0, 90, "B"),
    "U7": (41.9, 8.25, 180, "B"), "R50": (38.0, 19.5, 90, "B"), "R51": (39.5, 19.5, 90, "B"),
    "C50": (44.0, 19.5, 90, "B"), "C51": (46.0, 19.5, 90, "B"),
    "U6": (42.0, 45.0, 0, "B"), "R40": (38.0, 45.0, 90, "B"), "C40": (45.5, 44.0, 90, "B"), "C41": (45.5, 46.5, 90, "B"),
    "J4": (44.5, 51.0, 0, "B"),
    "J2": (46.5, 62.0, 90, "B"),
    "M1": (46.0, 74.5, 0, "B"),
    "SW1": (8.0, 42.0, 0, "B"), "SW2": (15.5, 42.0, 0, "B"), "R6": (11.8, 38.5, 0, "B"), "R7": (15.5, 46.0, 0, "B"),
    # probe pads in two rows above the battery
    "TP6": (5.5, 49.0, 0, "B"), "TP1": (9.5, 49.0, 0, "B"), "TP2": (13.5, 49.0, 0, "B"), "TP3": (17.5, 49.0, 0, "B"),
    "TP4": (21.5, 49.0, 0, "B"), "TP7": (5.5, 53.5, 0, "B"), "TP8": (9.5, 53.5, 0, "B"), "TP9": (13.5, 53.5, 0, "B"),
    "TP10": (17.5, 53.5, 0, "B"), "TP11": (21.5, 53.5, 0, "B"), "TP5": (25.5, 53.5, 0, "B"),
}
BATTERY = (21.8, 70.7, 180, "B")
SILK_REFS = {"J1", "J2", "J4", "SW1", "SW2", "U7"}


def mm(v):
    return pcbnew.FromMM(v)


def pt(x, y):
    return pcbnew.VECTOR2I(mm(OX + x), mm(OY + y))


def netlist(path):
    t = parse(open(path).read())
    find = lambda x, k: [e for e in x if isinstance(e, list) and e and e[0] == k]  # noqa: E731
    comps = {}
    for comp in find(find(t, "components")[0], "comp"):
        g = lambda k: find(comp, k)[0][1].strip('"')  # noqa: E731
        sp = find(comp, "sheetpath")[0]
        tst = find(sp, "tstamps")[0][1].strip('"')
        lcsc = ""
        for f in find((find(comp, "fields") or [[]])[0], "field"):
            if f[1][1] == '"LCSC"' and len(f) > 2:
                lcsc = f[2].strip('"')
        comps[g("ref")] = dict(value=g("value"), footprint=g("footprint"), path=tst + find(comp, "tstamps")[0][1].strip('"'),
                               lcsc=lcsc, nets={})
    for n in find(find(t, "nets")[0], "net"):
        name = find(n, "name")[0][1].strip('"')
        for nd in find(n, "node"):
            d = {e[0]: e[1].strip('"') for e in nd[1:]}
            comps[d["ref"]]["nets"][d["pin"]] = name
    return comps


def load(fpid):
    lib, name = fpid.split(":")
    path = f"{LOCAL}.pretty" if lib == LOCAL else STOCK + lib + ".pretty"
    fp = pcbnew.FootprintLoad(path, name)
    if fp is None:
        raise SystemExit(f"no footprint {fpid}")
    fp.SetFPIDAsString(fpid)
    return fp


def place(fp, x, y, rot, side):
    if side == "B":
        fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    fp.SetOrientationDegrees(rot)
    fp.SetPosition(pt(x, y))


def outline(board):
    def seg(a, b):
        s = pcbnew.PCB_SHAPE(board); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(pcbnew.Edge_Cuts)
        s.SetStart(pt(*a)); s.SetEnd(pt(*b)); s.SetWidth(mm(0.1)); board.Add(s)

    def arc(c, a, b):
        s = pcbnew.PCB_SHAPE(board); s.SetShape(pcbnew.SHAPE_T_ARC); s.SetLayer(pcbnew.Edge_Cuts)
        s.SetCenter(pt(*c)); s.SetStart(pt(*a)); s.SetArcAngleAndEnd(pcbnew.EDA_ANGLE(90, pcbnew.DEGREES_T))
        s.SetWidth(mm(0.1)); board.Add(s)
    r = RC
    seg((r, 0), (W - r, 0)); seg((W, r), (W, H - r)); seg((W - r, H), (r, H)); seg((0, H - r), (0, r))
    arc((W - r, r), (W - r, 0), None); arc((W - r, H - r), (W, H - r), None)
    arc((r, H - r), (r, H), None); arc((r, r), (0, r), None)


def main(net_path):
    comps = netlist(net_path)
    board = pcbnew.BOARD()
    board.SetCopperLayerCount(4)
    board.SetLayerType(pcbnew.In1_Cu, pcbnew.LT_POWER)
    board.SetLayerName(pcbnew.In1_Cu, "In1.Cu")
    nets = {}

    def net(n):
        if n not in nets:
            ni = pcbnew.NETINFO_ITEM(board, n); board.Add(ni); nets[n] = ni
        return nets[n]

    outline(board)
    missing = set(comps) - set(PLACE)
    if missing:
        raise SystemExit(f"no placement for {sorted(missing)}")
    for ref, c in sorted(comps.items()):
        fp = load(c["footprint"])
        fp.SetReference(ref); fp.SetValue(c["value"])
        fp.Value().SetVisible(False)
        fp.SetPath(pcbnew.KIID_PATH(c["path"]))
        fp.SetField("LCSC", c["lcsc"]); fp.GetField("LCSC").SetVisible(False)
        for field in ("Description", "Datasheet"):  # the schematic leaves these empty
            if fp.HasField(field):
                fp.GetField(field).SetText("")
        if ref == "U7":  # the stock footprint has no 3D model
            fp.Models().clear()
            m = pcbnew.FP_3DMODEL(); m.m_Filename = "${KIPRJMOD}/3d-models/rpi_rmc20452t.step"; fp.Models().append(m)
        if ref in NO_BOM or ref.startswith("TP"):
            fp.SetExcludedFromBOM(True); fp.SetExcludedFromPosFiles(True)
        board.Add(fp)
        for pad in fp.Pads():
            n = c["nets"].get(pad.GetNumber())
            if n:
                pad.SetNet(net(n))
        place(fp, *PLACE[ref])
        back = PLACE[ref][3] == "B"
        ref_txt = fp.Reference()
        if ref in SILK_REFS:  # parts people look for when building or testing: reference on the silkscreen
            ref_txt.SetTextSize(pcbnew.VECTOR2I(mm(0.8), mm(0.8))); ref_txt.SetTextThickness(mm(0.15))
        else:  # the board is dense: other references go on the assembly (fab) layer only
            ref_txt.SetLayer(pcbnew.B_Fab if back else pcbnew.F_Fab)
            ref_txt.SetTextSize(pcbnew.VECTOR2I(mm(0.5), mm(0.5))); ref_txt.SetTextThickness(mm(0.08))
        if ref.startswith("TP"):  # probe pads: net name on the silkscreen
            v = fp.Value(); v.SetVisible(True)
            v.SetLayer(pcbnew.B_SilkS); v.SetTextSize(pcbnew.VECTOR2I(mm(0.8), mm(0.8))); v.SetTextThickness(mm(0.15))
            v.SetPosition(pt(PLACE[ref][0], PLACE[ref][1] + 1.5))
            ref_txt.SetVisible(False)
    bat = load(f"{LOCAL}:LiPo_502540")
    bat.SetReference("BT1"); bat.SetValue("502540")
    bat.SetBoardOnly(True); bat.SetExcludedFromBOM(True); bat.SetExcludedFromPosFiles(True)
    board.Add(bat); place(bat, *BATTERY)

    ds = board.GetDesignSettings()
    ds.m_CopperEdgeClearance = mm(0.3)
    ds.m_TrackMinWidth = mm(0.127)
    ds.m_MinClearance = mm(0.127)
    ds.m_ViasMinSize = mm(0.45)
    ds.m_MinThroughDrill = mm(0.2)
    pcbnew.SaveBoard(OUT, board)
    print("footprints", len(board.GetFootprints()), "nets", len(nets))


main(sys.argv[1])
