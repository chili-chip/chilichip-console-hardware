"""Add the ground plane and the antenna keep-out, autoroute with Freerouting, then pour ground.
Run from the repo root after gen_pcb.py:
    python3 scripts/route.py path/to/freerouting-1.9.0.jar [passes]
Freerouting: https://github.com/freerouting/freerouting (GPL-3.0, not part of this repo).
"""
import json
import math
import os
import subprocess
import sys

import pcbnew

BOARD = "chilichip-console.kicad_pcb"
OX, OY, W, H = 100.0, 100.0, 50.0, 83.9
# No copper on any layer next to the RM2 antenna (Raspberry Pi RM2 datasheet keep-out), top edge.
ANTENNA = (24.15, 0.0, W, 5.0)
RC = 2.5  # outline corner radius


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


def restore_fanout_vias(b, gnd):
    """The SES import can lose fixed fanout vias: put a via back on every ground stub end left open."""
    net = gnd.GetNetCode()
    tracks = [t for t in b.GetTracks() if t.Type() == pcbnew.PCB_TRACE_T and t.GetNetCode() == net]
    vias = [t.GetPosition() for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T]
    pads = [p for fp in b.GetFootprints() for p in fp.Pads() if p.GetNetCode() == net]
    n = 0
    for t in tracks:
        for e in (t.GetStart(), t.GetEnd()):
            if any(v == e for v in vias) or any(p.HitTest(e) for p in pads):
                continue
            if any(o is not t and o.GetLayer() == t.GetLayer()
                   and pcbnew.SEG(o.GetStart(), o.GetEnd()).Distance(e) <= o.GetWidth() // 2 for o in tracks):
                continue  # joins another ground track
            x, y = pcbnew.ToMM(e.x) - OX, pcbnew.ToMM(e.y) - OY
            if not via_fits(b, x, y, net):
                continue
            add_via(b, x, y, gnd)
            vias.append(e)
            n += 1
    print("restored vias", n)


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


VIA_D, VIA_DRILL, GAP = 0.5, 0.3, 0.2


def via_fits(b, x, y, net, skip=None):
    """True when a GND via at board position (x, y) mm clears every other copper item on all layers."""
    p = pcbnew.VECTOR2I(mm(OX + x), mm(OY + y))
    r = VIA_D / 2 + GAP
    ax0, _, ax1, ay1 = ANTENNA
    if ax0 - r < x < ax1 + r and y < ay1 + r:
        return False
    for t in b.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T:
            if (t.GetPosition() - p).EuclideanNorm() < mm(VIA_D + GAP):
                return False
        elif t.GetNetCode() != net:
            seg = pcbnew.SEG(t.GetStart(), t.GetEnd())
            if pcbnew.ToMM(seg.Distance(p)) < r + pcbnew.ToMM(t.GetWidth()) / 2:
                return False
    for fp in b.GetFootprints():
        # no vias under the USB shell (tented ground vias under the radio module body are fine)
        if fp.GetReference() == "J1" and fp.GetCourtyard(fp.GetSide() and pcbnew.B_CrtYd or pcbnew.F_CrtYd).Collide(p, mm(r)):
            return False
        for pad in fp.Pads():
            if pad is not skip and pad.HitTest(p, mm(r)):
                return False
    return True


def stitch(b, gnd, pitch=2.5):
    """Tie the ground pours together: a GND via on a grid wherever one fits, kept off the edge and antenna."""
    net = gnd.GetNetCode()
    n = 0
    y = 1.5
    while y < H - 1.4:
        x = 1.5
        while x < W - 1.4:
            cx, cy = min(max(x, RC), W - RC), min(max(y, RC), H - RC)  # nearest corner arc centre
            corner = (x - cx) ** 2 + (y - cy) ** 2 > (RC - 1.4) ** 2
            if not corner and via_fits(b, x, y, net):
                add_via(b, x, y, gnd)
                n += 1
            x += pitch
        y += pitch
    print("stitching vias", n)


def stitch_islands(b, gnd, step=0.25):
    """Give every ground pour island without a via one, so it joins the In1 plane."""
    net = gnd.GetNetCode()
    vias = [t.GetPosition() for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T and t.GetNetCode() == net]
    added = 0
    for z in b.Zones():
        if z.GetIsRuleArea() or z.GetNetCode() != net or z.GetLayer() == pcbnew.In1_Cu:
            continue
        polys = z.GetFilledPolysList(z.GetLayer())
        for i in range(polys.OutlineCount()):
            island = pcbnew.SHAPE_POLY_SET(); island.AddOutline(polys.Outline(i))
            for h in range(polys.HoleCount(i)):
                island.AddHole(polys.CHole(i, h))
            if any(island.Contains(v) for v in vias):
                continue
            box = polys.Outline(i).BBox()
            spot = None
            y = pcbnew.ToMM(box.GetTop()) - OY
            while spot is None and y <= pcbnew.ToMM(box.GetBottom()) - OY:
                x = pcbnew.ToMM(box.GetLeft()) - OX
                while x <= pcbnew.ToMM(box.GetRight()) - OX:
                    p = pcbnew.VECTOR2I(mm(OX + x), mm(OY + y))
                    ring = [pcbnew.VECTOR2I(p.x + mm(dx), p.y + mm(dy))
                            for dx, dy in [(0, 0), (0.2, 0), (-0.2, 0), (0, 0.2), (0, -0.2)]]
                    if all(island.Contains(q) for q in ring) and via_fits(b, x, y, net):
                        spot = (x, y)
                        break
                    x += step
                y += step
            if spot:
                add_via(b, *spot, gnd)
                vias.append(pcbnew.VECTOR2I(mm(OX + spot[0]), mm(OY + spot[1])))
                added += 1
    print("island vias", added)
    return added


def unconnected_gnd_pads(b):
    """GND pads that the DRC still lists as unconnected."""
    out = "/tmp/console-drc.json"
    subprocess.run(["kicad-cli", "pcb", "drc", "--format", "json", "-o", out, BOARD], check=True, capture_output=True)
    want = set()
    with open(out) as f:
        report = json.load(f)
    for u in report["unconnected_items"]:
        for item in u["items"]:
            d = item["description"]
            if d.startswith("Pad ") and "[GND]" in d:
                want.add((d.split(" of ")[1].split()[0], d.split()[1]))
    return [pad for fp in b.GetFootprints() for pad in fp.Pads()
            if (fp.GetReference(), pad.GetNumber()) in want and pad.GetNetname() == "GND"]


def seg_fits(b, layer, a, c, width, net):
    """True when a track from a to c on layer clears all other-net copper by GAP."""
    seg = pcbnew.SHAPE_SEGMENT(a, c, mm(width))
    for t in b.GetTracks():
        if t.GetNetCode() != net and t.IsOnLayer(layer) and t.GetEffectiveShape(layer).Collide(seg, mm(GAP)):
            return False
    for fp in b.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNetCode() != net and pad.IsOnLayer(layer) and pad.GetEffectiveShape(layer).Collide(seg, mm(GAP)):
                return False
    return True


def tied_fill(b, net, layer):
    """The ground pour islands on layer that hold a via, so they reach the In1 plane."""
    vias = [t.GetPosition() for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T and t.GetNetCode() == net]
    out = pcbnew.SHAPE_POLY_SET()
    for z in b.Zones():
        if z.GetIsRuleArea() or z.GetNetCode() != net or not z.IsOnLayer(layer):
            continue
        polys = z.GetFilledPolysList(layer)
        for i in range(polys.OutlineCount()):
            island = pcbnew.SHAPE_POLY_SET(); island.AddOutline(polys.Outline(i))
            for h in range(polys.HoleCount(i)):
                island.AddHole(polys.CHole(i, h))
            if any(island.Contains(v) for v in vias):
                out.Append(island)
    return out


def fanout(b, gnd):
    """Before routing: a short track and via from every ground SMD pad down to the In1 plane."""
    net, n = gnd.GetNetCode(), 0
    vias = [t for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T and t.GetNetCode() == net]
    for fp in b.GetFootprints():
        done = []
        for pad in fp.Pads():
            if pad.GetNetCode() != net or pad.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
                continue
            if any(pad.HitTest(v.GetPosition()) for v in vias):
                continue  # thermal vias already
            size = pad.GetSize(pcbnew.F_Cu)
            if min(size.x, size.y) < mm(0.3):
                continue  # fine-pitch pins: the autorouter does better with these
            layer = pcbnew.F_Cu if pad.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu
            if any(d.GetEffectiveShape(layer).Collide(pad.GetEffectiveShape(layer)) for d in done):
                continue  # overlaps a pad that already has its via (stacked pads of one contact)
            if connect_pad(b, pad, gnd, via_only=True):
                done.append(pad)
                n += 1
    print("fanout vias", n)


def connect_pad(b, pad, gnd, via_only=False):
    """Tie a ground pad the pour could not reach: a short track to the nearest via spot or tied pour."""
    net, c = gnd.GetNetCode(), pad.GetPosition()
    layer = pcbnew.F_Cu if pad.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu
    fill = pcbnew.SHAPE_POLY_SET() if via_only else tied_fill(b, net, layer)
    vias = [t.GetPosition() for t in b.GetTracks() if t.Type() == pcbnew.PCB_VIA_T and t.GetNetCode() == net]
    size = pad.GetSize(layer)
    width = min(0.25, pcbnew.ToMM(min(size.x, size.y)) - 0.02)  # fine-pitch pins get a thinner stub
    for r in [0.4 + 0.2 * i for i in range(15)]:
        for k in range(24):
            a = 2 * math.pi * k / 24
            x = pcbnew.ToMM(c.x) - OX + r * math.cos(a)
            y = pcbnew.ToMM(c.y) - OY + r * math.sin(a)
            v = pcbnew.VECTOR2I(mm(OX + x), mm(OY + y))
            if not (0.8 < x < W - 0.8 and 0.8 < y < H - 0.8) or pad.HitTest(v, mm(0.3)):
                continue
            if not seg_fits(b, layer, c, v, width, net):
                continue
            # end on another ground pad, inside a tied pour (0.3 mm deep), or on a new via
            if any(o is not pad and o.GetNetCode() == net and o.IsOnLayer(layer) and o.HitTest(v)
                   and (not via_only or any(o.HitTest(w) for w in vias))  # before routing: only a pad with vias
                   for o in pad.GetParentFootprint().Pads()) or not via_only and all(fill.Contains(pcbnew.VECTOR2I(v.x + mm(dx), v.y + mm(dy)))
                   for dx, dy in [(0, 0), (0.3, 0), (-0.3, 0), (0, 0.3), (0, -0.3)]):
                via = False
            elif via_fits(b, x, y, net, skip=pad):
                via = True
            else:
                continue
            t = pcbnew.PCB_TRACK(b)
            t.SetStart(c); t.SetEnd(v); t.SetWidth(mm(width)); t.SetLayer(layer); t.SetNet(gnd); t.SetLocked(True)
            b.Add(t)
            if via:
                add_via(b, x, y, gnd)
            return 1
    print("no room next to", pad.GetParentFootprint().GetReference(), pad.GetNumber())
    return 0


def via_spots(b, pad, width, limit=8):
    """Via spots near a pad that a short stub on the pad's layer can reach."""
    net, c = pad.GetNetCode(), pad.GetPosition()
    layer = pcbnew.F_Cu if pad.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu
    size = pad.GetSize(layer)
    width = min(width, pcbnew.ToMM(min(size.x, size.y)) - 0.02)  # thinner stub out of fine-pitch pins
    out = []
    for r in [0.6 + 0.3 * i for i in range(8)]:
        for k in range(16):
            a = 2 * math.pi * k / 16
            x = pcbnew.ToMM(c.x) - OX + r * math.cos(a)
            y = pcbnew.ToMM(c.y) - OY + r * math.sin(a)
            v = pcbnew.VECTOR2I(mm(OX + x), mm(OY + y))
            if (0.8 < x < W - 0.8 and 0.8 < y < H - 0.8 and not pad.HitTest(v, mm(VIA_D / 2))
                    and via_fits(b, x, y, net, skip=pad) and seg_fits(b, layer, c, v, width, net)):
                out.append((x, y, v, layer, width))
                if len(out) >= limit:
                    return out
    return out


def bridge(b, pa, pb, width):
    """Last resort for a connection the autorouter left open: via near each pad, straight track between."""
    net = pa.GetNet()
    for xa, ya, va, la, wa in via_spots(b, pa, width):
        for xb, yb, vb, lb, wb in via_spots(b, pb, width):
            if (va - vb).EuclideanNorm() < mm(VIA_D + GAP):
                continue
            for layer in (pcbnew.In2_Cu, pcbnew.F_Cu, pcbnew.B_Cu):
                if seg_fits(b, layer, va, vb, width, net.GetNetCode()):
                    for s, e, l, w in [(pa.GetPosition(), va, la, wa), (va, vb, layer, width), (pb.GetPosition(), vb, lb, wb)]:
                        t = pcbnew.PCB_TRACK(b)
                        t.SetStart(s); t.SetEnd(e); t.SetWidth(mm(w)); t.SetLayer(l); t.SetNet(net)
                        b.Add(t)
                    for x, y in [(xa, ya), (xb, yb)]:
                        add_via(b, x, y, net)
                    return True
    return False


def add_via(b, x, y, gnd):
    v = pcbnew.PCB_VIA(b)
    v.SetPosition(pcbnew.VECTOR2I(mm(OX + x), mm(OY + y)))
    v.SetWidth(mm(VIA_D)); v.SetDrill(mm(VIA_DRILL)); v.SetNet(gnd); v.SetLocked(True)  # the autorouter keeps it
    b.Add(v)


def prepare(b):
    """Antenna keep-out and the solid In1 ground plane, before export."""
    gnd = b.FindNet("GND")
    fanout(b, gnd)
    rect_zone(b, [pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu], *ANTENNA, keepout=True)
    rect_zone(b, [pcbnew.In1_Cu], 0, 0, W, H, net=gnd)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())


def main(jar, passes="30"):
    """Expects a fresh board from gen_pcb.py (no zones, no tracks)."""
    b = pcbnew.LoadBoard(BOARD)
    prepare(b)
    pcbnew.SaveBoard(BOARD, b)
    b = pcbnew.LoadBoard(BOARD)
    dsn, ses = BOARD[:-10] + ".dsn", BOARD[:-10] + ".ses"
    assert pcbnew.ExportSpecctraDSN(b, dsn)
    # Freerouting 1.9 opens a window even in batch mode, so give it a virtual display.
    cmd = ["java", "-jar", jar, "-de", dsn, "-do", ses, "-mp", passes]
    if not os.environ.get("DISPLAY"):
        cmd = ["xvfb-run", "-a"] + cmd
    subprocess.run(cmd, check=True, timeout=3600)
    finish(b, ses)
    os.remove(dsn); os.remove(ses)


def finish(b, ses):
    """Import the routed SES, tidy it and pour ground on the other layers."""
    assert pcbnew.ImportSpecctraSES(b, ses)
    gnd = b.FindNet("GND")
    restore_fanout_vias(b, gnd)
    drop_dangling(b)
    for layer in (pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu):
        rect_zone(b, [layer], 0, 0, W, H, net=gnd)
    stitch(b, gnd)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    for _ in range(3):
        if not stitch_islands(b, gnd):
            break
        pcbnew.ZONE_FILLER(b).Fill(b.Zones())
    pcbnew.SaveBoard(BOARD, b)
    for _ in range(3):  # ground pads the pours could not reach get their own via
        pads = unconnected_gnd_pads(b)
        if not pads or not sum(connect_pad(b, pad, gnd) for pad in pads):
            break
        pcbnew.ZONE_FILLER(b).Fill(b.Zones())
        pcbnew.SaveBoard(BOARD, b)
    print("tracks", len(b.GetTracks()))


if __name__ == "__main__":
    main(*sys.argv[1:])
