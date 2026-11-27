"""Add the ground plane and the antenna keep-out, autoroute with Freerouting, then pour ground.
Run from the repo root after gen_pcb.py:
    python3 scripts/route.py path/to/freerouting.jar [passes]
Freerouting: https://github.com/freerouting/freerouting (GPL-3.0, not part of this repo).
"""
import os
import subprocess
import sys

import pcbnew

BOARD = "chilichip-console.kicad_pcb"
OX, OY, W, H = 100.0, 100.0, 50.0, 83.9
# No copper on any layer next to the RM2 antenna (Raspberry Pi RM2 datasheet keep-out), top edge.
ANTENNA = (24.15, 0.0, W, 5.0)


def mm(v):
    return pcbnew.FromMM(v)


def rect_zone(board, layers, x0, y0, x1, y1, net=None, keepout=False, clearance=0.2):
    z = pcbnew.ZONE(board)
    ls = pcbnew.LSET()
    for layer in layers:
        ls.AddLayer(layer)
    z.SetLayerSet(ls)
    if keepout:
        z.SetIsRuleArea(True)
        z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(True); z.SetDoNotAllowPads(False)
        z.SetDoNotAllowZoneFills(True); z.SetDoNotAllowFootprints(False)
        z.SetZoneName("Antenna keep-out")
    else:
        z.SetNet(net)
        z.SetLocalClearance(mm(clearance)); z.SetMinThickness(mm(0.2))
        z.SetThermalReliefGap(mm(0.25)); z.SetThermalReliefSpokeWidth(mm(0.3))
    ol = z.Outline(); ol.NewOutline()
    for x, y in [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]:
        ol.Append(mm(OX + x), mm(OY + y))
    board.Add(z)
    return z


def drop_dangling(b):
    """Remove track pieces with a free end, left over by the SES import."""
    while True:
        anchors = {}
        for fp in b.GetFootprints():
            for pad in fp.Pads():
                anchors.setdefault(pad.GetNetCode(), []).append(pad)
        tracks = [t for t in b.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T]
        vias = [t for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T]
        ends = {}
        for t in tracks:
            for e in (t.GetStart(), t.GetEnd()):
                ends.setdefault((t.GetNetCode(), t.GetLayer(), e.x, e.y), []).append(t)
        dead = []
        for t in tracks:
            for e in (t.GetStart(), t.GetEnd()):
                if len(ends[(t.GetNetCode(), t.GetLayer(), e.x, e.y)]) > 1:
                    continue
                if any(v.GetNetCode() == t.GetNetCode() and v.GetPosition() == e for v in vias):
                    continue
                if any(p.HitTest(e) and p.IsOnLayer(t.GetLayer()) for p in anchors.get(t.GetNetCode(), [])):
                    continue
                if t.GetNetname() == "GND":  # may end on a ground zone
                    continue
                dead.append(t)
                break
        if not dead:
            return
        for t in dead:
            b.Delete(t)


def main(jar, passes="100"):
    b = pcbnew.LoadBoard(BOARD)
    for z in list(b.Zones()):
        b.Remove(z)
    for t in list(b.GetTracks()):
        b.Remove(t)
    gnd = b.FindNet("GND")
    rect_zone(b, [pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu], *ANTENNA, keepout=True)
    rect_zone(b, [pcbnew.In1_Cu], 0, 0, W, H, net=gnd)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(BOARD, b)
    b = pcbnew.LoadBoard(BOARD)
    dsn, ses = BOARD[:-10] + ".dsn", BOARD[:-10] + ".ses"
    assert pcbnew.ExportSpecctraDSN(b, dsn)
    r = subprocess.run(["java", "-Djava.awt.headless=true", "-jar", jar, "-de", dsn, "-do", ses, "-mp", passes,
                        "--gui.enabled=false"], capture_output=True, text=True, timeout=3600)
    print(r.stdout[-3000:], r.stderr[-2000:])
    assert pcbnew.ImportSpecctraSES(b, ses)
    drop_dangling(b)
    for layer in (pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu):
        rect_zone(b, [layer], 0, 0, W, H, net=gnd)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(BOARD, b)
    os.remove(dsn); os.remove(ses)
    print("tracks", len(b.GetTracks()))


main(*sys.argv[1:])
