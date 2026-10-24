# 🚌 BusTrack AI — AI-Powered IoT Real-Time Bus Tracking System

> A full-stack real-time bus tracking system with AI-powered ETA prediction, IoT integration via ESP32 + GPS hardware, HiveMQ Cloud MQTT, and a React dashboard with live Leaflet maps.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-green.svg)
![Node](https://img.shields.io/badge/node-18+-brightgreen.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20|%20Linux%20|%20macOS-lightgrey.svg)

---

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
  - [1. Clone the Repository](#1-clone-the-repository)
  - [2. Backend Setup (Python)](#2-backend-setup-python)
  - [3. Frontend Setup (Node.js)](#3-frontend-setup-nodejs)
  - [4. ESP32 Hardware Setup (Optional)](#4-esp32-hardware-setup-optional)
- [Running the Application](#-running-the-application)
- [Project Structure](#-project-structure)
- [API Endpoints](#-api-endpoints)
- [Environment Variables](#-environment-variables)
- [ESP32 Wiring Diagram](#-esp32-wiring-diagram)
- [Screenshots](#-screenshots)
- [Troubleshooting](#-troubleshooting)

---

## ✨ Features

- **🛰️ Real-Time GPS Tracking** — Live bus positions from ESP32 + NEO-6M GPS via HiveMQ Cloud MQTT
- **🧠 AI-Powered ETA Prediction** — Machine learning model (SGD Regressor) trained with incremental online learning
- **🗺️ Interactive Map Dashboard** — Dark-themed Leaflet map with animated bus markers, route polylines, and popups
- **📡 IoT Integration** — ESP32 firmware with WiFi/MQTT + GPS data pipeline
- **🚏 Google Maps Route Studio** — Discover and create bus routes using Google Maps Directions API
- **📊 Live Analytics** — Real-time stats: active buses, AI model accuracy (MAE), MQTT status, learning events
- **🔄 Bus Simulator** — Demo mode to simulate multiple buses on routes without hardware
- **⚡ WebSocket Updates** — Socket.IO for instant push of bus position updates to dashboard
- **🌙 Premium Dark UI** — Glassmorphism design with gradients, animations, and responsive layout

---

## 🏗️ Architecture

```
┌──────────────┐     MQTT (TLS)    ┌──────────────────┐     REST/WS      ┌──────────────┐
│  ESP32 +     │ ──────────────►   │  Python Flask    │ ◄──────────────► │  React +     │
│  NEO-6M GPS  │                   │  Backend Server  │                   │  Leaflet     │
│  (Hardware)  │                   │                  │                   │  Dashboard   │
└──────────────┘                   │  • MQTT Client   │                   └──────────────┘
                                   │  • ML Predictor  │
┌──────────────┐                   │  • REST API      │
│  HiveMQ      │ ◄──────────────►  │  • WebSocket     │
│  Cloud MQTT  │     MQTT (TLS)    │  • SQLite DB     │
│  Broker      │                   │  • Simulator     │
└──────────────┘                   └──────────────────┘
```

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| **Backend** | Python 3.10+, Flask, Flask-SocketIO, Eventlet |
| **Frontend** | React 19, Vite, Leaflet.js, Socket.IO Client |
| **Database** | SQLite |
| **ML Model** | scikit-learn (SGDRegressor with online learning) |
| **IoT Protocol** | MQTT over TLS (HiveMQ Cloud) |
| **Hardware** | ESP32 Dev Module + NEO-6M GPS |
| **Maps API** | Google Maps Directions API, Leaflet.js |
| **Styling** | Custom CSS with glassmorphism dark theme |

---

## 📦 Prerequisites

Before installing, make sure you have the following installed on your system:

| Requirement | Version | Download Link |
|-------------|---------|---------------|
| **Python** | 3.10 or higher | [python.org](https://www.python.org/downloads/) |
| **Node.js** | 18 or higher | [nodejs.org](https://nodejs.org/) |
| **Git** | Latest | [git-scm.com](https://git-scm.com/downloads) |
| **pip** | Latest | Comes with Python |

### Optional (for hardware)
- Arduino IDE 2.x with ESP32 board package
- ESP32 Dev Module
- NEO-6M GPS Module
- HiveMQ Cloud account (free tier available)

---

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/sahan-bus-tracking.git
cd sahan-bus-tracking
```

### 2. Backend Setup (Python)

```bash
# Navigate to backend directory
cd backend

# Create a virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Create your environment file
cp .env.example .env
# Then edit .env with your actual credentials (see Environment Variables section)
```

### 3. Frontend Setup (Node.js)

```bash
# Navigate to frontend directory (from project root)
cd frontend

# Install Node.js dependencies
npm install
```

### 4. ESP32 Hardware Setup (Optional)

> **Note:** The system works without hardware — use the built-in **Bus Simulator** for demo.

If you have ESP32 + NEO-6M GPS hardware:

1. Open Arduino IDE
2. Install the ESP32 board package:
   - Go to **File → Preferences → Additional Board Manager URLs**
   - Add: `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`
   - Go to **Tools → Board Manager** → Search "ESP32" → Install
3. Install required libraries via **Sketch → Include Library → Manage Libraries**:
   - `TinyGPSPlus` by Mikal Hart
   - `PubSubClient` by Nick O'Leary
4. Open `esp32_firmware/bus_tracker.ino`
5. Update WiFi and MQTT credentials in the sketch
6. Select board: **ESP32 Dev Module**
7. Upload to your ESP32

For SIM7670C (4G LTE) variant, use `esp32_firmware/bus_tracker_sim7670c/bus_tracker_sim7670c.ino`.

---

## ▶️ Running the Application

You need **two terminals** — one for the backend and one for the frontend.

### Terminal 1: Start the Backend Server

```bash
cd backend

# Activate virtual environment (if not already active)
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Run the Flask server
python app.py
```

The backend will start on `http://localhost:5000`. You should see:
```
[SERVER] Flask-SocketIO server starting on 0.0.0.0:5000
[MQTT] Connecting to HiveMQ Cloud...
[ML] ETA Predictor initialized
```

### Terminal 2: Start the Frontend Dev Server

```bash
cd frontend

# Start the Vite development server
npm run dev
```

The frontend will start on `http://localhost:5173`.

### Open the Dashboard

Open your browser and navigate to:
```
http://localhost:5173
```

### Using the Bus Simulator (No Hardware Needed)

1. On the dashboard, look for the **"▶ Start"** button in the left sidebar under "Bus Simulator"
2. Click it to simulate buses moving on predefined Sri Lanka routes
3. The map will show animated bus markers moving along routes

---

## 📁 Project Structure

```
sahan-bus-tracking/
├── backend/                    # Python Flask backend
│   ├── app.py                  # Main server (MQTT, REST API, WebSocket)
│   ├── database.py             # SQLite database operations
│   ├── ml_model.py             # AI/ML ETA prediction model
│   ├── simulator.py            # Bus movement simulator
│   ├── sri_lanka_routes.py     # Pre-configured Sri Lanka bus routes
│   ├── requirements.txt        # Python dependencies
│   ├── .env.example            # Environment variables template
│   └── data/                   # SQLite database directory
│
├── frontend/                   # React + Vite frontend
│   ├── src/
│   │   ├── App.jsx             # Main application component
│   │   ├── RouteStudio.jsx     # Google Maps Route Studio modal
│   │   ├── api.js              # API client helper
│   │   ├── index.css           # Full design system (dark theme)
│   │   └── main.jsx            # React entry point
│   ├── index.html              # HTML entry point
│   ├── package.json            # Node.js dependencies
│   └── vite.config.js          # Vite configuration
│
├── esp32_firmware/             # Arduino/ESP32 firmware
│   ├── bus_tracker.ino         # WiFi + GPS + MQTT firmware
│   └── bus_tracker_sim7670c/   # 4G LTE variant
│       └── bus_tracker_sim7670c.ino
│
├── .gitignore                  # Git ignore rules
└── README.md                   # This file
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/buses` | Get all bus positions and status |
| `GET` | `/api/routes` | Get all configured routes with stops |
| `GET` | `/api/eta/<bus_id>` | Get AI-predicted ETA for a specific bus |
| `GET` | `/api/health` | Server health check (MQTT status, uptime) |
| `GET` | `/api/analytics` | Fleet analytics and statistics |
| `GET` | `/api/ai/metrics` | AI model performance metrics |
| `GET` | `/api/learning/history` | Active learning event history |
| `POST` | `/api/routes` | Create a new route |
| `POST` | `/api/routes/<id>/stops` | Add a stop to a route |
| `POST` | `/api/buses` | Register a new bus |
| `DELETE` | `/api/routes/<id>` | Delete a route |
| `PUT` | `/api/buses/<id>/route` | Change a bus's assigned route |
| `POST` | `/api/simulator/start` | Start the bus simulator |
| `POST` | `/api/simulator/stop` | Stop the bus simulator |
| `GET` | `/api/google/directions` | Proxy to Google Maps Directions API |
| `GET` | `/api/google/places/search` | Proxy to Google Maps Places API |

### WebSocket Events

| Event | Direction | Description |
|-------|-----------|-------------|
| `bus_update` | Server → Client | Real-time bus position update |
| `learning_event` | Server → Client | Active learning model update event |

---

## 🔐 Environment Variables

Create a `.env` file in the `backend/` directory (copy from `.env.example`):

| Variable | Description | Required |
|----------|-------------|----------|
| `MQTT_BROKER` | HiveMQ Cloud broker hostname | Yes (for hardware) |
| `MQTT_PORT` | MQTT TLS port (default: 8883) | Yes (for hardware) |
| `MQTT_USERNAME` | HiveMQ Cloud username | Yes (for hardware) |
| `MQTT_PASSWORD` | HiveMQ Cloud password | Yes (for hardware) |
| `FLASK_HOST` | Server bind host (default: 0.0.0.0) | No |
| `FLASK_PORT` | Server port (default: 5000) | No |
| `FLASK_DEBUG` | Debug mode (default: True) | No |
| `SECRET_KEY` | Flask secret key | Recommended |
| `DATABASE_PATH` | SQLite database path | No |
| `GOOGLE_MAPS_API_KEY` | Google Maps API key for Route Studio | Yes (for Route Studio) |

> **Note:** The system works without MQTT credentials — the simulator generates data locally. MQTT is only needed for real ESP32 hardware.

---

## 🔧 ESP32 Wiring Diagram

```
ESP32 Dev Module          NEO-6M GPS Module
┌──────────────┐         ┌──────────────┐
│          GPIO16 (RX2) ←── TX          │
│          GPIO17 (TX2) ──→ RX          │
│          3.3V ────────── VCC          │
│          GND ─────────── GND          │
└──────────────┘         └──────────────┘
```

### MQTT Topic Structure
```
bus/gps                    # GPS data from ESP32
bus/gps/<bus_id>           # Per-bus GPS data
```

### GPS Data JSON Format (sent by ESP32)
```json
{
  "bus_id": "lee_bus_esp32_001",
  "lat": 6.9271,
  "lng": 79.8612,
  "speed": 35.5,
  "heading": 180.0,
  "satellites": 12,
  "hdop": 0.8,
  "altitude": 15.2,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## 🖼️ Screenshots

The dashboard features:
- Dark-themed glassmorphism UI
- Live Leaflet map with animated bus markers
- Sidebar with fleet overview and bus cards
- ETA prediction panel with confidence indicators
- Google Maps Route Studio for route management
- Real-time stats bar showing AI metrics and MQTT status

---

## 🔧 Troubleshooting

### Backend won't start
- Make sure Python 3.10+ is installed: `python --version`
- Make sure the virtual environment is activated
- Check that all packages installed: `pip install -r requirements.txt`
- Verify `.env` file exists in `backend/` directory

### Frontend won't start
- Make sure Node.js 18+ is installed: `node --version`
- Run `npm install` in the `frontend/` directory
- Check for port conflicts on 5173

### MQTT Connection Fails
- This is expected if you don't have HiveMQ credentials
- The system will still work with the **Bus Simulator** (no MQTT needed)
- To use hardware, create a free account at [hivemq.cloud](https://www.hivemq.cloud/)

### Map Not Loading
- The app uses Leaflet with OpenStreetMap tiles (no API key needed for the map)
- Google Maps API key is only needed for the **Route Studio** feature
- Check your internet connection for tile loading

### "Module not found" Errors
```bash
# Backend
pip install -r requirements.txt

# Frontend
cd frontend && npm install
```

### Port Already in Use
```bash
# Change backend port in .env:
FLASK_PORT=5001

# Change frontend port:
npx vite --port 3000
```

---

## 📄 License

This project is licensed under the MIT License.

---

## 👤 Author

**W. Thasindu Hansana**

Built with ❤️ for the IoT Bus Tracking Project
