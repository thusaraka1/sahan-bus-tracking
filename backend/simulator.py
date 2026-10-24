"""
Bus Simulator - Generates realistic bus movement data for testing.
Simulates buses moving along their routes when real ESP32 hardware is unavailable.
Publishes data to the same MQTT topics as real ESP32 devices.
"""

import json
import math
import time
import random
import threading
from datetime import datetime


class BusSimulator:
    """
    Simulates multiple buses moving along predefined routes.
    Generates GPS-like data points and publishes them via a callback function.
    """

    def __init__(self, routes_data, publish_callback):
        """
        Args:
            routes_data: List of route dicts with stops
            publish_callback: Function to call with simulated bus data
        """
        self.routes_data = routes_data
        self.publish_callback = publish_callback
        self.running = False
        self.buses = {}
        self._thread = None

        # Initialize simulated buses
        self._init_buses()
        print(f"[SIMULATOR] Initialized with {len(self.buses)} buses")

    def _init_buses(self):
        """Initialize simulated bus positions on their routes dynamically from database."""
        try:
            from database import get_buses
            all_buses = get_buses()
        except Exception:
            all_buses = []

        if not all_buses:
            all_buses = [
                {"id": "BUS_001", "route_id": "ROUTE_A", "name": "Colombo-Kandy Express #1"},
                {"id": "BUS_002", "route_id": "ROUTE_A", "name": "Colombo-Kandy Express #2"},
                {"id": "BUS_003", "route_id": "ROUTE_B", "name": "Galle Coastal #1"},
                {"id": "BUS_004", "route_id": "ROUTE_B", "name": "Galle Coastal #2"},
                {"id": "BUS_005", "route_id": "ROUTE_C", "name": "Negombo Shuttle #1"},
            ]

        new_buses = {}
        for idx, b in enumerate(all_buses):
            bus_id = b["id"]
            bus_name = b.get("name", "")
            # NEVER simulate hardware devices or the user's live ESP32
            if "esp32" in bus_id.lower() or "hardware" in bus_name.lower() or "my bus" in bus_name.lower() or bus_id == "lee_bus_esp32_001":
                continue

            route = next((r for r in self.routes_data if r["id"] == b["route_id"]), None)
            if route and route.get("stops") and len(route["stops"]) >= 2:
                prev_progress = self.buses.get(b["id"], {}).get("progress")
                progress = prev_progress if prev_progress is not None else ((idx * 0.35) % 0.85)
                new_buses[b["id"]] = {
                    "id": b["id"],
                    "route_id": b["route_id"],
                    "name": bus_name or b["id"],
                    "route": route,
                    "progress": progress,
                    "speed": random.uniform(28, 48),
                    "direction": 1,
                    "stopped": False,
                    "stop_timer": 0,
                }
        self.buses = new_buses

    def reload_routes(self, new_routes_data):
        """Update routes and refresh simulated buses dynamically."""
        self.routes_data = new_routes_data
        self._init_buses()
        print(f"[SIMULATOR] Reloaded with {len(self.buses)} buses across {len(self.routes_data)} routes")

    def _interpolate_position(self, stops, progress):
        """
        Calculate GPS position along the route based on progress (0-1).
        Interpolates between stops.
        """
        if not stops or len(stops) < 2:
            return 0, 0, 0

        # Calculate which segment we're on
        total_segments = len(stops) - 1
        segment_progress = progress * total_segments
        segment_index = min(int(segment_progress), total_segments - 1)
        local_progress = segment_progress - segment_index

        # Interpolate between two stops
        stop_a = stops[segment_index]
        stop_b = stops[min(segment_index + 1, len(stops) - 1)]

        lat = stop_a["latitude"] + (stop_b["latitude"] - stop_a["latitude"]) * local_progress
        lon = stop_a["longitude"] + (stop_b["longitude"] - stop_a["longitude"]) * local_progress

        # Calculate heading
        heading = math.degrees(math.atan2(
            stop_b["longitude"] - stop_a["longitude"],
            stop_b["latitude"] - stop_a["latitude"]
        ))
        if heading < 0:
            heading += 360

        # Add small GPS noise (realistic ±5m)
        lat += random.uniform(-0.00005, 0.00005)
        lon += random.uniform(-0.00005, 0.00005)

        return lat, lon, heading

    def _update_bus(self, bus):
        """Update a single bus's position."""
        # Simulate stop behavior
        if bus["stopped"]:
            bus["stop_timer"] -= 1
            if bus["stop_timer"] <= 0:
                bus["stopped"] = False
                bus["speed"] = random.uniform(20, 40)
            return

        # Random chance to stop at a bus stop
        stops = bus["route"]["stops"]
        total_segments = len(stops) - 1
        segment_progress = bus["progress"] * total_segments
        local_progress = segment_progress - int(segment_progress)

        # Stop near bus stops (within 2% of segment)
        if local_progress < 0.02 and random.random() < 0.3:
            bus["stopped"] = True
            bus["stop_timer"] = random.randint(3, 8)  # 15-40 seconds at stop
            bus["speed"] = 0
            return

        # Update speed with variation (simulate traffic)
        hour = datetime.now().hour
        if 7 <= hour <= 9 or 16 <= hour <= 19:
            # Peak hours - slower
            target_speed = random.uniform(10, 30)
        else:
            target_speed = random.uniform(25, 50)

        # Smooth speed transition
        bus["speed"] = bus["speed"] * 0.8 + target_speed * 0.2

        # Calculate distance traveled in this tick (5 second interval)
        distance_km = (bus["speed"] / 3600) * 5  # 5 seconds

        # Estimate total route length (rough)
        route_length_km = self._estimate_route_length(stops)
        if route_length_km > 0:
            progress_delta = distance_km / route_length_km
        else:
            progress_delta = 0.001

        # Update progress
        bus["progress"] += progress_delta * bus["direction"]

        # Reverse at end of route
        if bus["progress"] >= 1.0:
            bus["progress"] = 1.0
            bus["direction"] = -1
        elif bus["progress"] <= 0.0:
            bus["progress"] = 0.0
            bus["direction"] = 1

    def _estimate_route_length(self, stops):
        """Estimate total route length in km from stops."""
        total = 0
        for i in range(len(stops) - 1):
            dlat = stops[i + 1]["latitude"] - stops[i]["latitude"]
            dlon = stops[i + 1]["longitude"] - stops[i]["longitude"]
            # Rough km conversion
            total += math.sqrt((dlat * 111) ** 2 + (dlon * 111 * math.cos(math.radians(stops[i]["latitude"]))) ** 2)
        return total

    def _generate_payload(self, bus):
        """Generate a GPS data payload matching ESP32 format."""
        stops = bus["route"]["stops"]
        lat, lon, heading = self._interpolate_position(stops, bus["progress"])

        return {
            "bus_id": bus["id"],
            "route_id": bus["route_id"],
            "bus_name": bus["name"],
            "latitude": round(lat, 6),
            "longitude": round(lon, 6),
            "speed": round(bus["speed"], 1),
            "heading": round(heading, 1),
            "altitude": round(random.uniform(5, 50), 1),
            "satellites": random.randint(6, 12),
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "simulated": True,
        }

    def _simulation_loop(self):
        """Main simulation loop running in a background thread."""
        print("[SIMULATOR] Simulation started")
        while self.running:
            for bus_id, bus in self.buses.items():
                self._update_bus(bus)
                payload = self._generate_payload(bus)

                # Publish via callback (same as real MQTT data)
                try:
                    self.publish_callback(bus_id, payload)
                except Exception as e:
                    print(f"[SIMULATOR] Error publishing for {bus_id}: {e}")

            time.sleep(5)  # Update every 5 seconds

    def start(self):
        """Start the bus simulation in a background thread."""
        if self.running:
            print("[SIMULATOR] Already running")
            return
        self.running = True
        self._thread = threading.Thread(target=self._simulation_loop, daemon=True)
        self._thread.start()
        print("[SIMULATOR] Started background simulation")

    def stop(self):
        """Stop the simulation."""
        self.running = False
        if self._thread:
            self._thread.join(timeout=10)
        print("[SIMULATOR] Stopped")

    def get_status(self):
        """Get current simulation status."""
        return {
            "running": self.running,
            "bus_count": len(self.buses),
            "buses": {
                bid: {
                    "progress": round(b["progress"] * 100, 1),
                    "speed": round(b["speed"], 1),
                    "stopped": b["stopped"],
                    "direction": "forward" if b["direction"] == 1 else "reverse",
                }
                for bid, b in self.buses.items()
            }
        }
