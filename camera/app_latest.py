import cv2
import numpy as np
import pickle
from ultralytics import YOLO
import time
import csv
import os

# =====================================================
# FIXED CAMERA–OBJECT DISTANCE
# =====================================================
FIXED_DISTANCE_MM = 270.0     # 26 cm

CAMERA_INDEX = 0
YOLO_MODEL_PATH = "yolov8n.pt"

CAMERA_MATRIX_FILE = "cameraMatrix.pkl"
DIST_FILE = "dist.pkl"
CALIBRATION_FILE = "calibration.pkl"

RAW_OUTPUT_FILE = "measured_output.csv"
CLEANED_OUTPUT_FILE = "cleaned_output.csv"     # <--- NEW CLEANED FILE
LIVE_OUTPUT_FILE = "current_measurement.txt"

# =====================================================
# INITIALIZE RAW CSV
# =====================================================
if not os.path.exists(RAW_OUTPUT_FILE):
    with open(RAW_OUTPUT_FILE, "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            "timestamp",
            "label",
            "type",
            "measurement_mm",
            "w_mm",
            "h_mm",
            "diameter_mm",
            "x1", "y1", "x2", "y2",
            "distance_mm"
        ])

# =====================================================
# INITIALIZE CLEANED CSV
# =====================================================
if not os.path.exists(CLEANED_OUTPUT_FILE):
    with open(CLEANED_OUTPUT_FILE, "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "OD_mm", "ID_mm"])


# =====================================================
# LIVE FILE WRITER
# =====================================================
def write_live_file(text):
    with open(LIVE_OUTPUT_FILE, "w") as f:
        f.write(text)


# =====================================================
# LOAD CALIBRATION
# =====================================================
print("[INFO] Loading calibration...")
with open(CAMERA_MATRIX_FILE, "rb") as f:
    camera_matrix = pickle.load(f)

with open(DIST_FILE, "rb") as f:
    dist_coeffs = pickle.load(f)

try:
    with open(CALIBRATION_FILE, "rb") as f:
        cal = pickle.load(f)
except:
    print("[WARN] calibration.pkl not loaded.")

fx = camera_matrix[0, 0]
fy = camera_matrix[1, 1]

model = YOLO(YOLO_MODEL_PATH)
print("[INFO] YOLO loaded")



# =====================================================
# BALL BEARING DETECTOR
# =====================================================
def detect_ball_bearing(roi):

    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (7, 7), 1.5)

    circles = cv2.HoughCircles(
        gray,
        cv2.HOUGH_GRADIENT,
        dp=1.1,
        minDist=20,
        param1=120,
        param2=30,
        minRadius=20,
        maxRadius=min(gray.shape[0] // 2, gray.shape[1] // 2)
    )

    if circles is None:
        return None

    circles = np.round(circles[0, :]).astype("int")
    ox, oy, orad = max(circles, key=lambda c: c[2])
    outer_diam_px = 2 * orad

    edges = cv2.Canny(gray, 50, 140)
    cnts, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    inner_diam_px = None
    ix = iy = None

    for c in cnts:
        (x, y), r = cv2.minEnclosingCircle(c)
        area = cv2.contourArea(c)

        if 10 < r < orad * 0.8 and area > 40:
            inner_diam_px = int(2 * r)
            ix = int(x)
            iy = int(y)
            break

    if inner_diam_px is None:
        return None

    return outer_diam_px, inner_diam_px, (ox, oy), (ix, iy)


# =====================================================
# WASHER DETECTOR
# =====================================================
def detect_washer_shape(roi):
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    gray = clahe.apply(gray)
    blur = cv2.GaussianBlur(gray, (5,5), 1)

    edges = cv2.Canny(blur, 40, 120)
    edges = cv2.dilate(edges, None, iterations=1)

    cnts, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if len(cnts) == 0:
        return None

    outer = max(cnts, key=cv2.contourArea)
    (ox, oy), orad = cv2.minEnclosingCircle(outer)
    ox, oy, orad = int(ox), int(oy), int(orad)
    outer_diam_px = 2 * orad

    hole_bin = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        35, 4
    )

    cnts2, _ = cv2.findContours(hole_bin, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    inner_diam_px = None
    ix = iy = None

    for c in cnts2:
        area = cv2.contourArea(c)
        if 30 < area < (outer_diam_px ** 2):
            (ix, iy), irad = cv2.minEnclosingCircle(c)
            ix, iy, irad = int(ix), int(iy), int(irad)
            inner_diam_px = 2 * irad
            break

    return outer_diam_px, inner_diam_px, (ox, oy), (ix, iy)


# =====================================================
# PIXEL → MM CONVERSION
# =====================================================
def get_mm_per_px():
    return FIXED_DISTANCE_MM / fx


cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
if not cap.isOpened():
    print("[ERROR] Camera cannot open")
    exit()

mm_per_px = get_mm_per_px()
distance_mm = FIXED_DISTANCE_MM


# =====================================================
# MAIN LOOP
# =====================================================
while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.undistort(frame, camera_matrix, dist_coeffs)
    display = frame.copy()

    results = model.predict(frame, conf=0.3, verbose=False)

    for r in results:
        for box in r.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cls_name = model.names[int(box.cls[0])]

            cv2.rectangle(display, (x1, y1), (x2, y2), (0,255,0), 1)
            roi = frame[y1:y2, x1:x2]

            # =====================================================
            # 1 — BALL BEARING DETECTION
            # =====================================================
            bearing = detect_ball_bearing(roi)

            if bearing is not None:
                outer_px, inner_px, (ox, oy), (ix, iy) = bearing

                outer_mm = outer_px * mm_per_px
                inner_mm = inner_px * mm_per_px

                cv2.circle(display, (x1 + ox, y1 + oy), outer_px // 2, (0,200,255), 3)
                cv2.circle(display, (x1 + ix, y1 + iy), inner_px // 2, (255,100,0), 2)

                text = f"BALL BEARING | OD {outer_mm:.2f} mm | ID {inner_mm:.2f} mm"
                cv2.putText(display, text, (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,255), 2)

                with open(RAW_OUTPUT_FILE, "a", newline='') as f:
                    csv.writer(f).writerow([
                        time.time(), cls_name, "ball_bearing",
                        outer_mm, "", "", inner_mm,
                        x1, y1, x2, y2, distance_mm
                    ])

                with open(CLEANED_OUTPUT_FILE, "a", newline='') as f:
                    csv.writer(f).writerow([
                        time.time(),
                        round(outer_mm, 3),
                        round(inner_mm, 3)
                    ])

                live_text = (
                    f"OBJECT: BALL BEARING\n"
                    f"OUTER DIAMETER: {outer_mm:.2f} mm\n"
                    f"INNER DIAMETER: {inner_mm:.2f} mm\n"
                    f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                )
                write_live_file(live_text)
                continue


            # =====================================================
            # 2 — WASHER DETECTION
            # =====================================================
            washer = detect_washer_shape(roi)

            if washer is not None:
                outer_px, inner_px, (ox, oy), (ix, iy) = washer

                outer_mm = outer_px * mm_per_px
                inner_mm = inner_px * mm_per_px if inner_px else None

                cv2.circle(display, (x1 + ox, y1 + oy), outer_px // 2, (0,255,0), 3)

                if inner_mm:
                    cv2.circle(display, (x1 + ix, y1 + iy), inner_px // 2, (255,0,0), 2)

                if inner_mm:
                    text = f"OD {outer_mm:.2f} mm | ID {inner_mm:.2f} mm"
                else:
                    text = f"OD {outer_mm:.2f} mm"

                cv2.putText(display, text, (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,255), 2)

                with open(RAW_OUTPUT_FILE, "a", newline='') as f:
                    csv.writer(f).writerow([
                        time.time(), cls_name, "washer",
                        outer_mm, "", "", inner_mm if inner_mm else "",
                        x1, y1, x2, y2, distance_mm
                    ])

                with open(CLEANED_OUTPUT_FILE, "a", newline='') as f:
                    csv.writer(f).writerow([
                        time.time(),
                        round(outer_mm, 3),
                        round(inner_mm, 3) if inner_mm else ""
                    ])

                live_text = (
                    f"OBJECT: WASHER\n"
                    f"OUTER DIAMETER: {outer_mm:.2f} mm\n"
                    f"INNER DIAMETER: {inner_mm:.2f} mm\n"
                    f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                )
                write_live_file(live_text)
                continue


            # =====================================================
            # 3 — FALLBACK RECTANGLE
            # =====================================================
            w_px = x2 - x1
            h_px = y2 - y1

            w_mm = w_px * mm_per_px
            h_mm = h_px * mm_per_px

            cv2.putText(display, f"{w_mm:.2f} x {h_mm:.2f} mm",
                        (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX,
                        0.7, (0,255,255), 2)

            with open(RAW_OUTPUT_FILE, "a", newline='') as f:
                csv.writer(f).writerow([
                    time.time(), cls_name, "rect",
                    "", w_mm, h_mm, "",
                    x1, y1, x2, y2, distance_mm
                ])

            live_text = (
                f"OBJECT: RECTANGLE\n"
                f"WIDTH: {w_mm:.2f} mm\n"
                f"HEIGHT: {h_mm:.2f} mm\n"
                f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            )
            write_live_file(live_text)

    cv2.imshow("Measurement System", display)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
