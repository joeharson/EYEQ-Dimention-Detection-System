import pandas as pd
import numpy as np

# ===========================================================
# CONFIG (CHANGE PER COMPONENT IF NEEDED)
# ===========================================================
CAD_FILE = "dxf_measurements.csv"
MEASURED_FILE = "cleaned_output.csv"

ABS_TOL_MM = 2.0            # absolute tolerance (mm)
REL_TOL_PERCENT = 20.0      # relative tolerance (%)

OUTPUT_REPORT = "component_comparison_report.csv"

# ===========================================================
# LOAD CAD VALUES (GENERIC)
# ===========================================================
def load_cad_values():
    df = pd.read_csv(CAD_FILE)

    cad_dims = {}

    for _, row in df.iterrows():
        dim_type = str(row["type"]).strip().lower()

        # support both diameter_mm / value_mm
        if "diameter_mm" in row:
            val = row["diameter_mm"]
        elif "value_mm" in row:
            val = row["value_mm"]
        else:
            continue

        cad_dims[dim_type] = float(val)

    if not cad_dims:
        raise ValueError("No usable CAD dimensions found.")

    return cad_dims

# ===========================================================
# LOAD MEASURED VALUES (GENERIC)
# ===========================================================
def load_measured_values():
    df = pd.read_csv(MEASURED_FILE)

    if "timestamp" not in df.columns:
        raise ValueError("Measured file must contain 'timestamp' column")

    dim_columns = [c for c in df.columns if c.lower().endswith("_mm")]

    if not dim_columns:
        raise ValueError("No dimension columns (_mm) found in measured file")

    measurements = []

    for _, row in df.iterrows():
        entry = {"timestamp": row["timestamp"]}
        for col in dim_columns:
            entry[col] = float(row[col])
        measurements.append(entry)

    return measurements, dim_columns

# ===========================================================
# ERROR CHECK
# ===========================================================
def check_error(meas, cad):
    abs_err = abs(meas - cad)
    rel_err = (abs_err / cad) * 100 if cad != 0 else 0
    ok = abs_err <= ABS_TOL_MM and rel_err <= REL_TOL_PERCENT
    return abs_err, rel_err, ok

# ===========================================================
# GENERIC COMPARISON ENGINE
# ===========================================================
def compare_components():
    cad_dims = load_cad_values()
    measured_list, dim_columns = load_measured_values()

    report = []

    for m in measured_list:
        row_out = {"timestamp": m["timestamp"]}
        overall_ok = True

        for col in dim_columns:
            meas_val = m[col]

            # try matching CAD key using name similarity
            key = col.replace("_mm", "").lower()

            cad_match = None
            for cad_key in cad_dims:
                if cad_key in key or key in cad_key:
                    cad_match = cad_dims[cad_key]
                    break

            if cad_match is None:
                continue  # skip unmatched dimension

            abs_err, rel_err, ok = check_error(meas_val, cad_match)
            overall_ok = overall_ok and ok

            row_out[f"CAD_{col}"] = cad_match
            row_out[f"MEAS_{col}"] = meas_val
            row_out[f"{col}_abs_err"] = abs_err
            row_out[f"{col}_rel_err_percent"] = rel_err

        row_out["status"] = "NOT DEFECTIVE" if overall_ok else "DEFECTIVE"
        report.append(row_out)

    df = pd.DataFrame(report)
    df.to_csv(OUTPUT_REPORT, index=False)

    print("\n=========== FINAL COMPONENT DEFECT REPORT ===========\n")
    print(df)
    print(f"\nSaved as {OUTPUT_REPORT}\n")

# ===========================================================
# MAIN
# ===========================================================
if __name__ == "__main__":
    compare_components()
