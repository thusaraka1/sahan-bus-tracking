"""
AI-Powered IoT Bus Tracking System - Flask Backend Server

Main application entry point. This server:
1. Subscribes to HiveMQ Cloud MQTT broker for real-time bus data from ESP32 devices
2. Processes incoming GPS data and stores it in SQLite
3. Runs ML-based ETA prediction on incoming data
4. Serves REST API for the React frontend
5. Pushes real-time updates to frontend via WebSocket (Socket.IO)
6. Includes a bus simulator for testing without hardware
"""

import os
import sys
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)
    except Exception:
        pass
if hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)
    except Exception:
        pass
import json
import ssl
import threading
import urllib.request
import urllib.parse
from datetime import datetime

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO
from dotenv import load_dotenv
import paho.mqtt.client as mqtt

from database import init_db, save_location, save_eta_prediction, get_routes, get_buses, \
    get_bus_location_history, get_stops_for_route, get_analytics, \
    save_learning_sample, get_learning_history, get_learning_metrics, \
    add_route, add_stop, add_bus, delete_route, get_route_count, update_bus_route
from ml_model import ETAPredictor
from simulator import BusSimulator

# ============================================================
# Configuration
# ============================================================

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "bus-tracking-secret")
CORS(app, resources={r"/api/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

# MQTT Configuration
MQTT_BROKER = os.environ.get("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.environ.get("MQTT_PORT", 8883))
MQTT_USERNAME = os.environ.get("MQTT_USERNAME", "")
MQTT_PASSWORD = os.environ.get("MQTT_PASSWORD", "")
GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "")

# Global state
eta_predictor = ETAPredictor()
mqtt_clients = []
mqtt_client = None
bus_simulator = None
live_bus_data = {}  # In-memory cache of latest bus positions
bus_trip_tracker = {}  # Tracks bus stop-to-stop movements for active learning
bus_last_position = {}  # Tracks previous GPS position per bus for speed calculation


def _haversine_km(lat1, lon1, lat2, lon2):
    """Calculate distance between two GPS points in kilometers using Haversine formula."""
    from math import radians, sin, cos, sqrt, atan2
    R = 6371.0  # Earth radius in km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))

# ============================================================
# MQTT Handlers (HiveMQ Cloud)
# ============================================================

def make_on_mqtt_connect(broker_name):
    def on_mqtt_connect(client, userdata, flags, rc, properties=None):
        """Callback when connected to HiveMQ Cloud."""
        if rc == 0:
            print(f"[MQTT] Connected to HiveMQ Cloud ({broker_name}) successfully!")
            # Subscribe to standard bus telemetry, status, and custom sensor topics
            client.subscribe("bus/+/location", qos=1)
            client.subscribe("bus/+/status", qos=1)
            client.subscribe("bus/#", qos=1)
            client.subscribe("lee_bus/#", qos=1)
            client.subscribe("lee_bus/sensors", qos=1)
            print(f"[MQTT] [{broker_name}] Subscribed to bus/# and lee_bus/# topics")
        else:
            print(f"[MQTT] [{broker_name}] Connection failed with code {rc}")
    return on_mqtt_connect


def on_mqtt_message(client, userdata, msg):
    """Process incoming MQTT messages from ESP32 devices."""
    try:
        topic = msg.topic
        raw_payload = msg.payload.decode('utf-8', errors='replace')
        print(f"\n[MQTT INCOMING] Broker message received on topic: '{topic}' ({len(raw_payload)} bytes)")
        payload = json.loads(raw_payload)

        # Handle location and sensor updates
        if "/location" in topic or "sensors" in topic or "lee_bus" in topic or "latitude" in payload or "gps" in payload:
            process_bus_location(payload)
        elif "/status" in topic:
            bus_id = payload.get("bus_id", topic.split("/")[1] if "/" in topic else "unknown")
            print(f"[MQTT STATUS] Bus {bus_id} status: {payload.get('status')}")
        else:
            print(f"[MQTT INFO] Topic '{topic}': {payload}")

    except json.JSONDecodeError:
        print(f"[MQTT] Invalid JSON on {msg.topic}: {msg.payload[:100]}")
    except Exception as e:
        print(f"[MQTT] Error processing message on {msg.topic}: {e}")


def on_mqtt_disconnect(client, userdata, rc, properties=None):
    """Handle MQTT disconnection."""
    if rc != 0:
        print(f"[MQTT] Unexpected disconnection (rc={rc}). Auto-reconnecting in background...")


def setup_mqtt():
    """Initialize and connect to HiveMQ Cloud MQTT broker(s)."""
    global mqtt_client, mqtt_clients
    mqtt_clients = []

    broker_configs = []

    # 1. Primary broker from environment (.env)
    if MQTT_BROKER and MQTT_BROKER != "localhost" and MQTT_USERNAME and "YOUR_CLUSTER" not in MQTT_BROKER:
        broker_configs.append({
            "name": "Cluster-1",
            "host": MQTT_BROKER,
            "port": MQTT_PORT,
            "user": MQTT_USERNAME,
            "pass": MQTT_PASSWORD,
        })

    # 2. Lee Bus Project reference broker
    lee_host = "9ce9a991c31542a49529dd4db804495d.s1.eu.hivemq.cloud"
    if lee_host != MQTT_BROKER:
        broker_configs.append({
            "name": "Cluster-LeeBus",
            "host": lee_host,
            "port": 8883,
            "user": "lee_project",
            "pass": "Lee_project@123",
        })

    if not broker_configs:
        print("[MQTT] No HiveMQ credentials configured. Running in simulation-only mode.")
        mqtt_client = None
        return

    for conf in broker_configs:
        try:
            client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
            client.username_pw_set(conf["user"], conf["pass"])
            client.tls_set(tls_version=ssl.PROTOCOL_TLS)
            client.on_connect = make_on_mqtt_connect(conf["name"])
            client.on_message = on_mqtt_message
            client.on_disconnect = on_mqtt_disconnect

            print(f"[MQTT] Connecting to {conf['name']} ({conf['host']}:{conf['port']})...")
            client.connect(conf["host"], conf["port"], keepalive=60)
            client.loop_start()
            mqtt_clients.append(client)
        except Exception as e:
            print(f"[MQTT] Setup failed for {conf['name']}: {e}")

    if mqtt_clients:
        mqtt_client = mqtt_clients[0]
        print(f"[MQTT] Successfully initialized {len(mqtt_clients)} HiveMQ Cloud listener(s)")
    else:
        mqtt_client = None


# ============================================================
# Data Processing
# ============================================================

def process_bus_location(data):
    """
    Process a bus location and IoT sensor hub update (from MQTT or simulator).
    Seamlessly parses both flat GPS payloads and nested ESP32 sensor objects
    (GPS, MPU6050 Accelerometer/Gyro/Temp, HW-484 Microphone).
    Stores data, runs ETA prediction, and pushes to frontend.
    """
    bus_id = data.get("bus_id") or data.get("device") or "BUS_001"
    is_sim = data.get("simulated", False)

    # Never let simulated updates overwrite a live hardware ESP32 bus
    if is_sim and (bus_id == "lee_bus_esp32_001" or "esp32" in bus_id.lower() or live_bus_data.get(bus_id, {}).get("is_hardware")):
        return

    is_hardware = (not is_sim) or (bus_id == "lee_bus_esp32_001") or ("esp32" in bus_id.lower())
    if is_hardware:
        is_sim = False

    # Support nested GPS object if present
    gps_info = data.get("gps", {}) if isinstance(data.get("gps"), dict) else {}
    lat = data.get("latitude") if data.get("latitude") is not None else gps_info.get("lat", 0)
    lon = data.get("longitude") if data.get("longitude") is not None else gps_info.get("lng", 0)
    raw_speed = data.get("speed") if data.get("speed") is not None else gps_info.get("speed", 0)
    heading = data.get("heading") if data.get("heading") is not None else gps_info.get("course", 0)
    altitude = data.get("altitude") if data.get("altitude") is not None else gps_info.get("alt", 0)
    satellites = data.get("satellites") if data.get("satellites") is not None else gps_info.get("sats", 0)

    has_gps_fix = bool((lat != 0 or lon != 0) and gps_info.get("valid", True))

    # Calculate speed from consecutive GPS positions if raw speed is 0 or missing
    speed = raw_speed or 0
    now_ts = datetime.utcnow()
    if is_hardware and has_gps_fix and (speed is None or speed < 0.5):
        prev = bus_last_position.get(bus_id)
        if prev and prev.get("lat") and prev.get("lon"):
            elapsed_seconds = (now_ts - prev["ts"]).total_seconds()
            if elapsed_seconds > 0.5:  # At least 0.5s between fixes
                dist_km = _haversine_km(prev["lat"], prev["lon"], lat, lon)
                # GPS drift filter: under 6 meters is considered stationary jitter
                if dist_km < 0.006:
                    speed = 0.0
                else:
                    calculated_speed = (dist_km / elapsed_seconds) * 3600  # km/h
                    # Clamp unreasonable values (GPS jumps can cause spikes)
                    if calculated_speed < 150:
                        speed = round(calculated_speed, 1)
                    else:
                        speed = 0.0

    # Store current position for next speed calculation
    if has_gps_fix:
        bus_last_position[bus_id] = {"lat": lat, "lon": lon, "ts": now_ts}

    if not is_sim:
        if has_gps_fix:
            print(f"[HARDWARE GPS FIX] Bus '{bus_id}' -> Lat: {lat:.6f}, Lon: {lon:.6f}, Speed: {speed} km/h, Sats: {satellites}")
        else:
            print(f"[HARDWARE TELEMETRY] Bus '{bus_id}' connected! Searching for GPS satellite fix (Sats: {satellites})")

    timestamp = data.get("timestamp") or (
        f"{gps_info.get('date', '')}T{gps_info.get('time', '')}Z" if gps_info.get("time") else datetime.utcnow().isoformat()
    )

    # Ensure bus exists in database with correct route & friendly name
    existing_buses = [b["id"] for b in get_buses()]
    route_id = data.get("route_id", "ROUTE_04" if is_hardware else "ROUTE_A")
    bus_name = data.get("bus_name") or ("My Bus (ESP32 Live Tracker)" if is_hardware else f"Hardware Tracker ({bus_id})")
    if bus_id not in existing_buses or (is_hardware and bus_name != "My Bus (ESP32 Live Tracker)"):
        add_bus(bus_id, route_id, bus_name)

    # Update in-memory cache with pure GPS telemetry
    live_bus_data[bus_id] = {
        "bus_id": bus_id,
        "route_id": route_id,
        "bus_name": bus_name,
        "latitude": lat if has_gps_fix else 0,
        "longitude": lon if has_gps_fix else 0,
        "gps_fixed": has_gps_fix,
        "speed": speed,
        "heading": heading,
        "altitude": altitude,
        "satellites": satellites,
        "timestamp": timestamp,
        "simulated": False if is_hardware else is_sim,
        "is_hardware": is_hardware,
        "is_live": True,
        "last_updated": datetime.utcnow().isoformat(),
    }

    # If no valid GPS fix yet, we still push live sensor telemetry to frontend, but skip ETA/DB coordinates
    if not has_gps_fix:
        socketio.emit("bus_update", live_bus_data[bus_id])
        return

    # Store in database
    save_location(bus_id, lat, lon, speed, heading, timestamp)

    # Run ETA prediction
    if route_id:
        try:
            stops = get_stops_for_route(route_id)
            if stops:
                predictions = eta_predictor.predict_eta(lat, lon, speed, stops)
                live_bus_data[bus_id]["eta_predictions"] = predictions

                # Save top predictions to DB
                for pred in predictions[:3]:
                    save_eta_prediction(
                        bus_id, pred["stop_id"],
                        pred["eta_minutes"], pred["cumulative_distance_km"],
                        pred["confidence"]
                    )

                # Stop Geofencing & Continual Online Learning
                nearby_stop = None
                min_dist_to_stop = float("inf")
                for s in stops:
                    d = eta_predictor.calculate_distance(lat, lon, s["latitude"], s["longitude"])
                    if d < 0.20 and d < min_dist_to_stop:
                        min_dist_to_stop = d
                        nearby_stop = s

                if nearby_stop:
                    tracker = bus_trip_tracker.get(bus_id)
                    now_utc = datetime.utcnow()
                    if tracker and tracker.get("stop_id") != nearby_stop["id"]:
                        dep_time = tracker.get("timestamp", now_utc)
                        actual_min = (now_utc - dep_time).total_seconds() / 60.0

                        if 0.15 <= actual_min <= 120.0:
                            seg_dist = tracker.get("distance_to_next", min_dist_to_stop)
                            pred_eta = tracker.get("predicted_eta", actual_min)
                            cong = eta_predictor._calculate_congestion_factor()

                            learn_res = eta_predictor.learn_from_completed_segment(
                                distance_km=seg_dist,
                                effective_speed=speed if speed > 2 else 25.0,
                                hour=now_utc.hour,
                                day=now_utc.weekday(),
                                congestion=cong,
                                road_type_idx=0,
                                dwell_stops=1,
                                actual_time_minutes=actual_min,
                                predicted_time_minutes=pred_eta
                            )

                            save_learning_sample(
                                bus_id=bus_id,
                                route_id=route_id,
                                from_stop=tracker.get("stop_name", "Previous Stop"),
                                to_stop=nearby_stop["name"],
                                segment_distance_km=seg_dist,
                                avg_speed_kmh=speed if speed > 2 else 25.0,
                                hour_of_day=now_utc.hour,
                                day_of_week=now_utc.weekday(),
                                congestion_factor=cong,
                                predicted_eta=pred_eta,
                                actual_travel_time=round(actual_min, 2),
                                error_minutes=learn_res["error_minutes"],
                                samples_total=learn_res["samples_learned"]
                            )

                            socketio.emit("ai_learning_update", {
                                "bus_id": bus_id,
                                "route_id": route_id,
                                "from_stop": tracker.get("stop_name"),
                                "to_stop": nearby_stop["name"],
                                "actual_travel_time": round(actual_min, 2),
                                "predicted_eta": round(pred_eta, 2),
                                "error_minutes": learn_res["error_minutes"],
                                "samples_learned": learn_res["samples_learned"],
                                "rolling_mae": learn_res["rolling_mae"],
                                "timestamp": now_utc.isoformat()
                            })

                    # Update tracker with newly reached stop
                    next_pred = predictions[0]["eta_minutes"] if predictions else 5.0
                    next_dist = predictions[0]["distance_km"] if predictions else 2.0
                    bus_trip_tracker[bus_id] = {
                        "stop_id": nearby_stop["id"],
                        "stop_name": nearby_stop["name"],
                        "timestamp": now_utc,
                        "predicted_eta": next_pred,
                        "distance_to_next": next_dist,
                    }

        except Exception as e:
            print(f"[ETA] Prediction error for {bus_id}: {e}")

    # Push to frontend via WebSocket
    socketio.emit("bus_update", live_bus_data[bus_id])


# ============================================================
# REST API Routes
# ============================================================

@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    is_connected = any(c.is_connected() for c in mqtt_clients) if mqtt_clients else False
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "mqtt_connected": is_connected,
        "mqtt_listener_count": len([c for c in mqtt_clients if c.is_connected()]),
        "simulator_running": bus_simulator.running if bus_simulator else False,
        "active_buses": len(live_bus_data),
        "ai_model": eta_predictor.get_model_info(),
    })


@app.route("/api/buses", methods=["GET"])
def get_all_buses():
    """Get all buses with their current live positions."""
    db_buses = get_buses()
    result = []
    seen_ids = set()
    now_utc = datetime.utcnow()
    OFFLINE_THRESHOLD_SECONDS = 60  # Mark bus offline if no data for 60s

    for bus in db_buses:
        bus_data = dict(bus)
        b_id = bus["id"]
        seen_ids.add(b_id)
        if b_id in live_bus_data:
            bus_data.update(live_bus_data[b_id])
            # Check freshness for offline detection
            last_upd = live_bus_data[b_id].get("last_updated")
            if last_upd:
                try:
                    last_dt = datetime.fromisoformat(last_upd)
                    age_seconds = (now_utc - last_dt).total_seconds()
                    if age_seconds > OFFLINE_THRESHOLD_SECONDS:
                        bus_data["is_live"] = False
                        bus_data["is_offline"] = True
                    else:
                        bus_data["is_live"] = True
                        bus_data["is_offline"] = False
                except (ValueError, TypeError):
                    bus_data["is_live"] = True
                    bus_data["is_offline"] = False
            else:
                bus_data["is_live"] = True
                bus_data["is_offline"] = False
        else:
            bus_data["is_live"] = False
            bus_data["is_offline"] = True
            bus_data["simulated"] = True
            bus_data["is_hardware"] = False

        # Ensure hardware flag is consistent
        if b_id == "lee_bus_esp32_001" or "esp32" in b_id.lower():
            bus_data["is_hardware"] = True
            bus_data["simulated"] = False
        result.append(bus_data)

    for b_id, b_live in live_bus_data.items():
        if b_id not in seen_ids:
            item = dict(b_live)
            item["id"] = b_id
            # Check freshness for offline detection
            last_upd = b_live.get("last_updated")
            if last_upd:
                try:
                    last_dt = datetime.fromisoformat(last_upd)
                    age_seconds = (now_utc - last_dt).total_seconds()
                    if age_seconds > OFFLINE_THRESHOLD_SECONDS:
                        item["is_live"] = False
                        item["is_offline"] = True
                    else:
                        item["is_live"] = True
                        item["is_offline"] = False
                except (ValueError, TypeError):
                    item["is_live"] = True
                    item["is_offline"] = False
            else:
                item["is_live"] = True
                item["is_offline"] = False
            result.append(item)

    # Sort hardware buses to the top of the fleet list
    result.sort(key=lambda b: (0 if (b.get("is_hardware") or not b.get("simulated", True)) else 1, b.get("name", "")))
    return jsonify(result)


@app.route("/api/buses/<bus_id>", methods=["GET"])
def get_bus_detail(bus_id):
    """Get detailed info for a specific bus including ETA predictions."""
    if bus_id in live_bus_data:
        return jsonify(live_bus_data[bus_id])
    return jsonify({"error": "Bus not found or not currently active"}), 404


@app.route("/api/buses/<bus_id>/route", methods=["PUT"])
def change_bus_route(bus_id):
    """Change the assigned route for a bus (e.g. reassign hardware ESP32 bus to a different route)."""
    data = request.json or {}
    new_route_id = data.get("route_id")
    if not new_route_id:
        return jsonify({"error": "'route_id' is required"}), 400

    success, msg = update_bus_route(bus_id, new_route_id)
    if not success:
        return jsonify({"error": msg}), 400

    # Update the in-memory cache too so WebSocket pushes use the new route
    if bus_id in live_bus_data:
        live_bus_data[bus_id]["route_id"] = new_route_id
        # Update route name from routes list
        all_routes = get_routes()
        route_match = next((r for r in all_routes if r["id"] == new_route_id), None)
        if route_match:
            live_bus_data[bus_id]["route_name"] = route_match["name"]

    # Reset trip tracker for this bus since it's on a new route
    if bus_id in bus_trip_tracker:
        del bus_trip_tracker[bus_id]

    return jsonify({"message": f"Bus {bus_id} assigned to route {new_route_id}", "route_id": new_route_id})


@app.route("/api/buses/<bus_id>/history", methods=["GET"])
def get_bus_history(bus_id):
    """Get location history for a bus."""
    limit = request.args.get("limit", 100, type=int)
    history = get_bus_location_history(bus_id, limit)
    return jsonify(history)


@app.route("/api/routes", methods=["GET"])
def get_all_routes():
    """Get all routes with stops."""
    routes = get_routes()
    return jsonify(routes)


@app.route("/api/routes/<route_id>/stops", methods=["GET"])
def get_route_stops(route_id):
    """Get stops for a specific route."""
    stops = get_stops_for_route(route_id)
    return jsonify(stops)


@app.route("/api/eta/<bus_id>", methods=["GET"])
def get_eta(bus_id):
    """Get current ETA predictions for a bus."""
    bus = live_bus_data.get(bus_id)
    if bus and "eta_predictions" in bus:
        return jsonify({
            "bus_id": bus_id,
            "predictions": bus["eta_predictions"],
            "model_info": eta_predictor.get_model_info(),
        })

    # Calculate on the fly if bus has coordinates
    lat = bus.get("latitude") if bus else None
    lon = bus.get("longitude") if bus else None
    route_id = bus.get("route_id", "ROUTE_04") if bus else "ROUTE_04"
    if lat and lon:
        stops = get_stops_for_route(route_id)
        if stops:
            preds = eta_predictor.predict_eta(lat, lon, bus.get("speed", 25.0) or 25.0, stops)
            if bus:
                bus["eta_predictions"] = preds
            return jsonify({
                "bus_id": bus_id,
                "predictions": preds,
                "model_info": eta_predictor.get_model_info(),
            })

    return jsonify({
        "bus_id": bus_id,
        "predictions": [],
        "model_info": eta_predictor.get_model_info(),
    }), 200


@app.route("/api/analytics", methods=["GET"])
def get_system_analytics():
    """Get system-wide analytics."""
    analytics = get_analytics()
    analytics["model_info"] = eta_predictor.get_model_info()
    analytics["learning_metrics"] = get_learning_metrics()
    return jsonify(analytics)


@app.route("/api/ai/metrics", methods=["GET"])
def get_ai_metrics():
    """Get detailed AI model metadata, active learning stats, and error benchmarks."""
    model_info = eta_predictor.get_model_info()
    db_metrics = get_learning_metrics()
    return jsonify({
        **model_info,
        "database_metrics": db_metrics,
    })


@app.route("/api/ai/history", methods=["GET"])
def get_ai_history():
    """Get the recent history of actively learned segment predictions vs actual ground truth."""
    limit = request.args.get("limit", 50, type=int)
    history = get_learning_history(limit=limit)
    return jsonify(history)


# ============================================================
# Route Management API (Google Maps Transit & Route Number Lookup)
# ============================================================

from sri_lanka_routes import lookup_route_by_number, SRI_LANKA_ROUTES


@app.route("/api/routes/lookup", methods=["GET"])
def lookup_routes():
    """
    Search bus routes directly by route number (e.g. '04', '138', '177', '01', '02')
    or city name. Returns full verified stop sequences, corridor, and GPS coordinates.
    """
    q = request.args.get("q", "").strip()
    routes = lookup_route_by_number(q)
    return jsonify({"routes": routes, "query": q, "count": len(routes)})


@app.route("/api/routes/search", methods=["POST"])
def search_google_transit_route():
    """
    Search for a bus route between two points using Google Maps Directions API
    with transit mode. Returns discovered bus lines, stops, and coordinates.
    """
    if not GOOGLE_MAPS_API_KEY:
        return jsonify({"error": "Google Maps API key not configured"}), 500

    data = request.json or {}
    origin = data.get("origin", "")        # e.g. "Colombo Fort" or "6.9344,79.8428"
    destination = data.get("destination", "")  # e.g. "Kandy" or "7.2931,80.6350"

    if not origin or not destination:
        return jsonify({"error": "Both 'origin' and 'destination' are required"}), 400

    try:
        # Query Google Directions API with transit mode
        params = urllib.parse.urlencode({
            "origin": origin,
            "destination": destination,
            "mode": "transit",
            "transit_mode": "bus",
            "alternatives": "true",
            "key": GOOGLE_MAPS_API_KEY,
        })
        url = f"https://maps.googleapis.com/maps/api/directions/json?{params}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode())

        if result.get("status") != "OK":
            # Fallback to driving mode for custom route generation if transit is unavailable
            params_fallback = urllib.parse.urlencode({
                "origin": origin,
                "destination": destination,
                "mode": "driving",
                "key": GOOGLE_MAPS_API_KEY,
            })
            url_fallback = f"https://maps.googleapis.com/maps/api/directions/json?{params_fallback}"
            try:
                with urllib.request.urlopen(urllib.request.Request(url_fallback), timeout=15) as resp_fallback:
                    result = json.loads(resp_fallback.read().decode())
            except Exception as fe:
                print(f"[GOOGLE] Driving fallback error: {fe}")

        if result.get("status") != "OK":
            return jsonify({
                "error": f"Google API returned: {result.get('status')}",
                "details": result.get("error_message", "No route found between these locations."),
            }), 400

        # Parse transit routes from response
        discovered_routes = []
        route_colors = ["#3B82F6", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6", "#06B6D4", "#EC4899"]

        for route_idx, route in enumerate(result.get("routes", [])):
            legs = route.get("legs", [])
            if not legs:
                continue

            leg = legs[0]  # Usually single-leg for transit
            route_summary = route.get("summary", f"Route {route_idx + 1}")

            # Extract transit steps (bus segments)
            transit_stops = []
            bus_lines = []

            for step in leg.get("steps", []):
                transit_details = step.get("transit_details")
                if not transit_details:
                    continue

                line = transit_details.get("line", {})
                line_name = line.get("short_name") or line.get("name") or "Bus"
                agency = line.get("agencies", [{}])[0].get("name", "")
                vehicle = line.get("vehicle", {}).get("type", "BUS")

                dep = transit_details.get("departure_stop", {})
                arr = transit_details.get("arrival_stop", {})
                dep_loc = dep.get("location", {})
                arr_loc = arr.get("location", {})
                num_stops = transit_details.get("num_stops", 0)

                bus_lines.append({
                    "line_name": line_name,
                    "agency": agency,
                    "vehicle_type": vehicle,
                    "num_stops": num_stops,
                    "headsign": transit_details.get("headsign", ""),
                })

                # Add departure stop
                transit_stops.append({
                    "name": dep.get("name", "Unknown Stop"),
                    "latitude": dep_loc.get("lat", 0),
                    "longitude": dep_loc.get("lng", 0),
                    "type": "departure",
                })

                # Fetch intermediate stops via geocoding if line has multiple stops
                # For now, add any intermediate stops from the polyline
                intermediate = step.get("steps", [])  # sub-steps if available

                # Add arrival stop
                transit_stops.append({
                    "name": arr.get("name", "Unknown Stop"),
                    "latitude": arr_loc.get("lat", 0),
                    "longitude": arr_loc.get("lng", 0),
                    "type": "arrival",
                })

            # Remove duplicate consecutive stops
            unique_stops = []
            for s in transit_stops:
                if not unique_stops or s["name"] != unique_stops[-1]["name"]:
                    unique_stops.append(s)

            if unique_stops:
                # Build a descriptive route name from the bus lines found
                line_labels = list(set(bl["line_name"] for bl in bus_lines))
                route_name_parts = []
                if line_labels:
                    route_name_parts.append(" / ".join(line_labels))
                route_name_parts.append(f"{unique_stops[0]['name']} → {unique_stops[-1]['name']}")
                route_name = " — ".join(route_name_parts)

                discovered_routes.append({
                    "route_name": route_name,
                    "summary": route_summary,
                    "bus_lines": bus_lines,
                    "stops": unique_stops,
                    "total_distance": leg.get("distance", {}).get("text", ""),
                    "total_duration": leg.get("duration", {}).get("text", ""),
                    "color": route_colors[route_idx % len(route_colors)],
                    "origin_address": leg.get("start_address", origin),
                    "destination_address": leg.get("end_address", destination),
                })

        if not discovered_routes:
            # Fallback: No transit found, use driving directions to create a custom route
            leg = result["routes"][0]["legs"][0]
            discovered_routes.append({
                "route_name": f"{leg.get('start_address', origin)} → {leg.get('end_address', destination)}",
                "summary": "Custom route (no bus transit found by Google)",
                "bus_lines": [],
                "stops": [
                    {
                        "name": leg.get("start_address", origin),
                        "latitude": leg["start_location"]["lat"],
                        "longitude": leg["start_location"]["lng"],
                        "type": "departure",
                    },
                    {
                        "name": leg.get("end_address", destination),
                        "latitude": leg["end_location"]["lat"],
                        "longitude": leg["end_location"]["lng"],
                        "type": "arrival",
                    },
                ],
                "total_distance": leg.get("distance", {}).get("text", ""),
                "total_duration": leg.get("duration", {}).get("text", ""),
                "color": "#3B82F6",
                "origin_address": leg.get("start_address", origin),
                "destination_address": leg.get("end_address", destination),
            })

        return jsonify({
            "routes": discovered_routes,
            "query": {"origin": origin, "destination": destination},
        })

    except Exception as e:
        print(f"[GOOGLE] Route search error: {e}")
        return jsonify({"error": f"Google Maps API error: {str(e)}"}), 500


@app.route("/api/routes/add", methods=["POST"])
def add_new_route():
    """
    Add a new route to the system. Accepts route data from the Google search
    results or manual entry.
    """
    data = request.json or {}
    route_name = data.get("route_name", "")
    stops = data.get("stops", [])
    color = data.get("color", "#3B82F6")
    bus_count = data.get("bus_count", 1)

    if not route_name:
        return jsonify({"error": "'route_name' is required"}), 400
    if len(stops) < 2:
        return jsonify({"error": "At least 2 stops are required"}), 400

    try:
        # Generate route ID
        count = get_route_count()
        route_id = f"ROUTE_{chr(65 + count)}"  # ROUTE_A, ROUTE_B, ...
        # Handle beyond Z
        if count >= 26:
            route_id = f"ROUTE_{count + 1}"

        # Add route
        add_route(route_id, route_name, color)

        # Add stops
        for idx, stop in enumerate(stops):
            stop_id = f"STOP_{route_id[-1]}_{idx + 1}" if count < 26 else f"STOP_R{count + 1}_{idx + 1}"
            add_stop(
                stop_id=stop_id,
                route_id=route_id,
                name=stop.get("name", f"Stop {idx + 1}"),
                latitude=stop.get("latitude", 0),
                longitude=stop.get("longitude", 0),
                stop_order=idx + 1,
            )

        # Add buses for this route
        created_buses = []
        for i in range(bus_count):
            # Find next available bus ID
            existing_buses = get_buses()
            existing_ids = [b["id"] for b in existing_buses]
            bus_num = 1
            while f"BUS_{bus_num:03d}" in existing_ids:
                bus_num += 1
            bus_id = f"BUS_{bus_num:03d}"
            bus_name = f"{route_name} #{i + 1}"
            add_bus(bus_id, route_id, bus_name)
            created_buses.append({"id": bus_id, "name": bus_name})

        # Dynamically reload simulator with new route & fleet
        global bus_simulator
        if bus_simulator and bus_simulator.running:
            bus_simulator.reload_routes(get_routes())

        return jsonify({
            "message": "Route added successfully",
            "route_id": route_id,
            "route": {
                "id": route_id,
                "name": route_name,
                "color": color,
                "stops_count": len(stops),
                "buses": created_buses,
            }
        })

    except Exception as e:
        print(f"[ROUTE] Error adding route: {e}")
        return jsonify({"error": f"Failed to add route: {str(e)}"}), 500


@app.route("/api/routes/<route_id>", methods=["DELETE"])
def remove_route(route_id):
    """Delete a route and all associated data."""
    success = delete_route(route_id)
    if success:
        # Clean up live bus data for buses on this route
        to_remove = [bid for bid, bdata in live_bus_data.items() if bdata.get("route_id") == route_id]
        for bid in to_remove:
            del live_bus_data[bid]
            if bid in bus_trip_tracker:
                del bus_trip_tracker[bid]
        
        # Dynamically reload simulator
        global bus_simulator
        if bus_simulator and bus_simulator.running:
            bus_simulator.reload_routes(get_routes())

        return jsonify({"message": f"Route {route_id} deleted successfully"})
    return jsonify({"error": "Failed to delete route"}), 500


@app.route("/api/routes/<route_id>/add-stops", methods=["POST"])
def add_intermediate_stops(route_id):
    """
    Use Google Maps Geocoding to add intermediate waypoint stops to an existing route.
    Accepts a list of place names, geocodes them, and inserts them between existing stops.
    """
    if not GOOGLE_MAPS_API_KEY:
        return jsonify({"error": "Google Maps API key not configured"}), 500

    data = request.json or {}
    stop_names = data.get("stops", [])  # List of place name strings

    if not stop_names:
        return jsonify({"error": "'stops' list is required"}), 400

    # Get current stops to calculate next order
    existing_stops = get_stops_for_route(route_id)
    next_order = max((s["stop_order"] for s in existing_stops), default=0)

    added_stops = []
    for name in stop_names:
        try:
            params = urllib.parse.urlencode({
                "address": f"{name}, Sri Lanka",
                "key": GOOGLE_MAPS_API_KEY,
            })
            url = f"https://maps.googleapis.com/maps/api/geocode/json?{params}"
            with urllib.request.urlopen(url, timeout=10) as resp:
                result = json.loads(resp.read().decode())

            if result.get("status") == "OK" and result.get("results"):
                loc = result["results"][0]["geometry"]["location"]
                formatted_name = result["results"][0].get("formatted_address", name).split(",")[0]

                next_order += 1
                stop_id = f"STOP_{route_id}_{next_order}"
                add_stop(stop_id, route_id, formatted_name, loc["lat"], loc["lng"], next_order)
                added_stops.append({
                    "id": stop_id,
                    "name": formatted_name,
                    "latitude": loc["lat"],
                    "longitude": loc["lng"],
                    "stop_order": next_order,
                })
        except Exception as e:
            print(f"[GEOCODE] Failed to geocode '{name}': {e}")

    # Dynamically reload simulator with updated stops
    global bus_simulator
    if bus_simulator and bus_simulator.running:
        bus_simulator.reload_routes(get_routes())

    return jsonify({
        "message": f"Added {len(added_stops)} stops to route {route_id}",
        "stops": added_stops,
    })


@app.route("/api/geocode", methods=["GET"])
def geocode_place():
    """Geocode a place name using Google Maps. Useful for manual stop entry."""
    if not GOOGLE_MAPS_API_KEY:
        return jsonify({"error": "Google Maps API key not configured"}), 500

    place = request.args.get("q", "")
    if not place:
        return jsonify({"error": "'q' parameter is required"}), 400

    try:
        params = urllib.parse.urlencode({
            "address": f"{place}, Sri Lanka",
            "key": GOOGLE_MAPS_API_KEY,
        })
        url = f"https://maps.googleapis.com/maps/api/geocode/json?{params}"
        with urllib.request.urlopen(url, timeout=10) as resp:
            result = json.loads(resp.read().decode())

        if result.get("status") == "OK" and result.get("results"):
            places = []
            for r in result["results"][:5]:
                loc = r["geometry"]["location"]
                places.append({
                    "name": r.get("formatted_address", place),
                    "latitude": loc["lat"],
                    "longitude": loc["lng"],
                })
            return jsonify({"results": places})
        return jsonify({"results": [], "message": "No results found"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/simulator/status", methods=["GET"])
def get_simulator_status():
    """Get simulator status."""
    if bus_simulator:
        return jsonify(bus_simulator.get_status())
    return jsonify({"running": False, "message": "Simulator not initialized"})


@app.route("/api/simulator/start", methods=["POST"])
def start_simulator():
    """Start the bus simulator."""
    global bus_simulator
    if bus_simulator and bus_simulator.running:
        return jsonify({"message": "Simulator already running"})

    routes = get_routes()
    bus_simulator = BusSimulator(routes, lambda bus_id, data: process_bus_location(data))
    bus_simulator.start()
    return jsonify({"message": "Simulator started", "status": bus_simulator.get_status()})


@app.route("/api/simulator/stop", methods=["POST"])
def stop_simulator():
    """Stop the bus simulator."""
    global bus_simulator
    if bus_simulator:
        bus_simulator.stop()
        return jsonify({"message": "Simulator stopped"})
    return jsonify({"message": "No simulator running"})


# ============================================================
# WebSocket Events
# ============================================================

@socketio.on("connect")
def handle_ws_connect():
    """Handle new WebSocket connection."""
    print(f"[WS] Client connected")
    # Send all current bus data to new client
    for bus_id, data in live_bus_data.items():
        socketio.emit("bus_update", data)


@socketio.on("disconnect")
def handle_ws_disconnect():
    """Handle WebSocket disconnection."""
    print(f"[WS] Client disconnected")


@socketio.on("request_all_buses")
def handle_request_all():
    """Client requesting all bus data."""
    for bus_id, data in live_bus_data.items():
        socketio.emit("bus_update", data)


# ============================================================
# Application Startup
# ============================================================

def start_app():
    """Initialize and start the application."""
    print("\n" + "=" * 60)
    print("  AI-Powered IoT Bus Tracking System")
    print("  Backend Server v1.0.0")
    print("=" * 60 + "\n")

    # Initialize database
    init_db()

    # Setup MQTT connection to HiveMQ Cloud
    setup_mqtt()

    # Initialize bus simulator for background fleet telemetry
    global bus_simulator
    routes = get_routes()
    bus_simulator = BusSimulator(routes, lambda bus_id, data: process_bus_location(data))
    bus_simulator.start()

    print(f"\n[SERVER] Starting Flask server on http://localhost:{os.environ.get('FLASK_PORT', 5000)}")
    print("[SERVER] API docs: http://localhost:5000/api/health")
    print("[SERVER] Frontend: http://localhost:3000\n")


if __name__ == "__main__":
    start_app()
    socketio.run(
        app,
        host=os.environ.get("FLASK_HOST", "0.0.0.0"),
        port=int(os.environ.get("FLASK_PORT", 5000)),
        debug=os.environ.get("FLASK_DEBUG", "True").lower() == "true",
        use_reloader=False,
    )
