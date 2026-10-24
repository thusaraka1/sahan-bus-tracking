"""
Database module for the AI-Powered Bus Tracking System.
Handles SQLite operations for storing bus locations, routes, and stops.
"""

import sqlite3
import os
import json
from datetime import datetime, timedelta


DATABASE_PATH = os.environ.get("DATABASE_PATH", "data/bus_tracking.db")


def get_db():
    """Get a database connection."""
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Initialize the database schema and seed data."""
    conn = get_db()
    cursor = conn.cursor()

    # Create tables
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS routes (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            color TEXT DEFAULT '#3B82F6',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS stops (
            id TEXT PRIMARY KEY,
            route_id TEXT NOT NULL,
            name TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            stop_order INTEGER NOT NULL,
            FOREIGN KEY (route_id) REFERENCES routes(id)
        );

        CREATE TABLE IF NOT EXISTS buses (
            id TEXT PRIMARY KEY,
            route_id TEXT NOT NULL,
            name TEXT NOT NULL,
            status TEXT DEFAULT 'inactive',
            FOREIGN KEY (route_id) REFERENCES routes(id)
        );

        CREATE TABLE IF NOT EXISTS location_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bus_id TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            speed REAL DEFAULT 0,
            heading REAL DEFAULT 0,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (bus_id) REFERENCES buses(id)
        );

        CREATE TABLE IF NOT EXISTS eta_predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bus_id TEXT NOT NULL,
            stop_id TEXT NOT NULL,
            predicted_eta_minutes REAL NOT NULL,
            distance_km REAL,
            confidence REAL DEFAULT 0.85,
            predicted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (bus_id) REFERENCES buses(id),
            FOREIGN KEY (stop_id) REFERENCES stops(id)
        );

        CREATE TABLE IF NOT EXISTS active_learning_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bus_id TEXT NOT NULL,
            route_id TEXT NOT NULL,
            from_stop TEXT NOT NULL,
            to_stop TEXT NOT NULL,
            segment_distance_km REAL,
            avg_speed_kmh REAL,
            hour_of_day INTEGER,
            day_of_week INTEGER,
            congestion_factor REAL,
            predicted_eta_minutes REAL,
            actual_travel_time_minutes REAL,
            error_minutes REAL,
            samples_learned_total INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Seed sample route data (Colombo area - Sri Lanka)
    # Check if routes already exist
    existing = cursor.execute("SELECT COUNT(*) FROM routes").fetchone()[0]
    if existing == 0:
        _seed_sample_data(cursor)

    conn.commit()
    conn.close()
    seed_hardware_route()
    print("[DB] Database initialized successfully")


def seed_hardware_route():
    """Ensure Route 04 (Colombo Fort <-> Chilaw) and ESP32 hardware bus are present in DB."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        # Route 04
        cursor.execute("SELECT id FROM routes WHERE id = 'ROUTE_04'")
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO routes (id, name, color) VALUES (?, ?, ?)",
                ("ROUTE_04", "Route 04: Colombo Fort - Chilaw", "#10B981")
            )
            route_04_stops = [
                ("STOP_04_1", "ROUTE_04", "Colombo Fort Bus Stand", 6.9344, 79.8520, 1),
                ("STOP_04_2", "ROUTE_04", "Peliyagoda Junction", 6.9614, 79.8831, 2),
                ("STOP_04_3", "ROUTE_04", "Wattala", 6.9902, 79.8911, 3),
                ("STOP_04_4", "ROUTE_04", "Kandana", 7.0478, 79.8943, 4),
                ("STOP_04_5", "ROUTE_04", "Ja-Ela Bus Stand", 7.0747, 79.8917, 5),
                ("STOP_04_6", "ROUTE_04", "Seeduwa", 7.1367, 79.8833, 6),
                ("STOP_04_7", "ROUTE_04", "Negombo Central Bus Stand", 7.2094, 79.8386, 7),
                ("STOP_04_8", "ROUTE_04", "Kochchikade", 7.2612, 79.8601, 8),
                ("STOP_04_9", "ROUTE_04", "Wennappuwa", 7.3385, 79.8385, 9),
                ("STOP_04_10", "ROUTE_04", "Marawila", 7.4124, 79.8228, 10),
                ("STOP_04_11", "ROUTE_04", "Mahawewa", 7.4724, 79.8189, 11),
                ("STOP_04_12", "ROUTE_04", "Madampe", 7.5028, 79.8402, 12),
                ("STOP_04_13", "ROUTE_04", "Chilaw Bus Stand", 7.5758, 79.7953, 13),
            ]
            for s in route_04_stops:
                cursor.execute(
                    "INSERT OR REPLACE INTO stops (id, route_id, name, latitude, longitude, stop_order) "
                    "VALUES (?, ?, ?, ?, ?, ?)", s
                )
        # Ensure hardware bus is mapped to Route 04
        cursor.execute(
            "INSERT OR REPLACE INTO buses (id, route_id, name, status) VALUES (?, ?, ?, 'active')",
            ("lee_bus_esp32_001", "ROUTE_04", "My Bus (ESP32 Live Tracker)")
        )
        conn.commit()
    finally:
        conn.close()


def _seed_sample_data(cursor):
    """Seed the database with sample routes, stops, and buses."""

    # Route A: Colombo Fort → Kandy (simplified with key stops)
    cursor.execute(
        "INSERT INTO routes (id, name, color) VALUES (?, ?, ?)",
        ("ROUTE_A", "Colombo - Kandy Express", "#3B82F6")
    )

    route_a_stops = [
        ("STOP_A1", "ROUTE_A", "Colombo Fort Bus Stand", 6.9344, 79.8428, 1),
        ("STOP_A2", "ROUTE_A", "Pettah Bus Terminal", 6.9367, 79.8500, 2),
        ("STOP_A3", "ROUTE_A", "Maradana Junction", 6.9292, 79.8617, 3),
        ("STOP_A4", "ROUTE_A", "Kadawatha", 7.0014, 79.9536, 4),
        ("STOP_A5", "ROUTE_A", "Kadugannawa", 7.2547, 80.5244, 5),
        ("STOP_A6", "ROUTE_A", "Peradeniya", 7.2686, 80.5953, 6),
        ("STOP_A7", "ROUTE_A", "Kandy Bus Stand", 7.2931, 80.6350, 7),
    ]

    # Route B: Colombo → Galle (coastal route)
    cursor.execute(
        "INSERT INTO routes (id, name, color) VALUES (?, ?, ?)",
        ("ROUTE_B", "Colombo - Galle Coastal", "#10B981")
    )

    route_b_stops = [
        ("STOP_B1", "ROUTE_B", "Colombo Fort Bus Stand", 6.9344, 79.8428, 1),
        ("STOP_B2", "ROUTE_B", "Bambalapitiya Junction", 6.8897, 79.8561, 2),
        ("STOP_B3", "ROUTE_B", "Mount Lavinia", 6.8381, 79.8650, 3),
        ("STOP_B4", "ROUTE_B", "Panadura", 6.7139, 79.9044, 4),
        ("STOP_B5", "ROUTE_B", "Aluthgama", 6.4319, 80.0008, 5),
        ("STOP_B6", "ROUTE_B", "Hikkaduwa", 6.1400, 80.1050, 6),
        ("STOP_B7", "ROUTE_B", "Galle Bus Stand", 6.0328, 80.2150, 7),
    ]

    # Route C: Colombo → Negombo
    cursor.execute(
        "INSERT INTO routes (id, name, color) VALUES (?, ?, ?)",
        ("ROUTE_C", "Colombo - Negombo", "#F59E0B")
    )

    route_c_stops = [
        ("STOP_C1", "ROUTE_C", "Colombo Fort Bus Stand", 6.9344, 79.8428, 1),
        ("STOP_C2", "ROUTE_C", "Peliyagoda", 6.9614, 79.8831, 2),
        ("STOP_C3", "ROUTE_C", "Ja-Ela", 7.0747, 79.8917, 3),
        ("STOP_C4", "ROUTE_C", "Seeduwa", 7.1367, 79.8833, 4),
        ("STOP_C5", "ROUTE_C", "Negombo Bus Stand", 7.2094, 79.8386, 5),
    ]

    for stop in route_a_stops + route_b_stops + route_c_stops:
        cursor.execute(
            "INSERT INTO stops (id, route_id, name, latitude, longitude, stop_order) "
            "VALUES (?, ?, ?, ?, ?, ?)", stop
        )

    # Sample buses
    buses = [
        ("BUS_001", "ROUTE_A", "Colombo-Kandy Express #1"),
        ("BUS_002", "ROUTE_A", "Colombo-Kandy Express #2"),
        ("BUS_003", "ROUTE_B", "Galle Coastal #1"),
        ("BUS_004", "ROUTE_B", "Galle Coastal #2"),
        ("BUS_005", "ROUTE_C", "Negombo Shuttle #1"),
    ]

    for bus in buses:
        cursor.execute(
            "INSERT INTO buses (id, route_id, name, status) VALUES (?, ?, ?, 'active')",
            bus
        )

    print("[DB] Sample data seeded")


def save_location(bus_id, latitude, longitude, speed, heading, timestamp=None):
    """Save a bus location update to the database."""
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO location_history (bus_id, latitude, longitude, speed, heading, timestamp) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (bus_id, latitude, longitude, speed, heading, timestamp or datetime.utcnow().isoformat())
        )
        # Update bus status
        conn.execute(
            "UPDATE buses SET status = 'active' WHERE id = ?",
            (bus_id,)
        )
        conn.commit()
    finally:
        conn.close()


def save_eta_prediction(bus_id, stop_id, eta_minutes, distance_km, confidence):
    """Save an ETA prediction."""
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO eta_predictions (bus_id, stop_id, predicted_eta_minutes, distance_km, confidence) "
            "VALUES (?, ?, ?, ?, ?)",
            (bus_id, stop_id, eta_minutes, distance_km, confidence)
        )
        conn.commit()
    finally:
        conn.close()


def get_routes():
    """Get all routes with their stops."""
    conn = get_db()
    try:
        routes = conn.execute("SELECT * FROM routes ORDER BY name").fetchall()
        result = []
        for route in routes:
            stops = conn.execute(
                "SELECT * FROM stops WHERE route_id = ? ORDER BY stop_order",
                (route["id"],)
            ).fetchall()
            result.append({
                "id": route["id"],
                "name": route["name"],
                "color": route["color"],
                "stops": [dict(s) for s in stops]
            })
        return result
    finally:
        conn.close()


def get_buses():
    """Get all buses with their current status."""
    conn = get_db()
    try:
        buses = conn.execute("""
            SELECT b.*, r.name as route_name, r.color as route_color
            FROM buses b
            JOIN routes r ON b.route_id = r.id
            ORDER BY b.id
        """).fetchall()
        return [dict(b) for b in buses]
    finally:
        conn.close()


def get_bus_location_history(bus_id, limit=100):
    """Get recent location history for a bus."""
    conn = get_db()
    try:
        history = conn.execute(
            "SELECT * FROM location_history WHERE bus_id = ? ORDER BY timestamp DESC LIMIT ?",
            (bus_id, limit)
        ).fetchall()
        return [dict(h) for h in history]
    finally:
        conn.close()


def get_stops_for_route(route_id):
    """Get all stops for a specific route, ordered."""
    conn = get_db()
    try:
        stops = conn.execute(
            "SELECT * FROM stops WHERE route_id = ? ORDER BY stop_order",
            (route_id,)
        ).fetchall()
        return [dict(s) for s in stops]
    finally:
        conn.close()


def get_analytics():
    """Get system analytics data."""
    conn = get_db()
    try:
        total_buses = conn.execute("SELECT COUNT(*) FROM buses").fetchone()[0]
        active_buses = conn.execute("SELECT COUNT(*) FROM buses WHERE status = 'active'").fetchone()[0]
        total_routes = conn.execute("SELECT COUNT(*) FROM routes").fetchone()[0]
        total_stops = conn.execute("SELECT COUNT(*) FROM stops").fetchone()[0]
        total_locations = conn.execute("SELECT COUNT(*) FROM location_history").fetchone()[0]

        # Recent predictions
        recent_preds = conn.execute("""
            SELECT AVG(predicted_eta_minutes) as avg_eta, AVG(confidence) as avg_confidence
            FROM eta_predictions
            WHERE predicted_at > datetime('now', '-1 hour')
        """).fetchone()

        return {
            "total_buses": total_buses,
            "active_buses": active_buses,
            "total_routes": total_routes,
            "total_stops": total_stops,
            "total_location_records": total_locations,
            "avg_eta_minutes": round(recent_preds["avg_eta"] or 0, 1),
            "avg_confidence": round((recent_preds["avg_confidence"] or 0) * 100, 1),
        }
    finally:
        conn.close()


def save_learning_sample(bus_id, route_id, from_stop, to_stop, segment_distance_km,
                         avg_speed_kmh, hour_of_day, day_of_week, congestion_factor,
                         predicted_eta, actual_travel_time, error_minutes, samples_total):
    """Save an active learning event (predicted vs ground truth travel time)."""
    conn = get_db()
    try:
        conn.execute("""
            INSERT INTO active_learning_logs (
                bus_id, route_id, from_stop, to_stop, segment_distance_km,
                avg_speed_kmh, hour_of_day, day_of_week, congestion_factor,
                predicted_eta_minutes, actual_travel_time_minutes,
                error_minutes, samples_learned_total
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            bus_id, route_id, from_stop, to_stop, segment_distance_km,
            avg_speed_kmh, hour_of_day, day_of_week, congestion_factor,
            predicted_eta, actual_travel_time, error_minutes, samples_total
        ))
        conn.commit()
    finally:
        conn.close()


def get_learning_history(limit=50):
    """Get the recent stream of actively learned trip segments."""
    conn = get_db()
    try:
        rows = conn.execute("""
            SELECT * FROM active_learning_logs
            ORDER BY id DESC
            LIMIT ?
        """, (limit,)).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_learning_metrics():
    """Get aggregated metrics on AI learning progression and MAE."""
    conn = get_db()
    try:
        row = conn.execute("""
            SELECT 
                COUNT(*) as total_samples,
                AVG(error_minutes) as overall_mae,
                MIN(error_minutes) as min_error,
                MAX(error_minutes) as max_error
            FROM active_learning_logs
        """).fetchone()

        # Recent MAE (last 20 samples) vs Earlier MAE
        recent_row = conn.execute("""
            SELECT AVG(error_minutes) as recent_mae
            FROM (
                SELECT error_minutes FROM active_learning_logs
                ORDER BY id DESC LIMIT 20
            )
        """).fetchone()

        return {
            "total_samples": row["total_samples"] or 0,
            "overall_mae": round(row["overall_mae"] or 0, 2),
            "recent_mae": round(recent_row["recent_mae"] or (row["overall_mae"] or 0), 2),
            "min_error": round(row["min_error"] or 0, 2),
            "max_error": round(row["max_error"] or 0, 2),
        }
    finally:
        conn.close()


def add_route(route_id, name, color='#3B82F6'):
    """Add a new route to the database."""
    conn = get_db()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO routes (id, name, color) VALUES (?, ?, ?)",
            (route_id, name, color)
        )
        conn.commit()
    finally:
        conn.close()


def add_stop(stop_id, route_id, name, latitude, longitude, stop_order):
    """Add a stop to a route."""
    conn = get_db()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO stops (id, route_id, name, latitude, longitude, stop_order) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (stop_id, route_id, name, latitude, longitude, stop_order)
        )
        conn.commit()
    finally:
        conn.close()


def add_bus(bus_id, route_id, name):
    """Add a bus and assign it to a route."""
    conn = get_db()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO buses (id, route_id, name, status) VALUES (?, ?, ?, 'active')",
            (bus_id, route_id, name)
        )
        conn.commit()
    finally:
        conn.close()


def delete_route(route_id):
    """Delete a route and all its associated stops and buses."""
    conn = get_db()
    try:
        # Get bus IDs for this route to clean up related data
        bus_ids = [row[0] for row in conn.execute(
            "SELECT id FROM buses WHERE route_id = ?", (route_id,)
        ).fetchall()]

        # Delete location history for buses on this route
        for bus_id in bus_ids:
            conn.execute("DELETE FROM location_history WHERE bus_id = ?", (bus_id,))
            conn.execute("DELETE FROM eta_predictions WHERE bus_id = ?", (bus_id,))
            conn.execute("DELETE FROM active_learning_logs WHERE bus_id = ?", (bus_id,))

        # Delete stops, buses, and route
        conn.execute("DELETE FROM stops WHERE route_id = ?", (route_id,))
        conn.execute("DELETE FROM buses WHERE route_id = ?", (route_id,))
        conn.execute("DELETE FROM routes WHERE id = ?", (route_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"[DB] Error deleting route {route_id}: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def update_bus_route(bus_id, new_route_id):
    """Update a bus's assigned route."""
    conn = get_db()
    try:
        # Verify the route exists
        route = conn.execute("SELECT id FROM routes WHERE id = ?", (new_route_id,)).fetchone()
        if not route:
            return False, "Route not found"
        conn.execute(
            "UPDATE buses SET route_id = ? WHERE id = ?",
            (new_route_id, bus_id)
        )
        conn.commit()
        return True, "Route updated successfully"
    except Exception as e:
        print(f"[DB] Error updating bus route: {e}")
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()


def get_route_count():
    """Get the current number of routes."""
    conn = get_db()
    try:
        return conn.execute("SELECT COUNT(*) FROM routes").fetchone()[0]
    finally:
        conn.close()

