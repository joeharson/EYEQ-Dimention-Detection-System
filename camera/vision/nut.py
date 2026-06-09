import cv2
import numpy as np
import time

# ======================================
# CONFIG
# ======================================
CAMERA_INDEX = 0
REFERENCE_AF_MM = 25.0      # Known AF for calibration
EXPECTED_ID_RATIO = 0.55   # ID ≈ 0.65 * AF (hex nut geometry)

mm_per_px = None

# ======================================
# CAMERA SETUP
# ======================================
cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)
cap.set(cv2.CAP_PROP_EXPOSURE, -6)

if not cap.isOpened():
    raise RuntimeError("Camera not accessible")

time.sleep(2)

# ======================================
# TRUE ACROSS FLATS (MEDIAN METHOD)
# ======================================
def true_across_flats(contour):
    hull = cv2.convexHull(contour)
    pts = hull.reshape(-1, 2)

    distances = []
    edges = []

    for i in range(len(pts)):
        p1 = pts[i]
        p2 = pts[(i + 1) % len(pts)]

        edge = p2 - p1
        normal = np.array([-edge[1], edge[0]], dtype=np.float32)
        n = np.linalg.norm(normal)
        if n == 0:
            continue
        normal /= n

        proj = np.dot(pts, normal)
        dist = proj.max() - proj.min()

        distances.append(dist)
        edges.append((tuple(p1), tuple(p2)))

    if not distances:
        return None, None

    idx = np.argsort(distances)[len(distances) // 2]
    return distances[idx], edges[idx]

# ======================================
# HEX NUT DETECTOR (ROBUST)
# ======================================
def detect_hex_nut(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    img_cx, img_cy = w // 2, h // 2

    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 80, 180)
    edges = cv2.dilate(edges, None, iterations=1)

    contours, _ = cv2.findContours(
        edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    candidates = []

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if not (1500 < area < 20000):
            continue

        hull = cv2.convexHull(cnt)
        solidity = area / (cv2.contourArea(hull) + 1e-6)
        if solidity < 0.9:
            continue

        peri = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.04 * peri, True)
        if not (5 <= len(approx) <= 7):
            continue

        M = cv2.moments(cnt)
        if M["m00"] == 0:
            continue
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])

        dist_center = np.hypot(cx - img_cx, cy - img_cy)
        candidates.append((dist_center, cnt))


        candidates.append((dist_center, cnt))

    if not candidates:
        return None

    cnt = min(candidates, key=lambda x: x[0])[1]
    AF_px, edge = true_across_flats(cnt)
    if AF_px is None:
        return None

    # ---------- INNER HOLE (FIXED & ROBUST) ----------
    mask = np.zeros_like(gray)
    cv2.drawContours(mask, [cnt], -1, 255, -1)
    inside = cv2.bitwise_and(gray, gray, mask=mask)
    inside = cv2.equalizeHist(inside)


    _, dark = cv2.threshold(
        inside, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )
    dark = cv2.medianBlur(dark, 5)

    inner_contours, _ = cv2.findContours(
        dark, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    irad = None
    center = None
    best_error = 1e9
    expected_id_px = EXPECTED_ID_RATIO * AF_px

    for c in inner_contours:
        (ix, iy), r = cv2.minEnclosingCircle(c)
        diameter = 2 * r

        # Diameter sanity
        if not (0.5 * AF_px < diameter < 0.9 * AF_px):
            continue

        # Concentricity check
        dist_center = np.hypot(ix - hx, iy - hy)
        if dist_center > 0.1 * AF_px:
            continue

        error = abs(diameter - expected_id_px)
        if error < best_error:
            best_error = error
            irad = int(r)
            center = (int(ix), int(iy))

    return cnt, AF_px, irad, edge, center

# ======================================
# MAIN LOOP
# ======================================
while True:
    ret, frame = cap.read()
    if not ret:
        continue

    display = frame.copy()

    result = detect_hex_nut(frame)
    if result:
        cnt, AF_px, irad, edge, center = result

        # ---- CALIBRATION (ONCE) ----
        if mm_per_px is None:
            mm_per_px = REFERENCE_AF_MM / AF_px
            print(f"[CALIBRATED] {mm_per_px:.6f} mm/px")

        AF_mm = AF_px * mm_per_px
        ID_mm = (2 * irad * mm_per_px) if irad is not None else None

        # ---- DRAW ----
        cv2.drawContours(display, [cnt], -1, (0, 255, 0), 2)

        if edge:
            cv2.line(display, edge[0], edge[1], (0, 0, 255), 3)

        if center and irad:
            cv2.circle(display, center, irad, (255, 0, 0), 2)

        if ID_mm is not None:
            label = f"AF: {AF_mm:.2f} mm | ID: {ID_mm:.2f} mm"
            color = (0, 255, 255)
        else:
            label = f"AF: {AF_mm:.2f} mm | ID: ---"
            color = (0, 0, 255)

        cv2.putText(
            display, label, (30, 40),
            cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2
        )

    cv2.imshow("Hex Nut Measurement (STABLE)", display)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()