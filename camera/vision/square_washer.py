import cv2
import numpy as np
import pickle
from ultralytics import YOLO
import time
import csv
import os

# =====================================================
# CONFIGURATION
# =====================================================
CAMERA_INDEX = 0
YOLO_MODEL_PATH = "yolov8n.pt"

# DYNAMIC CALIBRATION - Reference Object Method
# Set this to the ACTUAL physical width of your square washer in millimeters
KNOWN_WASHER_WIDTH_MM = 40.0  # Change this to match your real object size

# CALIBRATION MODE
# True: Show raw pixel dimensions for calibration
# False: Show calculated real-world MM dimensions
CALIBRATION_MODE = False

CAMERA_MATRIX_FILE = "../calibration/cameraMatrix.pkl"
DIST_FILE = "../calibration/dist.pkl"
CALIBRATION_FILE = "../calibration/calibration.pkl"

OUTPUT_FILE = "measured_output.csv"

# =====================================================
# INITIALIZE OUTPUT CSV
# =====================================================
if not os.path.exists(OUTPUT_FILE):
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            "timestamp", "label", "shape_type", "measurement_mm",
            "width_mm", "height_mm", "diameter_mm", "sides",
            "x1", "y1", "x2", "y2", "distance_mm", "accuracy_score"
        ])

# Calibration disabled to remove fishbowl distortion and reduce lag
print("[INFO] Using raw camera feed (no distortion correction)...")
# with open(CAMERA_MATRIX_FILE, "rb") as f:
#     camera_matrix = pickle.load(f)
# with open(DIST_FILE, "rb") as f:
#     dist_coeffs = pickle.load(f)
# try:
#     with open(CALIBRATION_FILE, "rb") as f:
#         cal = pickle.load(f)
# except:
#     print("[WARN] calibration.pkl not loaded.")

# Default camera focal length (will be used for mm/px calculation)
# Adjust this value based on your actual camera setup
fx = 1000.0  # Default focal length in pixels
fy = 1000.0

model = YOLO(YOLO_MODEL_PATH)
print("[INFO] YOLO loaded")

# =====================================================
# UNIVERSAL SHAPE DETECTOR
# =====================================================
class ShapeDetector:
    """
    Square Washer Detector - Detects square/rectangular washers with holes
    """
    
    def __init__(self):
        self.shape_type = None
        self.measurements = {}
    
    def preprocess_roi(self, roi):
        """Enhanced preprocessing for better edge detection"""
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        
        # Adaptive lighting normalization
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)
        
        # Denoise
        gray = cv2.fastNlMeansDenoising(gray, h=10)
        
        return gray
    
    def detect_square_washer(self, roi, gray):
        """Detect SQUARE outer frame with CIRCULAR inner hole - ROBUST"""
        
        h, w = gray.shape
        
        # Enhanced preprocessing
        blur = cv2.GaussianBlur(gray, (9, 9), 2.0)
        
        # === STEP 1: Find OUTER SQUARE using multiple methods ===
        
        # Method 1: Edge detection with lower thresholds to capture full object
        edges = cv2.Canny(blur, 20, 60)
        edges = cv2.dilate(edges, np.ones((3,3), np.uint8), iterations=2)
        
        # Method 2: Adaptive threshold with larger block size
        binary = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                       cv2.THRESH_BINARY_INV, 15, 3)
        
        # Combine both methods
        combined = cv2.bitwise_or(edges, binary)
        
        # Clean up with morphology
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
        combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel, iterations=4)
        combined = cv2.morphologyEx(combined, cv2.MORPH_OPEN, kernel, iterations=1)
        
        # Find contours with hierarchy to detect holes
        cnts, hierarchy = cv2.findContours(combined, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        if len(cnts) == 0:
            return None
        
        # Filter contours by size - lowered threshold to capture full washer
        valid_cnts = []
        min_area = (w * h) * 0.08  # Reduced to 8% to catch larger objects
        
        for cnt in cnts:
            area = cv2.contourArea(cnt)
            if area > min_area:
                valid_cnts.append(cnt)
        
        if len(valid_cnts) == 0:
            return None
        
        # Get largest valid contour
        main_cnt = max(valid_cnts, key=cv2.contourArea)
        area = cv2.contourArea(main_cnt)
        
        # Check shape
        perimeter = cv2.arcLength(main_cnt, True)
        if perimeter == 0:
            return None
        
        # Calculate circularity
        circularity = 4 * np.pi * area / (perimeter ** 2)
        
        # MUST be rectangular (NOT circular) - relaxed threshold
        if circularity > 0.92:
            return None
        
        # Approximate to polygon
        epsilon = 0.04 * perimeter
        approx = cv2.approxPolyDP(main_cnt, epsilon, True)
        
        # Should have 4 corners (rectangle/square) - be more lenient
        if len(approx) < 4 or len(approx) > 8:
            return None
        
        # Get rotated rectangle
        rect = cv2.minAreaRect(main_cnt)
        box = cv2.boxPoints(rect)
        box = np.intp(box)
        
        width, height = rect[1]
        angle = rect[2]
        
        # Width and height must be reasonable - lowered threshold
        if width < 5 or height < 5:
            return None
        
        # Ensure width >= height for consistent measurements
        if width < height:
            width, height = height, width
            angle = angle + 90
        
        # Normalize angle to -45 to 45
        if angle < -45:
            angle = angle + 90
        elif angle > 45:
            angle = angle - 90
        
        # FIX: Stabilize dimensions for square objects (aspect ratio close to 1:1)
        aspect_ratio = width / height if height > 0 else 1.0
        
        # If aspect ratio is close to 1:1 (square), average the dimensions to reduce jitter
        if 0.90 <= aspect_ratio <= 1.10:  # Within 10% of being square
            avg_dimension = (width + height) / 2.0
            outer_width = avg_dimension
            outer_height = avg_dimension
        else:
            outer_width = width
            outer_height = height
        
        # Get center
        M = cv2.moments(main_cnt)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
        else:
            cx, cy = int(rect[0][0]), int(rect[0][1])
        
        # === STEP 2: Find INNER CIRCULAR HOLE ===
        inner_diameter = None
        inner_center = None
        
        # Prepare for circle detection
        blur_circle = cv2.GaussianBlur(gray, (9, 9), 2)
        
        # Try Hough Circles with adjusted parameters
        circles = cv2.HoughCircles(
            blur_circle,
            cv2.HOUGH_GRADIENT,
            dp=1.2,
            minDist=int(min(width, height) * 0.5),  # Increased to avoid multiple detections
            param1=50,
            param2=30,  # Increased for stricter detection
            minRadius=int(min(width, height) * 0.08),  # At least 8% of square
            maxRadius=int(min(width, height) * 0.45)   # Max 45% of square
        )
        
        if circles is not None:
            circles = np.uint16(np.around(circles))
            
            # Find best circle - ONLY ONE, most centered and circular
            best_circle = None
            best_score = 0
            
            for circle in circles[0]:
                cir_x, cir_y, cir_r = circle
                
                # Must be inside main contour
                if cv2.pointPolygonTest(main_cnt, (float(cir_x), float(cir_y)), False) < 0:
                    continue
                
                # Distance from square center - must be well centered
                dist = np.sqrt((cir_x - cx)**2 + (cir_y - cy)**2)
                max_dist = min(width, height) * 0.25  # Stricter centering (25% instead of 35%)
                
                if dist < max_dist:
                    # Size check - reasonable hole size
                    circle_area = np.pi * cir_r * cir_r
                    size_ratio = circle_area / area
                    
                    if 0.04 < size_ratio < 0.4:  # Hole should be 4%-40% of total area
                        # Score heavily favors centered holes
                        center_score = 1 - (dist / max_dist)
                        size_score = 1.0 if 0.08 < size_ratio < 0.25 else 0.7
                        
                        score = center_score * 0.85 + size_score * 0.15  # 85% weight on centering
                        
                        if score > best_score and score > 0.6:  # Minimum score threshold
                            best_score = score
                            best_circle = circle
            
            if best_circle is not None and best_score > 0.6:
                cir_x, cir_y, cir_r = best_circle
                inner_diameter = 2 * cir_r
                inner_center = (int(cir_x), int(cir_y))
        
        # Fallback: Threshold-based circle detection - ONLY if Hough failed
        if inner_center is None:
            # Try dark hole detection with adjusted threshold
            _, thresh = cv2.threshold(blur_circle, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            # Clean with larger kernel
            kernel_hole = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel_hole, iterations=2)
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel_hole, iterations=3)
            
            cnts2, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            
            best_hole = None
            best_score = 0
            
            for c in cnts2:
                hole_area = cv2.contourArea(c)
                
                # Size check - must be reasonable hole size
                size_ratio = hole_area / area
                if 0.04 < size_ratio < 0.4:  # 4%-40% of outer area
                    # Check circularity - MUST be very circular
                    hole_perimeter = cv2.arcLength(c, True)
                    if hole_perimeter > 0:
                        hole_circ = 4 * np.pi * hole_area / (hole_perimeter ** 2)
                        
                        # Stricter circularity requirement (>0.75)
                        if hole_circ > 0.75:
                            # Get center
                            hM = cv2.moments(c)
                            if hM["m00"] != 0:
                                hcx = int(hM["m10"] / hM["m00"])
                                hcy = int(hM["m01"] / hM["m00"])
                                
                                # Must be inside square and well centered
                                if cv2.pointPolygonTest(main_cnt, (float(hcx), float(hcy)), False) >= 0:
                                    dist = np.sqrt((hcx - cx)**2 + (hcy - cy)**2)
                                    max_dist = min(width, height) * 0.25  # Stricter centering
                                    
                                    if dist < max_dist:
                                        # Score: circularity (60%) + centering (40%)
                                        center_score = 1 - (dist / max_dist)
                                        score = hole_circ * 0.6 + center_score * 0.4
                                        
                                        if score > best_score and score > 0.65:  # Minimum threshold
                                            best_score = score
                                            (hx, hy), hr = cv2.minEnclosingCircle(c)
                                            best_hole = (int(hx), int(hy), int(hr))
            
            if best_hole and best_score > 0.65:
                hx, hy, hr = best_hole
                inner_diameter = 2 * hr
                inner_center = (hx, hy)
        
        # Calculate confidence
        confidence = 0.70
        if 0.50 < circularity < 0.85:  # Good rectangular shape
            confidence = 0.80
        if len(approx) == 4:  # Perfect 4 corners
            confidence += 0.05
        if inner_center:  # Has hole
            confidence = min(0.95, confidence + 0.10)
        
        return {
            'type': 'square_washer' if inner_center else 'square',
            'outer_width': outer_width,
            'outer_height': outer_height,
            'inner_diameter': inner_diameter,
            'outer_center': (cx, cy),
            'inner_center': inner_center,
            'bbox': box,
            'angle': angle,
            'circularity': circularity,
            'confidence': confidence
        }
        
        # === STEP 1: Detect OUTER SQUARE ===
        # Use edge detection for square
        edges = cv2.Canny(blur, 50, 150)
        
        # Dilate to connect edges
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        edges = cv2.dilate(edges, kernel, iterations=2)
        
        # Find contours
        cnts, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if len(cnts) == 0:
            return None
        
        # Get largest contour
        main_cnt = max(cnts, key=cv2.contourArea)
        area = cv2.contourArea(main_cnt)
        
        if area < 500:
            return None
        
        # Check if it's rectangular
        perimeter = cv2.arcLength(main_cnt, True)
        if perimeter == 0:
            return None
        
        circularity = 4 * np.pi * area / (perimeter ** 2)
        
        # Reject if too circular (must be square/rectangle)
        if circularity > 0.85:
            return None
        
        # Get rotated rectangle (for any angle)
        rect = cv2.minAreaRect(main_cnt)
        box = cv2.boxPoints(rect)
        box = np.intp(box)
        
        width, height = rect[1]
        angle = rect[2]
        
        # Ensure width >= height
        if width < height:
            width, height = height, width
        
        outer_width = width
        outer_height = height
        
        # Get center
        M = cv2.moments(main_cnt)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
        else:
            cx, cy = int(rect[0][0]), int(rect[0][1])
        
        # === STEP 2: Detect INNER CIRCULAR HOLE ===
        inner_diameter = None
        inner_center = None
        
        # Detect circles using Hough Transform
        circles = cv2.HoughCircles(
            blur,
            cv2.HOUGH_GRADIENT,
            dp=1.0,
            minDist=30,
            param1=50,
            param2=30,
            minRadius=5,
            maxRadius=int(min(width, height) // 2)
        )
        
        if circles is not None:
            circles = np.uint16(np.around(circles))
            
            # Find circle closest to center of square
            best_circle = None
            best_dist = float('inf')
            
            for circle in circles[0]:
                cir_x, cir_y, cir_r = circle
                
                # Distance from square center
                dist = np.sqrt((cir_x - cx)**2 + (cir_y - cy)**2)
                
                # Circle must be inside square and reasonably centered
                if dist < min(width, height) * 0.3:  # Within 30% of center
                    # Circle size must be reasonable (5% to 60% of square)
                    circle_area = np.pi * cir_r * cir_r
                    if 0.05 * area < circle_area < 0.6 * area:
                        if dist < best_dist:
                            best_dist = dist
                            best_circle = circle
            
            if best_circle is not None:
                cir_x, cir_y, cir_r = best_circle
                inner_diameter = 2 * cir_r
                inner_center = (int(cir_x), int(cir_y))
        
        # If Hough failed, try contour method for circular hole
        if inner_center is None:
            # Threshold for dark hole
            _, binary = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            # Clean up
            binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)
            binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)
            
            # Find holes
            cnts2, _ = cv2.findContours(binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            
            best_hole = None
            best_score = 0
            
            for c in cnts2:
                hole_area = cv2.contourArea(c)
                
                # Size check
                if 0.05 * area < hole_area < 0.6 * area:
                    # Check circularity of hole
                    hole_perimeter = cv2.arcLength(c, True)
                    if hole_perimeter > 0:
                        hole_circularity = 4 * np.pi * hole_area / (hole_perimeter ** 2)
                        
                        # Must be circular (>0.75)
                        if hole_circularity > 0.75:
                            # Get center
                            hM = cv2.moments(c)
                            if hM["m00"] != 0:
                                hcx = int(hM["m10"] / hM["m00"])
                                hcy = int(hM["m01"] / hM["m00"])
                                
                                # Check if inside square
                                if cv2.pointPolygonTest(main_cnt, (hcx, hcy), False) >= 0:
                                    dist = np.sqrt((hcx - cx)**2 + (hcy - cy)**2)
                                    
                                    if dist < min(width, height) * 0.3:
                                        # Score based on circularity and centering
                                        score = hole_circularity * (1 - dist / (min(width, height) * 0.3))
                                        
                                        if score > best_score:
                                            best_score = score
                                            (hx, hy), hr = cv2.minEnclosingCircle(c)
                                            best_hole = (int(hx), int(hy), int(hr))
            
            if best_hole:
                hx, hy, hr = best_hole
                inner_diameter = 2 * hr
                inner_center = (hx, hy)
        
        # Calculate confidence
        confidence = 0.75
        if 0.5 < circularity < 0.85:  # Good square shape
            confidence = 0.85
        if inner_center:  # Has circular hole
            confidence = 0.95
        
        return {
            'type': 'square_washer' if inner_center else 'square',
            'outer_width': outer_width,
            'outer_height': outer_height,
            'inner_diameter': inner_diameter,  # CIRCULAR hole
            'outer_center': (cx, cy),
            'inner_center': inner_center,
            'bbox': box,
            'angle': angle,
            'confidence': confidence
        }
        
        # Adaptive threshold to handle lighting variations
        binary = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                       cv2.THRESH_BINARY, 11, 2)
        
        # Invert if needed (make object white on black background)
        if np.mean(binary) > 127:
            binary = cv2.bitwise_not(binary)
        
        # Morphological operations to clean up
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)
        
        # Multi-method edge detection
        edges1 = cv2.Canny(blur, 30, 100)
        edges2 = cv2.Canny(blur, 50, 150)
        edges = cv2.bitwise_or(edges1, edges2)
        edges = cv2.dilate(edges, kernel, iterations=1)
        
        # Combine methods
        combined = cv2.bitwise_or(binary, edges)
        
        # Find contours
        cnts, _ = cv2.findContours(combined, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if len(cnts) == 0:
            return None
        
        # Get largest contour (outer square)
        main_cnt = max(cnts, key=cv2.contourArea)
        area = cv2.contourArea(main_cnt)
        
        if area < 300:  # Too small
            return None
        
        # Get perimeter and check if it's rectangular
        perimeter = cv2.arcLength(main_cnt, True)
        if perimeter == 0:
            return None
        
        # Calculate circularity (rectangles have low circularity)
        circularity = 4 * np.pi * area / (perimeter ** 2)
        
        # Reject circles (circularity > 0.85)
        if circularity > 0.85:
            return None
        
        # Get rotated rectangle (works for any angle)
        rect = cv2.minAreaRect(main_cnt)
        box = cv2.boxPoints(rect)
        box = np.intp(box)
        
        # Get width and height (order doesn't matter, we'll sort)
        width = rect[1][0]
        height = rect[1][1]
        angle = rect[2]
        
        # Ensure width >= height
        if width < height:
            width, height = height, width
        
        outer_width = width
        outer_height = height
        
        # Calculate center from moments
        M = cv2.moments(main_cnt)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
        else:
            cx, cy = int(rect[0][0]), int(rect[0][1])
        
        # Enhanced inner hole detection
        inner_width = None
        inner_height = None
        inner_center = None
        
        # Method 1: Adaptive threshold for dark holes
        hole_bin = cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            21, 8
        )
        
        # Method 2: Otsu threshold on center region
        roi_center = gray[max(0, cy-int(height//2)):min(gray.shape[0], cy+int(height//2)),
                         max(0, cx-int(width//2)):min(gray.shape[1], cx+int(width//2))]
        
        if roi_center.size > 0:
            _, hole_bin2 = cv2.threshold(roi_center, 0, 255, 
                                         cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            # Expand to full size
            hole_full = np.zeros_like(gray)
            y1 = max(0, cy-int(height//2))
            y2 = min(gray.shape[0], cy+int(height//2))
            x1 = max(0, cx-int(width//2))
            x2 = min(gray.shape[1], cx+int(width//2))
            hole_full[y1:y2, x1:x2] = hole_bin2
        else:
            hole_full = hole_bin
        
        # Combine hole detection methods
        hole_combined = cv2.bitwise_or(hole_bin, hole_full)
        
        # Clean up hole detection
        hole_combined = cv2.morphologyEx(hole_combined, cv2.MORPH_CLOSE, kernel, iterations=2)
        hole_combined = cv2.morphologyEx(hole_combined, cv2.MORPH_OPEN, kernel, iterations=1)
        
        # Find inner hole contours
        cnts2, hierarchy = cv2.findContours(hole_combined, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        best_hole = None
        best_score = 0
        
        # Look for holes inside the main contour
        for i, c in enumerate(cnts2):
            hole_area = cv2.contourArea(c)
            
            # Hole should be smaller than outer area but not too small
            min_hole_area = area * 0.02  # At least 2% of outer area
            max_hole_area = area * 0.7   # At most 70% of outer area
            
            if min_hole_area < hole_area < max_hole_area:
                # Get hole center
                hM = cv2.moments(c)
                if hM["m00"] != 0:
                    hcx = int(hM["m10"] / hM["m00"])
                    hcy = int(hM["m01"] / hM["m00"])
                    
                    # Check if hole is inside main contour
                    if cv2.pointPolygonTest(main_cnt, (hcx, hcy), False) >= 0:
                        # Distance from center
                        dist_from_center = np.sqrt((hcx - cx)**2 + (hcy - cy)**2)
                        max_offset = min(width, height) * 0.4  # Allow 40% offset
                        
                        if dist_from_center < max_offset:
                            # Get hole dimensions using rotated rectangle
                            h_rect = cv2.minAreaRect(c)
                            h_width = h_rect[1][0]
                            h_height = h_rect[1][1]
                            
                            if h_width < h_height:
                                h_width, h_height = h_height, h_width
                            
                            # Score based on centering and size
                            size_ratio = hole_area / area
                            center_score = 1 - (dist_from_center / max_offset)
                            score = center_score * (1 if 0.05 < size_ratio < 0.5 else 0.5)
                            
                            if score > best_score and h_width > 5:  # Minimum hole size
                                best_score = score
                                best_hole = {
                                    'width': h_width,
                                    'height': h_height,
                                    'center': (hcx, hcy),
                                    'box': cv2.boxPoints(h_rect).astype(int)
                                }
        
        if best_hole:
            inner_width = best_hole['width']
            inner_height = best_hole['height']
            inner_center = best_hole['center']
        
        # Calculate confidence based on shape quality
        confidence = 0.70
        if 0.5 < circularity < 0.85:  # Good rectangle shape
            confidence = 0.85
        if best_hole:  # Has hole
            confidence = min(confidence + 0.10, 0.95)
        
        return {
            'type': 'square_washer' if inner_width else 'square',
            'outer_width': outer_width,
            'outer_height': outer_height,
            'inner_width': inner_width,
            'inner_height': inner_height,
            'outer_center': (cx, cy),
            'inner_center': inner_center,
            'bbox': box,
            'angle': angle,
            'circularity': circularity,
            'confidence': confidence
        }
    
    def preprocess_roi(self, roi):
        """Enhanced preprocessing for better edge detection"""
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        
        # Adaptive lighting normalization
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)
        
        # Denoise
        gray = cv2.fastNlMeansDenoising(gray, h=10)
        
        return gray
    
    def detect_circle_washer(self, roi, gray):
        """Enhanced washer detection - works for ALL sizes (small to large)"""
        blur = cv2.GaussianBlur(gray, (9, 9), 2)
        
        # Multi-method approach for better detection across all sizes
        results = []
        
        # Method 1: Hough Circles - works well for medium/large washers
        circles = cv2.HoughCircles(
            blur,
            cv2.HOUGH_GRADIENT,
            dp=1.0,
            minDist=30,
            param1=50,
            param2=25,  # Lower threshold for better detection
            minRadius=10,
            maxRadius=min(roi.shape[0], roi.shape[1]) // 2
        )
        
        # Method 2: Contour-based detection - works for all sizes
        edges = cv2.Canny(blur, 30, 100)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel, iterations=2)
        
        cnts, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        outer_circle = None
        
        # Try Hough circles first
        if circles is not None:
            circles = np.uint16(np.around(circles))
            outer_circle = circles[0][0]
            ox, oy, orad = outer_circle
        
        # If no Hough circles, use contour method
        elif len(cnts) > 0:
            main_cnt = max(cnts, key=cv2.contourArea)
            area = cv2.contourArea(main_cnt)
            
            if area > 100:  # Minimum area threshold
                perimeter = cv2.arcLength(main_cnt, True)
                
                if perimeter > 0:
                    circularity = 4 * np.pi * area / (perimeter ** 2)
                    
                    # Accept highly circular contours (>0.75 for flexibility)
                    if circularity > 0.75:
                        (cx, cy), rad = cv2.minEnclosingCircle(main_cnt)
                        ox, oy, orad = int(cx), int(cy), int(rad)
                        outer_circle = (ox, oy, orad)
        
        if outer_circle is None:
            return None
        
        ox, oy, orad = outer_circle
        
        # Enhanced inner hole detection with multiple thresholding methods
        inner_circle = None
        
        # Method 1: Adaptive threshold
        hole_bin1 = cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            35, 5
        )
        
        # Method 2: Otsu's threshold on center region
        center_region = gray[max(0, oy-orad):min(gray.shape[0], oy+orad), 
                            max(0, ox-orad):min(gray.shape[1], ox+orad)]
        
        if center_region.size > 0:
            _, hole_bin2 = cv2.threshold(center_region, 0, 255, 
                                         cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            # Expand back to full size
            hole_bin_full = np.zeros_like(gray)
            y1, y2 = max(0, oy-orad), min(gray.shape[0], oy+orad)
            x1, x2 = max(0, ox-orad), min(gray.shape[1], ox+orad)
            hole_bin_full[y1:y2, x1:x2] = hole_bin2
        else:
            hole_bin_full = hole_bin1
        
        # Combine both methods
        hole_bin = cv2.bitwise_or(hole_bin1, hole_bin_full)
        
        # Find inner hole contours
        cnts2, _ = cv2.findContours(hole_bin, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        best_inner = None
        best_score = 0
        
        for c in cnts2:
            area = cv2.contourArea(c)
            
            # Adaptive area threshold based on outer radius
            min_area = max(50, (orad * 0.1) ** 2)
            max_area = (orad * 0.8) ** 2
            
            if min_area < area < max_area:
                (ix, iy), irad = cv2.minEnclosingCircle(c)
                
                # Verify inner circle is centered
                dist_from_center = np.sqrt((ix - ox)**2 + (iy - oy)**2)
                max_offset = orad * 0.3  # Allow more offset for imperfect alignment
                
                if dist_from_center < max_offset:
                    # Check circularity
                    perimeter_inner = cv2.arcLength(c, True)
                    if perimeter_inner > 0:
                        circularity_inner = 4 * np.pi * area / (perimeter_inner ** 2)
                        
                        # Score based on circularity and centering
                        score = circularity_inner * (1 - dist_from_center / max_offset)
                        
                        if circularity_inner > 0.65 and score > best_score:
                            best_score = score
                            best_inner = (int(ix), int(iy), int(irad))
        
        inner_circle = best_inner
        
        return {
            'type': 'washer' if inner_circle else 'circle',
            'outer_diameter': 2 * orad,
            'inner_diameter': 2 * inner_circle[2] if inner_circle else None,
            'outer_center': (ox, oy),
            'inner_center': (inner_circle[0], inner_circle[1]) if inner_circle else None,
            'confidence': 0.95 if inner_circle else 0.90
        }
    
    def detect_polygon(self, roi, gray):
        """Detect polygonal shapes (hexagon, pentagon, octagon for bolts/nuts)"""
        blur = cv2.GaussianBlur(gray, (5, 5), 1)
        
        # Multi-threshold approach for better edge detection
        edges1 = cv2.Canny(blur, 40, 120)
        edges2 = cv2.Canny(blur, 60, 180)
        edges = cv2.bitwise_or(edges1, edges2)
        
        # Morphology to connect edges
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel, iterations=2)
        
        cnts, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if len(cnts) == 0:
            return None
        
        # Get largest contour
        main_cnt = max(cnts, key=cv2.contourArea)
        area = cv2.contourArea(main_cnt)
        
        # Filter too small contours
        if area < 500:
            return None
        
        # Approximate polygon with tighter tolerance for better corner detection
        epsilon = 0.015 * cv2.arcLength(main_cnt, True)
        approx = cv2.approxPolyDP(main_cnt, epsilon, True)
        
        num_sides = len(approx)
        
        # Check if it's actually a polygon (not too many sides = circle)
        if num_sides > 10:
            # Too many sides, likely a circle
            return None
        
        # Verify it's a valid polygon (3-10 sides)
        if num_sides < 3:
            return None
        
        # Identify shape based on sides
        shape_name = {
            3: 'triangle',
            4: 'rectangle',
            5: 'pentagon',
            6: 'hexagon',
            7: 'heptagon',
            8: 'octagon'
        }.get(num_sides, f'{num_sides}-gon')
        
        # Calculate bounding measurements
        rect = cv2.minAreaRect(main_cnt)
        box = cv2.boxPoints(rect)
        box = np.intp(box)
        
        width = rect[1][0]
        height = rect[1][1]
        
        # For bolts/nuts, measure across flats (width of hexagon)
        across_flats = min(width, height)
        
        if num_sides == 6:  # Hexagon - measure more accurately
            # Find opposite parallel sides for across-flats measurement
            distances = []
            for i in range(len(approx)):
                p1 = approx[i][0]
                # Check points opposite (3 positions away in hexagon)
                for j in range(i + 2, min(i + 5, len(approx))):
                    p2 = approx[j][0]
                    dist = np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
                    distances.append(dist)
            
            if distances:
                distances.sort()
                # Across-flats is typically smaller perpendicular distance
                across_flats = distances[len(distances)//3]
        
        # Calculate confidence based on how well it fits the polygon
        perimeter = cv2.arcLength(main_cnt, True)
        circularity = 4 * np.pi * area / (perimeter ** 2) if perimeter > 0 else 0
        
        # Polygons should have lower circularity than circles
        if circularity > 0.85:
            # Too circular, probably not a polygon
            return None
        
        # Higher confidence for well-defined polygons
        confidence = 0.85 if 5 <= num_sides <= 8 else 0.70
        confidence = confidence * (1 - circularity * 0.3)  # Reduce confidence if too circular
        
        return {
            'type': shape_name,
            'sides': num_sides,
            'width': max(width, height),
            'height': min(width, height),
            'across_flats': across_flats,
            'contour': approx,
            'bbox': box,
            'confidence': min(confidence, 0.95)
        }
    
    def detect_gear(self, roi, gray):
        """Detect gear with teeth counting"""
        blur = cv2.GaussianBlur(gray, (5, 5), 1)
        edges = cv2.Canny(blur, 50, 150)
        
        # Morphology to enhance teeth
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
        
        # Find outer contour
        cnts, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        
        if len(cnts) == 0:
            return None
        
        main_cnt = max(cnts, key=cv2.contourArea)
        area = cv2.contourArea(main_cnt)
        
        # Filter small areas
        if area < 800:
            return None
        
        perimeter = cv2.arcLength(main_cnt, True)
        
        if perimeter == 0:
            return None
        
        circularity = 4 * np.pi * area / (perimeter ** 2)
        
        # Gears have moderate circularity (0.5-0.75) due to teeth
        if not (0.45 < circularity < 0.78):
            return None
        
        # Check solidity (gears have teeth gaps)
        hull = cv2.convexHull(main_cnt)
        hull_area = cv2.contourArea(hull)
        
        solidity = area / hull_area if hull_area > 0 else 0
        
        # Gears must have lower solidity (0.7-0.85) due to teeth
        if solidity > 0.87 or solidity < 0.65:
            return None
        
        # Count teeth by detecting peaks in contour
        smoothed = cv2.approxPolyDP(main_cnt, 1.5, True)
        
        # Estimate teeth from contour complexity
        teeth_estimate = len(smoothed) // 3
        teeth_estimate = max(min(teeth_estimate, 60), 8)  # Clamp between 8-60
        
        # Get gear diameter
        (cx, cy), radius = cv2.minEnclosingCircle(main_cnt)
        
        # Higher confidence if solidity and circularity are in gear range
        confidence = 0.80
        if 0.50 < circularity < 0.70 and 0.70 < solidity < 0.82:
            confidence = 0.90
        
        return {
            'type': 'gear',
            'diameter': 2 * radius,
            'teeth_count': teeth_estimate,
            'center': (int(cx), int(cy)),
            'solidity': solidity,
            'circularity': circularity,
            'confidence': confidence
        }
    
    def detect_shape(self, roi):
        """Main detection - robust square washer detection"""
        if roi.shape[0] < 20 or roi.shape[1] < 20:
            return None
        
        gray = self.preprocess_roi(roi)
        
        # Try square washer detection
        square_result = self.detect_square_washer(roi, gray)
        
        # Accept if confidence is reasonable - lowered for better detection
        if square_result and square_result['confidence'] > 0.50:
            return square_result
        
        return None

# =====================================================
# VISUALIZATION HELPERS
# =====================================================
def draw_detection(display, result, x1, y1, mm_per_px, calibration_mode=False):
    """Draw square washer with clean, professional visualization"""
    
    if result['type'] in ['square_washer', 'square']:
        # Draw OUTER SQUARE (green outline)
        if 'bbox' in result:
            cv2.drawContours(display, [result['bbox'] + [x1, y1]], 0, (0, 255, 0), 2)
        
        # Draw corner markers (white with green outline)
        if 'bbox' in result:
            for point in result['bbox']:
                px, py = point
                cv2.circle(display, (x1 + px, y1 + py), 4, (255, 255, 255), -1)
                cv2.circle(display, (x1 + px, y1 + py), 6, (0, 255, 0), 1)
        
        # Draw INNER CIRCULAR HOLE (blue circle)
        if result['type'] == 'square_washer' and result['inner_center'] and result['inner_diameter']:
            ix, iy = result['inner_center']
            radius = int(result['inner_diameter'] // 2)
            
            # Draw circle for hole (blue)
            cv2.circle(display, (x1 + ix, y1 + iy), radius, (255, 100, 0), 2)
            cv2.circle(display, (x1 + ix, y1 + iy), 3, (255, 100, 0), -1)
            
        
        # === CLEAN LABELS WITH BACKGROUND ===
        if calibration_mode:
            # CALIBRATION MODE: Show raw pixel dimensions
            outer_w_px = result['outer_width']
            outer_h_px = result['outer_height']
            
            overlay = display.copy()
            label_height = 65 if result['type'] == 'square_washer' else 45
            cv2.rectangle(overlay, (x1 - 5, y1 - label_height - 5), 
                         (x1 + 300, y1 - 5), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.65, display, 0.35, 0, display)
            
            if result['type'] == 'square_washer':
                inner_d_px = result['inner_diameter']
                
                # Pixel dimensions (yellow for calibration)
                text = f"{outer_w_px:.1f}px x {outer_h_px:.1f}px"
                cv2.putText(display, text, (x1, y1 - 42),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2)
                
                # Hole diameter in pixels (cyan)
                text2 = f"Hole: {inner_d_px:.1f}px"
                cv2.putText(display, text2, (x1, y1 - 23),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 100), 2)
                
                # Calibration label (orange)
                cv2.putText(display, "CALIBRATION MODE", (x1 + 2, y1 - 8),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 165, 255), 1)
            else:
                text = f"{outer_w_px:.1f}px x {outer_h_px:.1f}px"
                cv2.putText(display, text, (x1, y1 - 28),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2)
                cv2.putText(display, "CALIBRATION MODE", (x1 + 2, y1 - 8),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 165, 255), 1)
        else:
            # NORMAL MODE: Show real MM dimensions
            outer_w_mm = result['outer_width'] * mm_per_px
            outer_h_mm = result['outer_height'] * mm_per_px
            
            overlay = display.copy()
            label_height = 65 if result['type'] == 'square_washer' else 45
            cv2.rectangle(overlay, (x1 - 5, y1 - label_height - 5), 
                         (x1 + 300, y1 - 5), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.65, display, 0.35, 0, display)
            
            if result['type'] == 'square_washer':
                inner_d_mm = result['inner_diameter'] * mm_per_px
                
                # Main dimensions (white text)
                text = f"{outer_w_mm:.1f}mm x {outer_h_mm:.1f}mm"
                cv2.putText(display, text, (x1, y1 - 42),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
                
                # Hole diameter (cyan)
                text2 = f"Hole: {inner_d_mm:.1f}mm"
                cv2.putText(display, text2, (x1, y1 - 23),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 100), 2)
                
                # Type label (green)
                cv2.putText(display, "Square Washer", (x1 + 2, y1 - 8),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.45, (100, 255, 100), 1)
            else:
                # Plain square (no hole)
                text = f"{outer_w_mm:.1f}mm x {outer_h_mm:.1f}mm"
                cv2.putText(display, text, (x1, y1 - 28),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
                cv2.putText(display, "Square", (x1 + 2, y1 - 8),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.45, (100, 255, 100), 1)
    
    else:
        text = f"{result['type']} detected"
        cv2.putText(display, text, (x1, y1 - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (128, 128, 128), 2)

# =====================================================
# MAIN DETECTION LOOP
# =====================================================
def main():
    cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print("[ERROR] Camera cannot open")
        return
    
    detector = ShapeDetector()
    
    print("[INFO] Starting measurement system...")
    if CALIBRATION_MODE:
        print("[CALIBRATION MODE] Showing pixel dimensions")
        print(f"[INFO] Reference width set to: {KNOWN_WASHER_WIDTH_MM}mm")
    else:
        print("[MEASUREMENT MODE] Showing real-world MM dimensions")
    print("[INFO] Press 'q' to quit, 's' to save snapshot")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Use raw camera feed (no undistortion) for better FPS and traditional view
        # frame = cv2.undistort(frame, camera_matrix, dist_coeffs)  # DISABLED
        display = frame.copy()
        
        # YOLO detection with lower confidence for better detection
        results = model.predict(frame, conf=0.20, verbose=False)
        
        # FIX: Collect all detections first and filter overlapping boxes
        all_boxes = []
        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cls_name = model.names[int(box.cls[0])]
                confidence = float(box.conf[0])
                box_area = (x2 - x1) * (y2 - y1)
                all_boxes.append((x1, y1, x2, y2, cls_name, confidence, box_area))
        
        # Sort by area (largest first) to prioritize outer objects
        all_boxes.sort(key=lambda x: x[6], reverse=True)
        
        # Filter out boxes that are inside other boxes (prevent double detection)
        filtered_boxes = []
        for i, box_i in enumerate(all_boxes):
            x1_i, y1_i, x2_i, y2_i = box_i[:4]
            is_inside = False
            
            for j, box_j in enumerate(all_boxes):
                if i == j:
                    continue
                x1_j, y1_j, x2_j, y2_j = box_j[:4]
                
                # Check if box_i is completely inside box_j
                if (x1_i >= x1_j and y1_i >= y1_j and x2_i <= x2_j and y2_i <= y2_j):
                    is_inside = True
                    break
            
            if not is_inside:
                filtered_boxes.append(box_i)
        
        # Process only the filtered (non-overlapping) boxes
        for box_data in filtered_boxes:
            x1, y1, x2, y2, cls_name, confidence, _ = box_data
            
            # Draw YOLO bounding box
            cv2.rectangle(display, (x1, y1), (x2, y2), (100, 100, 100), 1)
            
            # Extract ROI
            roi = frame[y1:y2, x1:x2]
            
            # Detect shape
            shape_result = detector.detect_shape(roi)
            
            if shape_result:
                # DYNAMIC CALIBRATION: Calculate mm_per_pixel based on detected width
                if shape_result['type'] in ['square_washer', 'square']:
                    detected_width_px = shape_result['outer_width']
                    
                    # Calculate scale: mm_per_pixel = known_size / detected_pixels
                    mm_per_px = KNOWN_WASHER_WIDTH_MM / detected_width_px
                else:
                    mm_per_px = 1.0  # Fallback for other shapes
                
                # Draw accurate shape detection
                draw_detection(display, shape_result, x1, y1, mm_per_px, CALIBRATION_MODE)
                
                # Save to CSV
                timestamp = time.time()
                shape_type = shape_result['type']
                
                if shape_type in ['square_washer', 'square']:
                    detected_width_px = shape_result['outer_width']
                    mm_per_px = KNOWN_WASHER_WIDTH_MM / detected_width_px
                    
                    outer_w_mm = shape_result['outer_width'] * mm_per_px
                    outer_h_mm = shape_result['outer_height'] * mm_per_px
                    inner_d_mm = shape_result['inner_diameter'] * mm_per_px if shape_result.get('inner_diameter') else 0
                    
                    with open(OUTPUT_FILE, "a", newline='') as f:
                        csv.writer(f).writerow([
                            timestamp, cls_name, shape_type, outer_w_mm,
                            outer_w_mm, outer_h_mm, inner_d_mm, "",
                            x1, y1, x2, y2, KNOWN_WASHER_WIDTH_MM, shape_result['confidence']
                        ])
        
        # Display info
        if CALIBRATION_MODE:
            cv2.putText(display, f"CALIBRATION MODE | Reference: {KNOWN_WASHER_WIDTH_MM}mm",
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        else:
            cv2.putText(display, f"Measurement Active | Reference: {KNOWN_WASHER_WIDTH_MM}mm",
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        cv2.imshow("Square Washer Measurement System", display)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        elif key == ord("s"):
            filename = f"../output/snapshot_{int(time.time())}.jpg"
            cv2.imwrite(filename, display)
            print(f"[INFO] Saved: {filename}")
    
    cap.release()
    cv2.destroyAllWindows()
    print("[INFO] Measurement system closed")

if __name__ == "__main__":
    main()
