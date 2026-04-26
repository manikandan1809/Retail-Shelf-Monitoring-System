# 🛒 Retail Shelf Monitoring System (RSMS)

> A real-time AI-powered shelf monitoring dashboard that uses computer vision to detect stock levels, raise alerts, and help retail staff restock shelves — all from a live web interface.

---

## 📌 Project Description

The **Retail Shelf Monitoring System (RSMS)** is a full-stack computer vision project designed for smart retail environments. It simulates a real-time shelf scanning pipeline where a camera captures shelf images, an AI model (YOLOv8) detects products, and a web dashboard displays live inventory status across 6 shelf zones.

The system automatically:
- Scans shelves every 5 seconds using a background thread
- Detects product quantities using a YOLO-style pipeline
- Flags **LOW STOCK** and **OUT OF STOCK** conditions
- Raises and stores alerts in a database
- Lets staff manually restock items from the dashboard

---

## 🖥️ Live Dashboard Features

| Feature | Description |
|---|---|
| 📊 Stat Cards | Total products, In Stock, Low Stock, Out of Stock counts |
| 🗂️ Zone View | 6 shelf zones (A1–C2) with per-product status pills |
| 🔔 Active Alerts | Real-time LOW/OUT alerts with one-click Resolve |
| 📈 Inventory Chart | Bar chart (Chart.js) with color-coded stock levels |
| 🎯 Confidence Bars | Detection confidence % per product |
| 🔄 Manual Restock | Dropdown + quantity input to update stock instantly |
| ⏱️ Auto Refresh | Dashboard polls API every 5 seconds |

---

## 🗂️ Zone Layout

```
Zone A1 → Beverages    (Coca-Cola, Pepsi)
Zone A2 → Snacks       (Lays, Oreo)
Zone B1 → Dairy+Bakery (Butter, Bread)
Zone B2 → Instant      (Maggi Noodles)
Zone C1 → Personal     (Dove, Colgate)
Zone C2 → Beverages    (Red Bull)
```

---

## 🧠 How It Works — Step by Step

```
Camera captures shelf image
        ↓
preprocess_frame()  →  Resize + GaussianBlur + CLAHE contrast boost
        ↓
segment_shelf_zones()  →  Split frame into 6 grid zones
        ↓
YOLOv8 detects products  →  Bounding boxes + confidence scores
        ↓
confidence check > 60%
        ↓
status = ok / low / out  →  Save to SQLite DB
        ↓
raise_alerts()  →  Create LOW_STOCK or OUT_OF_STOCK alert
        ↓
Flask API serves data  →  Dashboard auto-refreshes every 5 seconds
```

---

## 🔬 ML & Computer Vision Techniques

### 🎯 Object Detection — YOLOv8
- Single-pass detection across entire shelf zone
- Outputs bounding box + class label + confidence score per product
- Faster and more accurate than traditional Haar Cascade methods
- Production: plug in `ultralytics` YOLO with a custom-trained `.pt` model

### 🖼️ Image Preprocessing Pipeline
1. **Resize** → Standard 640×480 resolution
2. **Gaussian Blur** → Noise reduction
3. **CLAHE** → Contrast Limited Adaptive Histogram Equalization (on LAB L-channel)
4. **Canny Edge Detection** → Product boundary detection

### 🧱 CNN — Image Classification
- Convolutional layers learn spatial features (shapes, colors, patterns)
- Max pooling for spatial reduction
- Feature maps recognize products even when partially hidden or tilted

### 🚨 Rule-Based Alert Engine
- `qty == 0` → `OUT_OF_STOCK` alert
- `0 < qty < min_stock` → `LOW_STOCK` alert
- Duplicate prevention: skips re-alerting already active SKUs
- Alerts stored in SQLite, resolvable from dashboard

---

## 🏗️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python, Flask 3.0 |
| **Computer Vision** | OpenCV 4.9, NumPy 1.26 |
| **ML / Detection** | YOLOv8 (ultralytics), PyTorch 2.2 |
| **Database** | SQLite3 (built-in, no setup needed) |
| **Frontend** | HTML5, CSS3, Vanilla JS |
| **Charts** | Chart.js 4.4 |
| **Concurrency** | Python `threading` (background scanner) |

---

## 📁 Project Structure

```
rsms/
├── app.py              # Flask server + REST API + HTML dashboard
├── database.py         # SQLite schema, CRUD helpers, seed data
├── detector.py         # CV pipeline: preprocess → detect → alert
├── requirements.txt    # Python dependencies
└── rsms_inventory.db   # Auto-generated SQLite database
```

---

## 🚀 Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/rsms.git
cd rsms
```

### 2. Install Dependencies
```bash
pip install flask opencv-python numpy
# For production with real YOLO:
# pip install ultralytics torch
```

### 3. Run the App
```bash
python app.py
```

### 4. Open Dashboard
```
http://localhost:5000
```

> The background scanner starts automatically. No camera needed in demo mode — the system simulates detections.

---

## 🗄️ Database Schema

```sql
products          → id, name, sku, category, min_stock, price
shelf_inventory   → product_id, shelf_zone, quantity, last_updated
detection_logs    → timestamp, shelf_zone, product_sku, detected_qty, confidence, status
alerts            → timestamp, shelf_zone, product_sku, alert_type, message, resolved
```

---

## 📡 REST API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/inventory` | All products with zone + quantity |
| `GET` | `/api/alerts` | Active (unresolved) alerts |
| `GET` | `/api/stats` | Summary counts (ok/low/out) |
| `POST` | `/api/alerts/:id/resolve` | Mark alert as resolved |
| `POST` | `/api/restock` | Manually update product quantity |

---

## 🧰 Key Skills Demonstrated

### 💻 Computer Vision
- Image preprocessing with OpenCV (resize, blur, CLAHE, edge detection)
- Zone segmentation of shelf images into grid ROIs
- Bounding box drawing with color-coded status labels
- YOLOv8 inference pipeline (production-ready integration point)

### 🤖 Deep Learning & ML
- YOLOv8 object detection architecture (single-pass, real-time)
- CNN-based product image classification
- Confidence score thresholding (>60% to accept detections)
- Custom model training with PyTorch/ultralytics

### 🗃️ Database Design
- Relational SQLite schema design (4 normalized tables)
- CRUD operations with Python `sqlite3`
- Detection log management and alert lifecycle tracking
- JOIN queries for inventory-product aggregation

### 🌐 Backend Development
- Flask REST API with multiple route handlers
- Background threading for non-blocking shelf scans
- JSON serialization and request/response handling
- Modular architecture (app / database / detector separation)

### 🎨 Frontend Development
- Responsive dark-themed dashboard (pure HTML/CSS/JS)
- Real-time polling with `setInterval` every 5 seconds
- Dynamic DOM rendering without any framework
- Chart.js integration for live inventory bar chart

### ⚠️ Alert Systems
- Rule-based anomaly detection engine
- Duplicate alert prevention logic
- Auto-resolve workflow via REST API
- Priority classification (LOW vs OUT)

### 🔧 Software Engineering
- Multithreaded Python application design
- Separation of concerns (3-module architecture)
- Demo mode vs production mode switching
- Configurable thresholds (confidence, low stock limit, scan interval)

---

## ⚙️ Configuration

Inside `detector.py`:
```python
CONFIDENCE_THRESHOLD = 0.60   # Min confidence to accept a detection
LOW_STOCK_THRESHOLD  = 5      # Items below this → LOW_STOCK alert
SCAN_INTERVAL        = 3      # Seconds between shelf scans
```

---

## 🔮 Production Upgrade Path

To switch from simulation to real camera + YOLO:

```python
# In detector.py — replace simulate_detection() with:
from ultralytics import YOLO
model = YOLO("best.pt")      # your custom-trained model
results = model(roi_frame)
for box in results[0].boxes:
    # parse class, confidence, bounding box
    ...
```

**Hardware needed for production:**
- HD Camera (720p+)
- PC or Raspberry Pi
- Wi-Fi / Ethernet
- GPU (recommended for YOLO training)

---

## 🧪 Demo Data

The system auto-seeds 10 products across 6 zones on first run:

| SKU | Product | Zone | Initial Qty |
|---|---|---|---|
| CC-500 | Coca-Cola 500ml | A1 | 12 |
| PP-500 | Pepsi 500ml | A1 | 3 ⚠️ |
| LC-100 | Lays Chips | A2 | 7 |
| OR-200 | Oreo Biscuits | A2 | 0 🚨 |
| BB-400 | Britannia Bread | B1 | 5 |
| AB-100 | Amul Butter | B1 | 2 ⚠️ |
| MN-70 | Maggi Noodles | B2 | 15 |
| DS-200 | Dove Shampoo | C1 | 1 ⚠️ |
| CT-150 | Colgate 150g | C1 | 8 |
| RB-250 | Red Bull 250ml | C2 | 4 ⚠️ |



 ⭐ If you found this project useful, give it a star on GitHub!
