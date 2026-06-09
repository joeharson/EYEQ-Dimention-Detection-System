import subprocess
import sys
import os
import pandas as pd

# ======================================================
# ARGUMENT CHECK
# ======================================================
if len(sys.argv) < 2:
    print("\nUSAGE:")
    print("  python main.py cad_inputs/<file>.dxf")
    print("  python main.py cad_inputs/<file>.stl\n")
    sys.exit(1)

# ======================================================
# CONFIG
# ======================================================
CAD_FILE = sys.argv[1]
CAD_OUTPUT = "dxf_measurements.csv"

# ======================================================
# STEP 1: RUN CAD DIMENSION EXTRACTION
# ======================================================
print("\n[STEP 1] Extracting CAD dimensions...\n")

if CAD_FILE.lower().endswith(".dxf"):
    subprocess.run(
        ["python", os.path.join("cad", "cad_extractor.py"), CAD_FILE],
        check=True
    )

elif CAD_FILE.lower().endswith(".stl"):
    subprocess.run(
        ["python", os.path.join("cad", "stl_extractor.py"), CAD_FILE],
        check=True
    )

else:
    raise ValueError("Unsupported CAD format (only DXF / STL supported)")

# ======================================================
# STEP 2: IDENTIFY PART TYPE FROM CAD CSV
# ======================================================
print("[STEP 2] Identifying component type...")

if not os.path.exists(CAD_OUTPUT):
    raise FileNotFoundError(f"CAD output file not found: {CAD_OUTPUT}")

cad_df = pd.read_csv(CAD_OUTPUT)

if "type" not in cad_df.columns:
    raise ValueError("CAD CSV must contain a 'type' column")

types = cad_df["type"].astype(str).str.lower().tolist()

if "outer_diameter" in types and "inner_diameter" in types:
    part = "bearing"

elif "outer_width" in types and "inner_diameter" in types:
    part = "square_washer"

elif "across_flats" in types:
    part = "hex_nut"

else:
    part = "washer"

print(f"Detected Part Type: {part.upper()}")

# ======================================================
# STEP 3: RUN LIVE CAMERA INSPECTION (SAFE)
# ======================================================
print("\n[STEP 3] Starting live inspection...\n")

VISION_SCRIPT = {
    "bearing": os.path.join("vision", "bearing.py"),
    "washer": os.path.join("vision", "washer.py"),
    "square_washer": os.path.join("vision", "square_washer.py"),
    "hex_nut": os.path.join("vision", "nut.py")
}

script_path = VISION_SCRIPT.get(part)

if script_path is None:
    raise ValueError(f"No vision script mapped for part type: {part}")

if not os.path.exists(script_path):
    raise FileNotFoundError(f"Vision script not found: {script_path}")

# 🔴 IMPORTANT: new console + non-blocking
process = subprocess.Popen(
    ["python", script_path],
    creationflags=subprocess.CREATE_NEW_CONSOLE
)

print("▶ Live inspection running.")
print("▶ Close the camera window (press 'q') to continue...\n")

# Wait until camera window is closed
process.wait()

# ======================================================
# STEP 4: CAD vs CAMERA COMPARISON
# ======================================================
print("\n[STEP 4] Comparing CAD and measured dimensions...\n")

subprocess.run(
    ["python", os.path.join("comparison", "compare_results.py")],
    check=True
)

print("\n✅ INSPECTION PIPELINE COMPLETE\n")
