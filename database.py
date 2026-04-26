"""
database.py — Retail Shelf Monitoring System
SQLite-based inventory & alert management
"""

import sqlite3
import json
from datetime import datetime

DB_PATH = "rsms_inventory.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create all tables and seed demo data."""
    conn = get_connection()
    c = conn.cursor()

    # Products table
    c.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            sku         TEXT UNIQUE NOT NULL,
            category    TEXT,
            min_stock   INTEGER DEFAULT 5,
            price       REAL DEFAULT 0.0
        )
    """)

    # Shelf inventory table
    c.execute("""
        CREATE TABLE IF NOT EXISTS shelf_inventory (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id  INTEGER REFERENCES products(id),
            shelf_zone  TEXT,          -- e.g. 'A1', 'B2'
            quantity    INTEGER DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Detection logs table
    c.execute("""
        CREATE TABLE IF NOT EXISTS detection_logs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            shelf_zone  TEXT,
            product_sku TEXT,
            detected_qty INTEGER,
            confidence  REAL,
            status      TEXT       -- 'ok', 'low_stock', 'out_of_stock', 'misplaced'
        )
    """)

    # Alerts table
    c.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            shelf_zone  TEXT,
            product_sku TEXT,
            alert_type  TEXT,      -- 'LOW_STOCK', 'OUT_OF_STOCK', 'MISPLACED'
            message     TEXT,
            resolved    INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    _seed_demo_data(c, conn)
    conn.close()
    print("[DB] Database initialized successfully.")


def _seed_demo_data(c, conn):
    """Insert demo products and inventory if empty."""
    c.execute("SELECT COUNT(*) FROM products")
    if c.fetchone()[0] > 0:
        return  # already seeded

    products = [
        ("Coca-Cola 500ml",   "CC-500",  "Beverages",  8,  1.50),
        ("Pepsi 500ml",       "PP-500",  "Beverages",  8,  1.40),
        ("Lays Chips 100g",   "LC-100",  "Snacks",     6,  0.99),
        ("Oreo Biscuits",     "OR-200",  "Snacks",     5,  1.25),
        ("Britannia Bread",   "BB-400",  "Bakery",     4,  1.10),
        ("Amul Butter 100g",  "AB-100",  "Dairy",      5,  1.80),
        ("Maggi Noodles",     "MN-70",   "Instant",    10, 0.75),
        ("Dove Shampoo",      "DS-200",  "Personal",   4,  3.50),
        ("Colgate 150g",      "CT-150",  "Personal",   5,  2.00),
        ("Red Bull 250ml",    "RB-250",  "Beverages",  6,  2.80),
    ]

    c.executemany(
        "INSERT INTO products (name, sku, category, min_stock, price) VALUES (?,?,?,?,?)",
        products
    )

    inventory = [
        (1, "A1", 12), (2, "A1", 3),  (3, "A2", 7),
        (4, "A2", 0),  (5, "B1", 5),  (6, "B1", 2),
        (7, "B2", 15), (8, "C1", 1),  (9, "C1", 8),
        (10,"C2", 4),
    ]
    c.executemany(
        "INSERT INTO shelf_inventory (product_id, shelf_zone, quantity) VALUES (?,?,?)",
        inventory
    )
    conn.commit()


# ─── CRUD helpers ─────────────────────────────────────────────────────────────

def get_all_inventory():
    conn = get_connection()
    rows = conn.execute("""
        SELECT p.name, p.sku, p.category, p.min_stock, p.price,
               si.shelf_zone, si.quantity, si.last_updated
        FROM shelf_inventory si
        JOIN products p ON si.product_id = p.id
        ORDER BY si.shelf_zone, p.name
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_quantity(sku, shelf_zone, new_qty):
    conn = get_connection()
    conn.execute("""
        UPDATE shelf_inventory
        SET quantity = ?, last_updated = CURRENT_TIMESTAMP
        WHERE product_id = (SELECT id FROM products WHERE sku = ?)
          AND shelf_zone = ?
    """, (new_qty, sku, shelf_zone))
    conn.commit()
    conn.close()


def log_detection(shelf_zone, product_sku, detected_qty, confidence, status):
    conn = get_connection()
    conn.execute("""
        INSERT INTO detection_logs (shelf_zone, product_sku, detected_qty, confidence, status)
        VALUES (?, ?, ?, ?, ?)
    """, (shelf_zone, product_sku, detected_qty, confidence, status))
    conn.commit()
    conn.close()


def create_alert(shelf_zone, product_sku, alert_type, message):
    conn = get_connection()
    conn.execute("""
        INSERT INTO alerts (shelf_zone, product_sku, alert_type, message)
        VALUES (?, ?, ?, ?)
    """, (shelf_zone, product_sku, alert_type, message))
    conn.commit()
    conn.close()


def get_active_alerts():
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM alerts WHERE resolved = 0 ORDER BY timestamp DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def resolve_alert(alert_id):
    conn = get_connection()
    conn.execute("UPDATE alerts SET resolved = 1 WHERE id = ?", (alert_id,))
    conn.commit()
    conn.close()


def get_detection_stats():
    conn = get_connection()
    stats = conn.execute("""
        SELECT status, COUNT(*) as count
        FROM detection_logs
        GROUP BY status
    """).fetchall()
    conn.close()
    return {r["status"]: r["count"] for r in stats}
