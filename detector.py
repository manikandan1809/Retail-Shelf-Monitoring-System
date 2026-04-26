"""
detector.py — Retail Shelf Monitoring System
Core detection engine using OpenCV + simulated YOLOv8-style pipeline.

In production: swap simulate_detection() with real YOLOv8 inference:
    from ultralytics import YOLO
    model = YOLO("yolov8n.pt")
    results = model(frame)
"""

import cv2
import numpy as np
import random
import time
from datetime import datetime
from database import (
    get_all_inventory, update_quantity, log_detection,
    create_alert, get_active_alerts
)


# ─── CONFIG ───────────────────────────────────────────────────────────────────
CONFIDENCE_THRESHOLD = 0.60   # Minimum confidence to accept detection
LOW_STOCK_THRESHOLD  = 5      # Below this → LOW_STOCK alert
SCAN_INTERVAL        = 3      # Seconds between shelf scans


# ─── IMAGE PREPROCESSING ──────────────────────────────────────────────────────

def preprocess_frame(frame: np.ndarray) -> np.ndarray:
    """
    Full preprocessing pipeline before detection:
    1. Resize to standard resolution
    2. Convert to grayscale (optional branch)
    3. Apply Gaussian blur for noise reduction
    4. Enhance contrast with CLAHE
    """
    # Step 1: Resize to 640×480 standard
    frame = cv2.resize(frame, (640, 480))

    # Step 2: Noise reduction — Gaussian blur
    blurred = cv2.GaussianBlur(frame, (3, 3), 0)

    # Step 3: CLAHE for contrast enhancement (on L channel of LAB)
    lab   = cv2.cvtColor(blurred, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l     = clahe.apply(l)
    enhanced = cv2.merge((l, a, b))
    enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)

    return enhanced


def detect_edges(frame: np.ndarray) -> np.ndarray:
    """Canny edge detection to find product boundaries."""
    gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, threshold1=50, threshold2=150)
    return edges


def segment_shelf_zones(frame: np.ndarray):
    """
    Divide the shelf image into zones (A1, A2, B1 …)
    Returns list of (zone_name, roi_frame) tuples.
    """
    h, w = frame.shape[:2]
    rows, cols = 3, 2          # 3-row × 2-col grid
    rh, rw = h // rows, w // cols
    zones = []
    zone_labels = ["A1","A2","B1","B2","C1","C2"]
    idx = 0
    for r in range(rows):
        for c in range(cols):
            roi = frame[r*rh:(r+1)*rh, c*rw:(c+1)*rw]
            zones.append((zone_labels[idx], roi))
            idx += 1
    return zones


# ─── DETECTION ENGINE ─────────────────────────────────────────────────────────

def simulate_detection(zone_name: str, inventory: list) -> list:
    """
    Simulates YOLOv8 bounding-box detections for a shelf zone.
    
    In production, replace this with:
        model = YOLO('yolov8n.pt')
        results = model(roi_frame)
        for box in results[0].boxes:
            ...
    
    Returns list of detection dicts.
    """
    zone_items = [i for i in inventory if i["shelf_zone"] == zone_name]
    detections = []

    for item in zone_items:
        # Simulate confidence with slight noise around real quantity
        noise       = random.uniform(-1.5, 1.5)
        detected_qty = max(0, int(item["quantity"] + noise))
        confidence   = round(random.uniform(0.72, 0.98), 2)

        if confidence < CONFIDENCE_THRESHOLD:
            continue  # Skip low-confidence detections

        # Determine stock status
        if detected_qty == 0:
            status = "out_of_stock"
        elif detected_qty < item["min_stock"]:
            status = "low_stock"
        else:
            status = "ok"

        detections.append({
            "sku":          item["sku"],
            "name":         item["name"],
            "zone":         zone_name,
            "detected_qty": detected_qty,
            "confidence":   confidence,
            "status":       status,
        })

    return detections


def draw_detections(frame: np.ndarray, detections: list) -> np.ndarray:
    """
    Draw bounding boxes and labels on the shelf frame.
    Color coding:
        Green  → OK stock
        Orange → Low stock
        Red    → Out of stock
    """
    h, w = frame.shape[:2]
    box_w, box_h = w // max(len(detections), 1), 80

    COLOR = {
        "ok":           (0, 200, 80),
        "low_stock":    (0, 165, 255),
        "out_of_stock": (0, 0, 220),
    }

    for i, det in enumerate(detections):
        x1 = (i % 4) * (w // 4)
        y1 = (i // 4) * 100
        x2, y2 = x1 + box_w - 10, y1 + box_h

        color = COLOR.get(det["status"], (200, 200, 200))
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

        label = f"{det['name'][:12]} | qty:{det['detected_qty']} | {det['confidence']:.0%}"
        cv2.putText(frame, label, (x1 + 4, y1 + 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)

    return frame


# ─── ALERT ENGINE ─────────────────────────────────────────────────────────────

def raise_alerts(detections: list):
    """Create alerts in DB for any anomalies detected."""
    existing = {a["product_sku"] for a in get_active_alerts()}

    for det in detections:
        if det["sku"] in existing:
            continue  # Don't duplicate active alerts

        if det["status"] == "out_of_stock":
            create_alert(
                det["zone"], det["sku"], "OUT_OF_STOCK",
                f"🚨 {det['name']} is OUT OF STOCK at zone {det['zone']}!"
            )
        elif det["status"] == "low_stock":
            create_alert(
                det["zone"], det["sku"], "LOW_STOCK",
                f"⚠️ {det['name']} is LOW ({det['detected_qty']} left) at zone {det['zone']}"
            )


# ─── MAIN MONITORING LOOP ─────────────────────────────────────────────────────

def run_monitoring(use_camera=False, demo_mode=True):
    """
    Main shelf monitoring loop.

    Args:
        use_camera: If True, uses webcam (index 0). If False, uses blank canvas.
        demo_mode:  If True, uses simulated detections (no real YOLO model needed).
    """
    from database import init_db
    init_db()

    cap = None
    if use_camera:
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("[WARN] Camera not found — switching to demo mode.")
            use_camera = False

    print("[RSMS] Monitoring started. Press Q to quit.")

    while True:
        # ── Get frame ──
        if use_camera:
            ret, frame = cap.read()
            if not ret:
                break
        else:
            # Blank canvas simulating a shelf image
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            frame[:] = (30, 30, 50)

        # ── Preprocess ──
        processed = preprocess_frame(frame)

        # ── Get latest inventory from DB ──
        inventory = get_all_inventory()

        # ── Zone segmentation & detection ──
        zones = segment_shelf_zones(processed)
        all_detections = []

        for zone_name, roi in zones:
            if demo_mode:
                detections = simulate_detection(zone_name, inventory)
            else:
                # ── PRODUCTION: Real YOLOv8 ──
                # from ultralytics import YOLO
                # model = YOLO("best.pt")   # your trained model
                # results = model(roi)
                # detections = parse_yolo_results(results, zone_name)
                detections = simulate_detection(zone_name, inventory)

            all_detections.extend(detections)

            # Log each detection
            for det in detections:
                log_detection(
                    det["zone"], det["sku"],
                    det["detected_qty"], det["confidence"],
                    det["status"]
                )
                # Update inventory in DB
                update_quantity(det["sku"], det["zone"], det["detected_qty"])

        # ── Raise alerts ──
        raise_alerts(all_detections)

        # ── Draw results ──
        output = draw_detections(processed.copy(), all_detections)

        # ── Status overlay ──
        ok_count  = sum(1 for d in all_detections if d["status"] == "ok")
        low_count = sum(1 for d in all_detections if d["status"] == "low_stock")
        out_count = sum(1 for d in all_detections if d["status"] == "out_of_stock")

        cv2.putText(output, f"RSMS | {datetime.now().strftime('%H:%M:%S')}",
                    (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255,255,255), 1)
        cv2.putText(output, f"OK:{ok_count}  LOW:{low_count}  OUT:{out_count}",
                    (10, 44), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (100,255,100), 1)

        print(f"[{datetime.now().strftime('%H:%M:%S')}] Scanned — "
              f"OK:{ok_count} | Low:{low_count} | Out:{out_count}")

        # cv2.imshow("RSMS — Shelf Monitor", output)
        # if cv2.waitKey(1) & 0xFF == ord('q'):
        #     break

        time.sleep(SCAN_INTERVAL)

    if cap:
        cap.release()
    cv2.destroyAllWindows()
    print("[RSMS] Monitoring stopped.")


if __name__ == "__main__":
    run_monitoring(use_camera=False, demo_mode=True)
