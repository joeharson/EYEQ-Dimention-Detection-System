import cv2
import numpy as np
import pickle
from ultralytics import YOLO
import time
import csv
import os
import pandas as pd

# =====================================================
# CONFIG
# =====================================================
CAMERA_INDEX = 0
YOLO_MODEL_PATH = "yolov8n.pt"

CAMERA_MATRIX_FILE = "cameraMatrix.pkl"
DIST_FILE = "dist.pkl"

CAD_MEASURE_FILE = "dxf_measurements.csv"

RAW_OUTPUT_FILE = "measured_output.csv"
CLEANED_OUTPUT_FILE = "cleaned_output.csv"
LIVE_OUTPUT_FILE = "current_measurement.txt"

# =====================================================
# LOAD CAD REFERENCE (AUTO CALIBRATION)
# =====================================================
cad_df = pd.read_csv(CAD_MEASURE_FILE)

CAD_OD_MM = float(
    cad_df[cad_df["type"].str.contains("outer", case=False)]["value_mm"].iloc[0]
)

print(f"[INFO] CAD Outer Diameter = {CAD_OD_MM:.2f} mm")

# =====================================================
# INIT FILES
# =====================================================
if not os.path.exists(RAW_OUTPUT_FILE):
    with open(RAW_OUTPUT_FILE, "w", newline="") as f:
        csv.writer(f).writerow(["timestamp", "OD_mm", "ID_mm"])

if not os.path.exists(CLEANED_OUTPUT_FILE):
    with open(CLEANED_OUTPUT_FILE, "w", newline="") as f:
        csv.writer(f).writerow(["timestamp", "OD_mm", "ID_mm"])

def write_live(text):
    with open(LIVE_OUTPUT_FILE, "w") as f:
        f.write(text)

# =====================================================
# LOAD CAMERA & MODEL
# =====================================================
with open(CAMERA_MATRIX_FILE, "rb") as f:
    camera_matrix = pickle.load(f)

with open(DIST_FILE, "rb") as f:
    dist_coeffs = pickle.load(f)

model = YOLO(YOLO_MODEL_PATH)

cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
if not cap.isOpened():
    raise RuntimeError("Camera not accessible")

# =====================================================
# ROBUST WASHER / BEARING DETECTION
# =====================================================
def detect_washer(gray):
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    # ---------- OUTER CIRCLE ----------
    edges = cv2.Canny(blur, 30, 120)
    edges = cv2.dilate(edges, None, iterations=2)
    edges = cv2.erode(edges, None, iterations=1)

    cnts, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return None

    outer = max(cnts, key=cv2.contourArea)
    (ox, oy), orad = cv2.minEnclosingCircle(outer)

    # ---------- INNER ROI ----------
    r_search = int(orad * 0.6)
    cx, cy = int(ox), int(oy)

    h, w = gray.shape
    x1 = max(cx - r_search, 0)
    y1 = max(cy - r_search, 0)
    x2 = min(cx + r_search, w)
    y2 = min(cy + r_search, h)

    inner_roi = gray[y1:y2, x1:x2]

    # ---------- BRIGHT-HOLE DETECTION ----------
    _, bin_img = cv2.threshold(
        inner_roi, 0, 255,
        bin_img = cv2.adaptiveThreshold(
            inner_roi, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            31, 3
        )

    )

    # Ensure hole is white
    if np.mean(bin_img) < 127:
        bin_img = cv2.bitwise_not(bin_img)

    cnts_i, _ = cv2.findContours(
        bin_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    inner_rad = None
    for c in cnts_i:
        area = cv2.contourArea(c)
        if area < 50:
            continue

        (ix, iy), r = cv2.minEnclosingCircle(c)

        # Geometric constraint
        if 0.15 * orad < r < 0.6 * orad:
            inner_rad = r
            break

    return (ox, oy, orad), inner_rad

# =====================================================
# MAIN LOOP
# =====================================================
while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.undistort(frame, camera_matrix, dist_coeffs)
    gray_full = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    display = frame.copy()

    results = model.predict(frame, conf=0.3, verbose=False)

    for r in results:
        for box in r.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            roi_gray = gray_full[y1:y2, x1:x2]

            detected = detect_washer(roi_gray)
            if detected is None:
                continue

            (ox, oy, orad), irad = detected

            # ---------- AUTO CALIBRATION ----------
            outer_mm = (2 * orad) / PX_PER_MM
            inner_mm = (2 * irad) / PX_PER_MM if irad else None


            outer_mm = (2 * orad) / px_per_mm
            inner_mm = (2 * irad) / px_per_mm if irad else None

            # ---------- DRAW ----------
            cv2.circle(display, (x1 + int(ox), y1 + int(oy)), int(orad), (0, 255, 0), 2)

            if irad:
                cv2.circle(display, (x1 + int(ox), y1 + int(oy)), int(irad), (255, 0, 0), 2)

            label = f"OD: {outer_mm:.2f} mm"
            if inner_mm:
                label += f" | ID: {inner_mm:.2f} mm"

            cv2.putText(display, label, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

            # ---------- LOGGING ----------
            ts = time.time()

            with open(RAW_OUTPUT_FILE, "a", newline="") as f:
                csv.writer(f).writerow([
                    ts,
                    round(outer_mm, 3),
                    round(inner_mm, 3) if inner_mm else ""
                ])

            with open(CLEANED_OUTPUT_FILE, "a", newline="") as f:
                csv.writer(f).writerow([
                    ts,
                    round(outer_mm, 3),
                    round(inner_mm, 3) if inner_mm else ""
                ])

            write_live(
                f"OBJECT: WASHER / BEARING\n"
                f"OUTER DIAMETER: {outer_mm:.2f} mm\n"
                f"INNER DIAMETER: {inner_mm:.2f} mm\n"
                f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            )

    cv2.imshow("Bearing / Washer Measurement", display)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
