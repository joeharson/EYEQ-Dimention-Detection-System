import cv2
import numpy as np
import threading
import time
import os
import csv
from datetime import datetime
from ultralytics import YOLO

# ======================================
# CONFIG (UNCHANGED)
# ======================================
CAMERA_INDEX = 0
YOLO_MODEL_PATH = "yolov8n.pt"
CONF = 0.3

REFERENCE_OD_MM = 31.0
REFERENCE_ID_MM = 14.0

mm_per_px = None

# ======================================
# 🔹 ADDED FOR FRONTEND REPORTING
# ======================================
RAW_OUTPUT_FILE = "measured_output.csv"
CLEANED_OUTPUT_FILE = "cleaned_output.csv"
LIVE_OUTPUT_FILE = "current_measurement.txt"

if not os.path.exists(RAW_OUTPUT_FILE):
    with open(RAW_OUTPUT_FILE, "w", newline="") as f:
        csv.writer(f).writerow([
            "timestamp",
            "outer_diameter_mm",
            "inner_diameter_mm",
            "outer_diameter_px",
            "inner_diameter_px",
            "mm_per_px"
        ])

if not os.path.exists(CLEANED_OUTPUT_FILE):
    with open(CLEANED_OUTPUT_FILE, "w", newline="") as f:
        csv.writer(f).writerow([
            "timestamp",
            "outer_diameter_mm",
            "inner_diameter_mm"
        ])

def write_live_file(text):
    with open(LIVE_OUTPUT_FILE, "w") as f:
        f.write(text)

# ======================================
# ROBUST CAMERA STREAM (UNCHANGED)
# ======================================
class RobustVideoStream:
    def __init__(self, src=0):
        self.src = src
        self.cap = None
        self.frame = None
        self.lock = threading.Lock()
        self.stopped = False

    def start(self):
        self.cap = cv2.VideoCapture(self.src, cv2.CAP_DSHOW)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        threading.Thread(target=self._update, daemon=True).start()
        return self

    def _update(self):
        while not self.stopped:
            ret, frame = self.cap.read()
            if ret:
                with self.lock:
                    self.frame = frame
            else:
                time.sleep(0.01)

    def read(self):
        with self.lock:
            return None if self.frame is None else self.frame.copy()

    def stop(self):
        self.stopped = True
        if self.cap:
            self.cap.release()

# ======================================
# LOAD YOLO (UNCHANGED)
# ======================================
model = YOLO(YOLO_MODEL_PATH)

# ======================================
# BEARING DETECTOR (UNCHANGED)
# ======================================
def detect_bearing(gray):
    blur = cv2.GaussianBlur(gray, (9, 9), 1.5)

    circles = cv2.HoughCircles(
        blur,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=100,
        param1=120,
        param2=30,
        minRadius=40,
        maxRadius=200,
    )

    if circles is None:
        return None

    circles = circles[0]

    if mm_per_px:
        expected_od_px = (REFERENCE_OD_MM / mm_per_px) / 2
        ox, oy, orad = min(circles, key=lambda c: abs(c[2] - expected_od_px))
    else:
        ox, oy, orad = max(circles, key=lambda c: c[2])

    inner_circles = cv2.HoughCircles(
        blur,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=orad,
        param1=120,
        param2=25,
        minRadius=int(orad * 0.3),
        maxRadius=int(orad * 0.7),
    )

    irad = None
    if inner_circles is not None:
        inner_circles = inner_circles[0]
        if mm_per_px:
            expected_id_px = (REFERENCE_ID_MM / mm_per_px) / 2
            ix, iy, irad = min(inner_circles, key=lambda c: abs(c[2] - expected_id_px))
        else:
            ix, iy, irad = inner_circles[0]

    return (int(ox), int(oy), int(orad)), int(irad) if irad else None

# ======================================
# START CAMERA
# ======================================
vs = RobustVideoStream(CAMERA_INDEX).start()
time.sleep(0.3)

cv2.namedWindow("Ball Bearing Measurement (CORRECT)", cv2.WINDOW_NORMAL)

# ======================================
# MAIN LOOP
# ======================================
while True:
    frame = vs.read()
    if frame is None:
        continue

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    display = frame.copy()

    results = model.predict(frame, conf=CONF, verbose=False)
    detected_any = False

    for r in results:
        for box in r.boxes:
            detected_any = True
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            roi_gray = gray[y1:y2, x1:x2]

            detected = detect_bearing(roi_gray)
            if detected is None:
                continue

            (ox, oy, orad), irad = detected
            cx, cy = x1 + ox, y1 + oy

            OD_px = 2 * orad
            ID_px = 2 * irad if irad else None

            if mm_per_px is None:
                mm_per_px = REFERENCE_OD_MM / OD_px
                print(f"[CALIBRATED] {mm_per_px:.6f} mm/px")

            OD_mm = OD_px * mm_per_px
            ID_mm = ID_px * mm_per_px if ID_px else None

            # DRAW
            cv2.circle(display, (cx, cy), orad, (0, 0, 255), 2)
            if irad:
                cv2.circle(display, (cx, cy), irad, (255, 255, 0), 2)

            id_text = f"{ID_mm:.2f} mm" if ID_mm is not None else "NA"
            label = f"OD: {OD_mm:.2f} mm | ID: {id_text}"
            cv2.putText(display, label, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

            # ======================================
            # 🔹 ADDED FOR FRONTEND REPORTING
            # ======================================
            ts = time.time()

            with open(RAW_OUTPUT_FILE, "a", newline="") as f:
                csv.writer(f).writerow([
                    ts,
                    round(OD_mm, 3),
                    round(ID_mm, 3) if ID_mm else "",
                    round(OD_px, 1),
                    round(ID_px, 1) if ID_px else "",
                    mm_per_px
                ])

            with open(CLEANED_OUTPUT_FILE, "a", newline="") as f:
                csv.writer(f).writerow([
                    ts,
                    round(OD_mm, 3),
                    round(ID_mm, 3) if ID_mm else ""
                ])

            write_live_file(
                f"OBJECT: BEARING\n"
                f"OUTER DIAMETER: {OD_mm:.2f} mm\n"
                f"INNER DIAMETER: {id_text}\n"
                f"Timestamp: {datetime.now()}\n"
            )

    cv2.imshow("Ball Bearing Measurement (CORRECT)", display)

    key = cv2.waitKey(1)
    if key & 0xFF == ord("q"):
        break

    time.sleep(0.001)

# ======================================
# CLEAN EXIT
# ======================================
vs.stop()
cv2.destroyAllWindows()

