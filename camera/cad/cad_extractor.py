import csv
import math
import sys
import os

# ==========================================================
# DXF UNITS → MM
# ==========================================================
INSUNITS_TO_MM = {
    0: 1.0,
    1: 25.4,
    2: 304.8,
    4: 1.0,
    5: 10.0,
    6: 1000.0
}

# ==========================================================
# BASIC DXF HELPERS
# ==========================================================
def load_dxf(path):
    with open(path, "r", errors="ignore") as f:
        return [l.rstrip() for l in f]

def dxf_pairs(lines):
    i = 0
    while i < len(lines) - 1:
        yield lines[i].strip(), lines[i+1].strip()
        i += 2

# ==========================================================
# DXF PARSER (CIRCLE + LINE + POLYLINE)
# ==========================================================
def parse_dxf(path):
    lines = load_dxf(path)
    tokens = list(dxf_pairs(lines))

    # ---------- Units ----------
    insunits = None
    for i in range(len(tokens)):
        if tokens[i][1] == "$INSUNITS":
            try:
                insunits = int(tokens[i+1][1])
            except:
                pass
            break
    unit_to_mm = INSUNITS_TO_MM.get(insunits, 1.0)

    # ---------- Entity reader ----------
    def read_entity(k):
        ent = {"type": tokens[k][1], "data": {}}
        j = k + 1
        while j < len(tokens) and tokens[j][0] != "0":
            ent["data"].setdefault(tokens[j][0], []).append(tokens[j][1])
            j += 1
        return ent, j

    # ---------- Read ENTITIES ----------
    entities = []
    section = None
    i = 0
    while i < len(tokens):
        code, val = tokens[i]
        if code == "0" and val == "SECTION":
            section = tokens[i+1][1]
            i += 2
            continue
        if section == "ENTITIES" and code == "0":
            ent, i = read_entity(i)
            entities.append(ent)
            continue
        i += 1

    circles = []
    outer_points = []

    # ---------- Process entities ----------
    for ent in entities:
        t = ent["type"].upper()
        d = ent["data"]

        if t == "CIRCLE":
            r = float(d.get("40", [0])[0]) * unit_to_mm
            cx = float(d.get("10", [0])[0]) * unit_to_mm
            cy = float(d.get("20", [0])[0]) * unit_to_mm
            circles.append({"r": r, "d": 2 * r, "cx": cx, "cy": cy})

        if t == "LINE":
            x1 = float(d.get("10", [0])[0]) * unit_to_mm
            y1 = float(d.get("20", [0])[0]) * unit_to_mm
            x2 = float(d.get("11", [0])[0]) * unit_to_mm
            y2 = float(d.get("21", [0])[0]) * unit_to_mm
            outer_points.extend([(x1, y1), (x2, y2)])

        if t in ("LWPOLYLINE", "POLYLINE"):
            xs = [float(v) * unit_to_mm for v in d.get("10", [])]
            ys = [float(v) * unit_to_mm for v in d.get("20", [])]
            outer_points.extend(list(zip(xs, ys)))

    return circles, outer_points

# ==========================================================
# GEOMETRY HELPERS
# ==========================================================
def bounding_box(points):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return min(xs), max(xs), min(ys), max(ys)

# ==========================================================
# MAIN
# ==========================================================
if __name__ == "__main__":

    # --------- CLI INPUT ----------
    if len(sys.argv) < 2:
        print("USAGE: python cad_extractor.py <input_file.dxf>")
        sys.exit(1)

    DXF_FILE = sys.argv[1]

    if not os.path.exists(DXF_FILE):
        raise FileNotFoundError(f"DXF file not found: {DXF_FILE}")

    circles, outer_pts = parse_dxf(DXF_FILE)

    if not circles:
        raise ValueError("No CIRCLE entity found in DXF")

    inner = min(circles, key=lambda c: c["r"])

    # --------- OUTPUT CSV ----------
    OUTPUT_CSV = "dxf_measurements.csv"

    rows = []

    print("\n========== DXF PART ANALYSIS ==========\n")

    # ------------------------------------------------------
    # CASE 1: BALL BEARING / ROUND WASHER
    # ------------------------------------------------------
    if len(circles) >= 2 and not outer_pts:
        outer = max(circles, key=lambda c: c["r"])

        print("Detected Part : BALL BEARING / ROUND WASHER")
        print(f"Outer Diameter : {outer['d']:.3f} mm")
        print(f"Inner Diameter : {inner['d']:.3f} mm")

        rows.extend([
            ("outer_diameter", outer["d"]),
            ("inner_diameter", inner["d"])
        ])

    # ------------------------------------------------------
    # CASE 2: SQUARE WASHER
    # ------------------------------------------------------
    elif len(outer_pts) == 4:
        minx, maxx, miny, maxy = bounding_box(outer_pts)

        print("Detected Part : SQUARE WASHER")
        print(f"Outer Width   : {maxx - minx:.3f} mm")
        print(f"Outer Height  : {maxy - miny:.3f} mm")
        print(f"Inner Diameter: {inner['d']:.3f} mm")

        rows.extend([
            ("outer_width", maxx - minx),
            ("outer_height", maxy - miny),
            ("inner_diameter", inner["d"])
        ])

    # ------------------------------------------------------
    # CASE 3: HEX NUT
    # ------------------------------------------------------
    elif len(outer_pts) == 6:
        minx, maxx, miny, maxy = bounding_box(outer_pts)

        print("Detected Part : HEX NUT")
        print(f"Across Flats  : {maxx - minx:.3f} mm")
        print(f"Inner Diameter: {inner['d']:.3f} mm")

        rows.extend([
            ("across_flats", maxx - minx),
            ("inner_diameter", inner["d"])
        ])

    else:
        raise ValueError("Unsupported or malformed DXF geometry")

    # --------- WRITE CSV ----------
    with open(OUTPUT_CSV, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["type", "value_mm"])
        for r in rows:
            writer.writerow(r)

    print(f"\nCAD measurements saved to {OUTPUT_CSV}")
    print("\n======================================\n")
