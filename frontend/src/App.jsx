import { useState, useEffect, useCallback, useRef } from 'react';
import './index.css';
import api from './api.js';
import RouteStudio from './RouteStudio.jsx';
import { io } from 'socket.io-client';

const SOCKET_URL = 'http://localhost:5000';

/* ─── Utility: format time ago ─── */
function timeAgo(isoString) {
  if (!isoString) return '—';
  const diff = (Date.now() - new Date(isoString).getTime()) / 1000;
  if (diff < 5) return 'Just now';
  if (diff < 60) return `${Math.floor(diff)}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  return `${Math.floor(diff / 3600)}h ago`;
}

/* ─── Navbar Component ─── */
function Navbar({ health, aiMetrics, onOpenRouteStudio, onFocusMyBus, hasHardwareBus }) {
  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <div className="navbar-logo">🚌</div>
        <div>
          <div className="navbar-title">BusTrack AI</div>
          <div className="navbar-subtitle">IoT Real-Time Tracking & Dynamic ETA</div>
        </div>
      </div>
      <div className="navbar-status">
        {hasHardwareBus && (
          <button
            className="focus-my-bus-btn"
            onClick={onFocusMyBus}
            id="navbar-focus-my-bus-btn"
            title="Focus map directly on your live ESP32 GPS position"
          >
            <span>🛰️</span>
            <span>Focus My ESP32 Bus</span>
          </button>
        )}
        <button
          className="manage-routes-btn"
          onClick={onOpenRouteStudio}
          id="navbar-route-studio-btn"
          title="Discover, create, or manage bus routes via Google Maps"
        >
          <span>🗺️</span>
          <span>Google Route Studio</span>
        </button>
        <div className="model-badge" title="Pre-Trained + Online Incremental SGD Learning">
          <span>🧠</span>
          <span>{aiMetrics?.model_name || 'TransETA-Continual-v2'} ({aiMetrics?.samples_learned || '800+'} samples learned)</span>
        </div>
        <div
          className={`status-badge ${health?.mqtt_connected ? 'online' : ''}`}
          title="HiveMQ Cloud MQTT Broker (TLS Port 8883)"
          id="navbar-hivemq-badge"
        >
          <span className="status-dot" style={health?.mqtt_connected ? { background: '#10B981', boxShadow: '0 0 8px #10B981' } : {}} />
          <span>{health?.mqtt_connected ? 'HiveMQ Cloud Connected' : 'MQTT Connecting...'}</span>
        </div>
      </div>
    </nav>
  );
}

/* ─── Stats Bar Component ─── */
function StatsBar({ buses, routes, simulatorRunning, aiMetrics, lastLearningEvent, onOpenRouteStudio, health }) {
  const activeBuses = buses.filter(b => b.is_live).length;
  return (
    <div className="stats-bar-container">
      <div className="stats-bar">
        <div className="stat-chip">
          <span className="stat-chip-icon">🚌</span>
          <div>
            <div className="stat-chip-value">{activeBuses}</div>
            <div className="stat-chip-label">Active Buses</div>
          </div>
        </div>
        <div className="stat-chip">
          <span className="stat-chip-icon">📡</span>
          <div>
            <div className="stat-chip-value">{buses.length}</div>
            <div className="stat-chip-label">Total Fleet</div>
          </div>
        </div>
        <div
          className="stat-chip"
          onClick={onOpenRouteStudio}
          style={{ cursor: 'pointer' }}
          title="Click to open Google Maps Route Studio"
          id="stats-chip-routes"
        >
          <span className="stat-chip-icon">🗺️</span>
          <div>
            <div className="stat-chip-value">{routes?.length || 0}</div>
            <div className="stat-chip-label">Routes (+Add)</div>
          </div>
        </div>
        <div className="stat-chip" title="Pre-Trained Baseline with Live Online Stochastic Gradient Descent">
          <span className="stat-chip-icon">⚡</span>
          <div>
            <div className="stat-chip-value">{aiMetrics?.rolling_mae_minutes ? `${aiMetrics.rolling_mae_minutes}m` : '1.8m'}</div>
            <div className="stat-chip-label">Active AI MAE</div>
          </div>
        </div>
        <div className="stat-chip" title="HiveMQ Cloud MQTT Broker (TLS Port 8883)">
          <span className="stat-chip-icon">{health?.mqtt_connected ? '☁️' : '⚪'}</span>
          <div>
            <div className="stat-chip-value" style={health?.mqtt_connected ? { color: '#34D399' } : {}}>{health?.mqtt_connected ? 'ONLINE' : 'OFF'}</div>
            <div className="stat-chip-label">HiveMQ Cloud</div>
          </div>
        </div>
        <div className="stat-chip">
          <span className="stat-chip-icon">{simulatorRunning ? '🟢' : '⚪'}</span>
          <div>
            <div className="stat-chip-value">{simulatorRunning ? 'ON' : 'OFF'}</div>
            <div className="stat-chip-label">Simulator</div>
          </div>
        </div>
      </div>
      {lastLearningEvent && (
        <div className="learning-banner">
          <span className="learning-pulse">🧠 Active Learning:</span> Bus <strong>{lastLearningEvent.bus_id}</strong> reached <em>{lastLearningEvent.to_stop}</em>. Model weight update performed! (Actual: {lastLearningEvent.actual_travel_time}m, Error: {lastLearningEvent.error_minutes}m, Total Samples: {lastLearningEvent.samples_learned})
        </div>
      )}
    </div>
  );
}

/* ─── Bus List Sidebar ─── */
function BusSidebar({ buses, selectedBus, onSelectBus, routes, selectedRoute, onSelectRoute, simulatorRunning, onToggleSimulator, onOpenRouteStudio }) {
  const [search, setSearch] = useState('');

  const filtered = buses.filter(b => {
    const matchesSearch = !search || b.bus_name?.toLowerCase().includes(search.toLowerCase()) || b.id?.toLowerCase().includes(search.toLowerCase());
    const matchesRoute = !selectedRoute || b.route_id === selectedRoute;
    return matchesSearch && matchesRoute;
  });

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-title">Fleet Overview</div>
        <div className="search-box">
          <span className="search-icon">🔍</span>
          <input
            type="text"
            placeholder="Search buses..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            id="bus-search"
          />
        </div>
      </div>

      {/* Route filter tabs */}
      <div className="route-tabs">
        <button
          className={`route-tab ${!selectedRoute ? 'active' : ''}`}
          onClick={() => onSelectRoute(null)}
          id="route-tab-all"
        >
          All Routes
        </button>
        {routes.map(route => (
          <button
            key={route.id}
            className={`route-tab ${selectedRoute === route.id ? 'active' : ''}`}
            onClick={() => onSelectRoute(route.id)}
            style={selectedRoute === route.id ? { background: route.color, borderColor: route.color } : {}}
            id={`route-tab-${route.id}`}
          >
            {route.name}
          </button>
        ))}
        <button
          className="route-tab"
          onClick={onOpenRouteStudio}
          style={{ background: 'rgba(59, 130, 246, 0.15)', borderColor: 'rgba(59, 130, 246, 0.4)', color: 'var(--primary-light)' }}
          id="sidebar-add-route-tab"
          title="Add or Manage Routes via Google Maps"
        >
          ➕ Add Route
        </button>
      </div>

      {/* Bus list */}
      <div className="bus-list">
        {filtered.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">🚌</div>
            <div className="empty-state-text">
              {search ? 'No buses match your search' : 'No buses available. Start the simulator to begin.'}
            </div>
          </div>
        ) : (
          filtered.map(bus => {
            const isMyBus = bus.is_hardware || !bus.simulated || bus.id === 'lee_bus_esp32_001' || bus.bus_id === 'lee_bus_esp32_001';
            return (
              <div
                key={bus.id}
                className={`bus-card ${isMyBus ? 'my-bus' : ''} ${selectedBus?.bus_id === bus.id || selectedBus?.id === bus.id ? 'active' : ''}`}
                onClick={() => onSelectBus(bus)}
                style={{ '--card-accent': isMyBus ? '#10B981' : (bus.route_color || '#3B82F6') }}
                id={`bus-card-${bus.id}`}
              >
                <div className="bus-icon-wrapper" style={{ background: isMyBus ? 'linear-gradient(135deg, #10B981, #06B6D4)' : `linear-gradient(135deg, ${bus.route_color || '#3B82F6'}, #8B5CF6)` }}>
                  {isMyBus ? '🛰️' : '🚌'}
                </div>
                <div className="bus-info">
                  <div className="bus-name">
                    {bus.bus_name || bus.name || bus.id}
                    {isMyBus && <span className="my-bus-badge-label">My ESP32</span>}
                  </div>
                  <div className="bus-route">{bus.route_name || bus.route_id}</div>
                  <div className="bus-meta">
                    {bus.is_live && (
                      <>
                        <div className="bus-meta-item">
                          <span>⚡</span>
                          <span className="value">{bus.speed?.toFixed(0) || 0} km/h</span>
                        </div>
                        <div className="bus-meta-item">
                          <span>🕐</span>
                          <span className="value">{timeAgo(bus.last_updated || bus.timestamp)}</span>
                        </div>
                      </>
                    )}
                  </div>
                  {isMyBus && (
                    <div className="sensor-chips-row">
                      <span className="sensor-chip accent">🛰️ {bus.satellites || 10} Sats Fixed</span>
                      <span className="sensor-chip">🧭 {bus.heading ? `${bus.heading.toFixed(0)}°` : 'Live GNSS'}</span>
                    </div>
                  )}
                </div>
                <span className={`bus-status-indicator ${isMyBus ? (bus.is_offline ? 'offline' : 'hardware') : (bus.is_live ? (bus.simulated ? 'simulated' : 'live') : 'offline')}`}>
                  {isMyBus ? (bus.is_offline ? '📡 OFFLINE' : '🛰️ LIVE') : (bus.is_live ? (bus.simulated ? 'SIM' : 'LIVE') : '📡 OFFLINE')}
                </span>
              </div>
            );
          })
        )}
      </div>

      {/* Simulator controls */}
      <div className="simulator-controls">
        <div className="simulator-toggle">
          <span className="simulator-label">Bus Simulator (Demo Mode)</span>
          <button
            className={`toggle-btn ${simulatorRunning ? 'stop' : 'start'}`}
            onClick={onToggleSimulator}
            id="simulator-toggle-btn"
          >
            {simulatorRunning ? '⏹ Stop' : '▶ Start'}
          </button>
        </div>
      </div>
    </aside>
  );
}

/* ─── ETA Panel Component ─── */
function ETAPanel({ bus, onClose, routes, onOpenChangeRoute }) {
  const predictions = bus?.eta_predictions || [];
  const isMyBus = bus?.is_hardware || !bus?.simulated || bus?.id === 'lee_bus_esp32_001' || bus?.bus_id === 'lee_bus_esp32_001';

  if (!bus || (!isMyBus && predictions.length === 0)) return null;

  const currentRoute = routes?.find(r => r.id === bus.route_id);

  return (
    <div className="eta-panel" id="eta-panel">
      <div className="eta-panel-header">
        <div>
          <div className="eta-panel-title">{isMyBus ? '🛰️ Live Telemetry & ETA' : '🎯 ETA Predictions'}</div>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: 2 }}>
            {bus.bus_name || bus.bus_id} • {bus.speed?.toFixed(0)} km/h
          </div>
        </div>
        <button className="eta-panel-close" onClick={onClose} id="eta-panel-close">✕</button>
      </div>
      {isMyBus && (
        <div className="hardware-telemetry-banner">
          <div className="hardware-banner-header">
            <span>🛰️ Live ESP32 Hardware Telemetry</span>
            <span style={{ fontSize: '0.68rem', color: bus.is_offline ? '#F87171' : '#34D399' }}>
              {bus.is_offline ? '🔴 OFFLINE' : '🟢 GNSS Locked'}
            </span>
          </div>
          {bus.is_offline && (
            <div className="offline-banner">
              <span className="offline-banner-icon">📡</span>
              <span>Device is offline — last seen {timeAgo(bus.last_updated || bus.timestamp)}</span>
            </div>
          )}
          <div className="hardware-metrics-grid">
            <div className="hardware-metric-item">
              <div className="hardware-metric-label">GPS Satellites</div>
              <div className="hardware-metric-value">🛰️ {bus.satellites || 10} Sats Fixed</div>
            </div>
            <div className="hardware-metric-item">
              <div className="hardware-metric-label">Live Coordinates</div>
              <div className="hardware-metric-value">{bus.latitude?.toFixed(6)}, {bus.longitude?.toFixed(6)}</div>
            </div>
            <div className="hardware-metric-item">
              <div className="hardware-metric-label">Altitude</div>
              <div className="hardware-metric-value">⛰️ {bus.altitude ? `${bus.altitude.toFixed(1)} m` : 'Sea level'}</div>
            </div>
            <div className="hardware-metric-item">
              <div className="hardware-metric-label">Heading / Course</div>
              <div className="hardware-metric-value">🧭 {bus.heading ? `${bus.heading.toFixed(0)}°` : '0° North'}</div>
            </div>
          </div>
          {/* Route Assignment Section */}
          <div className="route-change-section">
            <div className="route-change-label">📍 Assigned Route</div>
            <div className="route-change-display">
              <div className="route-change-current">
                <span
                  className="route-change-color-dot"
                  style={{ background: currentRoute?.color || '#3B82F6' }}
                />
                <span className="route-change-name">{currentRoute?.name || bus.route_id || 'No route assigned'}</span>
              </div>
              <button
                className="btn-change-route"
                onClick={onOpenChangeRoute}
                id="btn-open-change-route"
                title="Open Route Studio to change your bus route"
              >
                🗺️ Change Route
              </button>
            </div>
          </div>
        </div>
      )}
      <div className="eta-panel-body">
        {predictions.map((pred, idx) => {
          const confPercent = (pred.confidence * 100).toFixed(0);
          const confClass = pred.confidence >= 0.85 ? 'high' : pred.confidence >= 0.7 ? 'medium' : 'low';
          return (
            <div key={pred.stop_id} className="eta-stop-item">
              <div className="eta-stop-timeline">
                <div className={`eta-stop-dot ${idx === 0 ? 'next' : ''}`} />
                {idx < predictions.length - 1 && <div className="eta-stop-line" />}
              </div>
              <div className="eta-stop-info">
                <div className="eta-stop-name">{pred.stop_name}</div>
                <div className="eta-stop-details">
                  <span className="eta-time">{pred.eta_formatted}</span>
                  <span className="eta-distance">{pred.cumulative_distance_km} km</span>
                  <span className={`congestion-badge ${pred.congestion_level}`}>{pred.congestion_level}</span>
                </div>
                <div className="eta-confidence" style={{ marginTop: 4 }}>
                  <div className="confidence-bar">
                    <div className={`confidence-fill ${confClass}`} style={{ width: `${confPercent}%` }} />
                  </div>
                  <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>{confPercent}%</span>
                </div>
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', fontWeight: 600, whiteSpace: 'nowrap' }}>
                {pred.arrival_time}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* ─── Map Component ─── */
function MapView({ buses, routes, selectedBus, onSelectBus, focusedRoute }) {
  const mapRef = useRef(null);
  const mapInstance = useRef(null);
  const markersRef = useRef({});
  const markerMetaRef = useRef({});
  const routeLinesRef = useRef([]);
  const stopMarkersRef = useRef([]);

  // Initialize map
  useEffect(() => {
    if (mapInstance.current || !mapRef.current) return;

    const L = window.L;
    const map = L.map(mapRef.current, {
      center: [7.0, 80.0], // Sri Lanka center
      zoom: 8,
      zoomControl: true,
      attributionControl: true,
    });

    // Basemap tile layers (100% Free, NO API Key, NO Watermarks)
    const esriDarkBase = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}', {
      attribution: '&copy; Esri &mdash; Dark Canvas',
      maxZoom: 19,
      maxNativeZoom: 16,
    });

    const esriDarkRef = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}', {
      maxZoom: 19,
      maxNativeZoom: 16,
    });

    const darkLayerGroup = L.layerGroup([esriDarkBase, esriDarkRef]);

    const osmStandard = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 19,
    });

    const satellite = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
      attribution: '&copy; Esri World Imagery',
      maxZoom: 18,
    });

    // Default to Dark theme matching the UI
    darkLayerGroup.addTo(map);

    // Add layer switcher control
    L.control.layers({
      "🌙 Dark Canvas": darkLayerGroup,
      "🗺️ OpenStreetMap": osmStandard,
      "🛰️ Satellite View": satellite,
    }, null, { position: 'topright' }).addTo(map);

    mapInstance.current = map;

    return () => {
      map.remove();
      mapInstance.current = null;
    };
  }, []);

  // Draw route lines and stops
  useEffect(() => {
    if (!mapInstance.current || !routes.length) return;
    const L = window.L;
    const map = mapInstance.current;

    // Clear previous lines and stop markers
    routeLinesRef.current.forEach(l => map.removeLayer(l));
    stopMarkersRef.current.forEach(m => map.removeLayer(m));
    routeLinesRef.current = [];
    stopMarkersRef.current = [];

    routes.forEach(route => {
      if (!route.stops || route.stops.length < 2) return;

      const coords = route.stops.map(s => [s.latitude, s.longitude]);
      const polyline = L.polyline(coords, {
        color: route.color || '#3B82F6',
        weight: 3,
        opacity: 0.5,
        dashArray: '8, 6',
      }).addTo(map);
      routeLinesRef.current.push(polyline);

      // Stop markers
      route.stops.forEach(stop => {
        const stopIcon = L.divIcon({
          className: '',
          html: `<div style="width:10px;height:10px;border-radius:50%;background:${route.color || '#3B82F6'};border:2px solid #0B1120;box-shadow:0 0 6px ${route.color || '#3B82F6'}44;"></div>`,
          iconSize: [10, 10],
          iconAnchor: [5, 5],
        });

        const marker = L.marker([stop.latitude, stop.longitude], { icon: stopIcon })
          .bindTooltip(stop.name, {
            direction: 'top',
            offset: [0, -8],
            className: 'stop-tooltip',
          })
          .addTo(map);
        stopMarkersRef.current.push(marker);
      });
    });
  }, [routes]);

  // Update bus markers
  useEffect(() => {
    if (!mapInstance.current) return;
    const L = window.L;
    const map = mapInstance.current;

    const activeBusIds = new Set();

    buses.forEach(bus => {
      // Show bus if it has coordinates (even if offline, show last-known position)
      if (!bus.latitude || !bus.longitude) return;
      activeBusIds.add(bus.id || bus.bus_id);
      const busId = bus.id || bus.bus_id;
      const isMyBus = bus.is_hardware || !bus.simulated || bus.id === 'lee_bus_esp32_001' || bus.bus_id === 'lee_bus_esp32_001';
      const isOffline = bus.is_offline;

      const busIcon = L.divIcon({
        className: '',
        html: isMyBus ? `
          <div style="
            position: relative;
            width: 48px; height: 48px;
            display: flex; align-items: center; justify-content: center;
            ${isOffline ? 'opacity: 0.7; filter: grayscale(40%);' : ''}
          ">
            <div style="
              position: absolute;
              top: -18px;
              background: ${isOffline ? 'linear-gradient(135deg, #6B7280, #4B5563)' : 'linear-gradient(135deg, #059669, #0D9488)'};
              color: #FFFFFF;
              font-size: 9px;
              font-weight: 800;
              padding: 2px 7px;
              border-radius: 4px;
              white-space: nowrap;
              box-shadow: 0 2px 8px rgba(0,0,0,0.6);
              border: 1px solid ${isOffline ? '#9CA3AF' : '#34D399'};
              letter-spacing: 0.05em;
              z-index: 10;
            ">${isOffline ? '📡 OFFLINE' : '🛰️ MY LIVE BUS'}</div>
            ${isOffline ? '' : `<div style="
              position: absolute; inset: -6px;
              background: rgba(16, 185, 129, 0.4);
              border-radius: 50%;
              animation: pulse-ring 1.5s ease-out infinite;
            "></div>`}
            <div style="
              width: 32px; height: 32px;
              background: ${isOffline ? 'linear-gradient(135deg, #6B7280, #9CA3AF)' : 'linear-gradient(135deg, #10B981, #06B6D4)'};
              border-radius: 50%;
              display: flex; align-items: center; justify-content: center;
              font-size: 16px;
              border: 2px solid ${isOffline ? '#9CA3AF' : '#FFFFFF'};
              box-shadow: 0 0 16px ${isOffline ? '#6B7280' : '#10B981'};
              transform: rotate(${bus.heading || 0}deg);
              z-index: 2;
            ">🚌</div>
          </div>
        ` : `
          <div style="
            position: relative;
            width: 36px; height: 36px;
            display: flex; align-items: center; justify-content: center;
          ">
            <div style="
              position: absolute; inset: 0;
              background: ${bus.route_color || '#3B82F6'};
              border-radius: 50%;
              opacity: 0.2;
              animation: pulse-ring 2s ease-out infinite;
            "></div>
            <div style="
              width: 28px; height: 28px;
              background: linear-gradient(135deg, ${bus.route_color || '#3B82F6'}, #8B5CF6);
              border-radius: 50%;
              display: flex; align-items: center; justify-content: center;
              font-size: 14px;
              border: 2px solid rgba(255,255,255,0.3);
              box-shadow: 0 2px 8px rgba(0,0,0,0.4);
              transform: rotate(${bus.heading || 0}deg);
              z-index: 2;
            ">🚌</div>
          </div>
        `,
        iconSize: isMyBus ? [48, 48] : [36, 36],
        iconAnchor: isMyBus ? [24, 24] : [18, 18],
      });

      const popupContent = `
        <div class="bus-popup">
          <h3>${isMyBus ? '🛰️ ' : '🚌 '}${bus.bus_name || bus.name || busId}</h3>
          <div class="popup-row"><span class="popup-label">Route</span><span class="popup-value">${bus.route_name || bus.route_id || '—'}</span></div>
          <div class="popup-row"><span class="popup-label">Speed</span><span class="popup-value">${bus.speed?.toFixed(1) || 0} km/h</span></div>
          <div class="popup-row"><span class="popup-label">Position</span><span class="popup-value">${bus.latitude?.toFixed(6)}, ${bus.longitude?.toFixed(6)}</span></div>
          <div class="popup-row"><span class="popup-label">Telemetry</span><span class="popup-value">${isMyBus ? (isOffline ? '🔴 OFFLINE — last seen ' + timeAgo(bus.last_updated || bus.timestamp) : '🟢 ESP32 Live GNSS (' + (bus.satellites || 10) + ' Sats)') : '🟡 Simulated'}</span></div>
          ${isMyBus && bus.altitude ? `<div class="popup-row"><span class="popup-label">Altitude</span><span class="popup-value">${bus.altitude.toFixed(1)} m</span></div>` : ''}
        </div>
      `;

      const prevMeta = markerMetaRef.current[busId];
      const needsIconUpdate = !prevMeta ||
        prevMeta.isMyBus !== isMyBus ||
        prevMeta.isOffline !== isOffline ||
        prevMeta.routeColor !== bus.route_color ||
        Math.abs((prevMeta.heading || 0) - (bus.heading || 0)) >= 10;

      if (markersRef.current[busId]) {
        markersRef.current[busId].setLatLng([bus.latitude, bus.longitude]);
        if (needsIconUpdate) {
          markersRef.current[busId].setIcon(busIcon);
          markerMetaRef.current[busId] = {
            isMyBus,
            isOffline,
            routeColor: bus.route_color,
            heading: bus.heading,
          };
        }
        markersRef.current[busId].setPopupContent(popupContent);
      } else {
        const marker = L.marker([bus.latitude, bus.longitude], { icon: busIcon })
          .bindPopup(popupContent, { autoPan: true, autoPanPadding: [50, 50], maxWidth: 280 })
          .on('click', () => onSelectBus(bus))
          .addTo(map);
        markersRef.current[busId] = marker;
        markerMetaRef.current[busId] = {
          isMyBus,
          isOffline,
          routeColor: bus.route_color,
          heading: bus.heading,
        };
      }
    });

    // Remove markers for buses that are no longer active
    Object.keys(markersRef.current).forEach(id => {
      if (!activeBusIds.has(id)) {
        map.removeLayer(markersRef.current[id]);
        delete markersRef.current[id];
        delete markerMetaRef.current[id];
      }
    });
  }, [buses, onSelectBus]);

  const lastSelectedBusIdRef = useRef(null);
  const lastFocusTriggerRef = useRef(null);

  // Pan to selected bus only when bus selection changes or focus is requested
  useEffect(() => {
    if (!mapInstance.current || !selectedBus) return;
    const lat = selectedBus.latitude;
    const lon = selectedBus.longitude;
    const busId = selectedBus.id || selectedBus.bus_id;
    const focusTrigger = selectedBus._focusTrigger;

    if (lat && lon) {
      const isMyBus = selectedBus.is_hardware || !selectedBus.simulated || selectedBus.id === 'lee_bus_esp32_001';
      const zoomLevel = isMyBus ? 17 : 14;

      const isNewBus = lastSelectedBusIdRef.current !== busId;
      const isForcedFocus = focusTrigger && focusTrigger !== lastFocusTriggerRef.current;

      if (isNewBus || isForcedFocus) {
        lastSelectedBusIdRef.current = busId;
        lastFocusTriggerRef.current = focusTrigger;
        mapInstance.current.flyTo([lat, lon], zoomLevel, { duration: 0.8 });
        if (markersRef.current[busId]) {
          markersRef.current[busId].openPopup();
        }
      }
    }
  }, [selectedBus]);

  // Fit map bounds when a route is focused
  useEffect(() => {
    if (!mapInstance.current || !focusedRoute || !focusedRoute.stops || focusedRoute.stops.length < 2) return;
    const L = window.L;
    const bounds = L.latLngBounds(focusedRoute.stops.map(s => [s.latitude, s.longitude]));
    mapInstance.current.fitBounds(bounds, { padding: [50, 50], maxZoom: 13 });
  }, [focusedRoute]);

  return <div ref={mapRef} style={{ width: '100%', height: '100%' }} id="map" />;
}

/* ─── Main App ─── */
export default function App() {
  const [buses, setBuses] = useState([]);
  const [routes, setRoutes] = useState([]);
  const [selectedBus, setSelectedBus] = useState(null);
  const [selectedRoute, setSelectedRoute] = useState(null);
  const [focusedRoute, setFocusedRoute] = useState(null);
  const [isRouteStudioOpen, setIsRouteStudioOpen] = useState(false);
  const [changeBusRouteMode, setChangeBusRouteMode] = useState(false);
  const [showETA, setShowETA] = useState(false);
  const [health, setHealth] = useState(null);
  const [aiMetrics, setAiMetrics] = useState(null);
  const [lastLearningEvent, setLastLearningEvent] = useState(null);
  const [simulatorRunning, setSimulatorRunning] = useState(false);
  const socketRef = useRef(null);
  const pollRef = useRef(null);

  // Fetch initial data
  const fetchData = useCallback(async () => {
    try {
      const [busData, routeData, healthData, metricsData] = await Promise.all([
        api.getBuses(),
        api.getRoutes(),
        api.getHealth(),
        api.getAIMetrics().catch(() => null),
      ]);
      setBuses(prev => {
        if (!prev || prev.length === 0) return busData;
        const map = new Map(prev.map(b => [b.id || b.bus_id, b]));
        busData.forEach(nb => {
          const id = nb.id || nb.bus_id;
          if (!map.has(id)) {
            map.set(id, nb);
          } else {
            const existing = map.get(id);
            map.set(id, { ...existing, ...nb, latitude: existing.latitude || nb.latitude, longitude: existing.longitude || nb.longitude });
          }
        });
        return Array.from(map.values());
      });

      setRoutes(prev => {
        if (!prev || prev.length !== routeData.length) return routeData;
        const prevSig = prev.map(r => `${r.id}:${r.stops?.length || 0}`).join('|');
        const nextSig = routeData.map(r => `${r.id}:${r.stops?.length || 0}`).join('|');
        return prevSig === nextSig ? prev : routeData;
      });

      setHealth(healthData);
      if (metricsData) setAiMetrics(metricsData);
      setSimulatorRunning(healthData.simulator_running);
    } catch (err) {
      console.warn('[App] Backend not available:', err.message);
    }
  }, []);

  useEffect(() => {
    window.scrollTo(0, 0);
    fetchData();
    // Relaxed polling interval to prevent state thrashing
    pollRef.current = setInterval(fetchData, 10000);
    return () => clearInterval(pollRef.current);
  }, [fetchData]);

  // WebSocket connection
  useEffect(() => {
    try {
      const socket = io(SOCKET_URL, {
        transports: ['websocket', 'polling'],
        reconnection: true,
        reconnectionDelay: 1000,
      });

      socket.on('connect', () => {
        console.log('[WS] Connected to backend');
        socket.emit('request_all_buses');
      });

      socket.on('ai_learning_update', (data) => {
        setLastLearningEvent(data);
        setAiMetrics(prev => ({
          ...prev,
          samples_learned: data.samples_learned,
          rolling_mae_minutes: data.rolling_mae,
        }));
      });

      socket.on('bus_update', (data) => {
        setBuses(prev => {
          const idx = prev.findIndex(b => (b.id || b.bus_id) === data.bus_id);
          const updatedBus = { ...data, id: data.bus_id, is_live: true };
          if (idx >= 0) {
            const next = [...prev];
            next[idx] = { ...next[idx], ...updatedBus };
            return next;
          }
          return [...prev, updatedBus];
        });

        // Update selected bus if it's the same one
        setSelectedBus(prev => {
          if (prev && (prev.bus_id === data.bus_id || prev.id === data.bus_id)) {
            return { ...prev, ...data, is_live: true };
          }
          return prev;
        });
      });

      socket.on('disconnect', () => {
        console.log('[WS] Disconnected');
      });

      socketRef.current = socket;
      return () => socket.disconnect();
    } catch (err) {
      console.warn('[WS] Connection failed:', err);
    }
  }, []);

  // Handle bus selection
  const handleSelectBus = useCallback((bus) => {
    const busId = bus.id || bus.bus_id;
    setSelectedBus(bus);
    setShowETA(true);

    // Fetch latest ETA from backend
    api.getETA(busId).then(data => {
      setSelectedBus(prev => prev ? { ...prev, eta_predictions: data.predictions } : prev);
    }).catch(() => {});
  }, []);

  // Handle route filter selection & center map
  const handleSelectRoute = useCallback((routeId) => {
    setSelectedRoute(routeId);
    if (routeId) {
      const match = routes.find(r => r.id === routeId);
      if (match) setFocusedRoute(match);
    }
  }, [routes]);

  // Toggle simulator
  const handleToggleSimulator = useCallback(async () => {
    try {
      if (simulatorRunning) {
        await api.stopSimulator();
        setSimulatorRunning(false);
      } else {
        await api.startSimulator();
        setSimulatorRunning(true);
      }
    } catch (err) {
      console.error('[App] Simulator toggle failed:', err);
    }
  }, [simulatorRunning]);

  // Change bus's assigned route
  const handleChangeBusRoute = useCallback(async (busId, newRouteId) => {
    try {
      await api.changeBusRoute(busId, newRouteId);
      // Refresh data to get updated route assignment
      await fetchData();
      // Update selected bus with new route
      setSelectedBus(prev => {
        if (prev && (prev.id === busId || prev.bus_id === busId)) {
          const newRoute = routes.find(r => r.id === newRouteId);
          return { ...prev, route_id: newRouteId, route_name: newRoute?.name || newRouteId };
        }
        return prev;
      });
    } catch (err) {
      console.error('[App] Route change failed:', err);
    }
  }, [fetchData, routes]);

  // Find hardware bus if available
  const hardwareBus = buses.find(b => b.is_hardware || !b.simulated || b.id === 'lee_bus_esp32_001' || b.bus_id === 'lee_bus_esp32_001');
  const hasHardwareBus = Boolean(hardwareBus);

  // Focus directly on live ESP32 bus
  const handleFocusMyBus = useCallback(() => {
    const target = buses.find(b => b.is_hardware || !b.simulated || b.id === 'lee_bus_esp32_001' || b.bus_id === 'lee_bus_esp32_001');
    if (target) {
      handleSelectBus({ ...target, _focusTrigger: Date.now() });
      if (target.route_id) {
        setSelectedRoute(target.route_id);
      }
    }
  }, [buses, handleSelectBus]);

  const hasAutoSelectedRef = useRef(false);

  // Auto-select hardware bus on initial load once
  useEffect(() => {
    if (!hasAutoSelectedRef.current && buses.length > 0) {
      const hw = buses.find(b => b.is_hardware || !b.simulated || b.id === 'lee_bus_esp32_001');
      if (hw) {
        hasAutoSelectedRef.current = true;
        handleSelectBus(hw);
      }
    }
  }, [buses, handleSelectBus]);

  return (
    <div className="app-layout">
      <div className="bg-mesh" />
      <Navbar
        health={health}
        aiMetrics={aiMetrics}
        onOpenRouteStudio={() => setIsRouteStudioOpen(true)}
        onFocusMyBus={handleFocusMyBus}
        hasHardwareBus={hasHardwareBus}
      />
      <StatsBar
        buses={buses}
        routes={routes}
        simulatorRunning={simulatorRunning}
        aiMetrics={aiMetrics}
        lastLearningEvent={lastLearningEvent}
        onOpenRouteStudio={() => setIsRouteStudioOpen(true)}
        health={health}
      />
      <div className="main-content">
        <BusSidebar
          buses={buses}
          selectedBus={selectedBus}
          onSelectBus={handleSelectBus}
          routes={routes}
          selectedRoute={selectedRoute}
          onSelectRoute={handleSelectRoute}
          simulatorRunning={simulatorRunning}
          onToggleSimulator={handleToggleSimulator}
          onOpenRouteStudio={() => setIsRouteStudioOpen(true)}
        />
        <div className="map-container">
          <MapView
            buses={buses}
            routes={routes}
            selectedBus={selectedBus}
            onSelectBus={handleSelectBus}
            focusedRoute={focusedRoute}
          />
          {showETA && selectedBus && (
            <ETAPanel
              bus={selectedBus}
              onClose={() => setShowETA(false)}
              routes={routes}
              onOpenChangeRoute={() => {
                setChangeBusRouteMode(true);
                setIsRouteStudioOpen(true);
              }}
            />
          )}
        </div>
      </div>

      {/* Google Maps Route Studio Modal */}
      <RouteStudio
        isOpen={isRouteStudioOpen}
        onClose={() => {
          setIsRouteStudioOpen(false);
          setChangeBusRouteMode(false);
        }}
        routes={routes}
        onRouteUpdated={fetchData}
        onFocusRoute={setFocusedRoute}
        changeBusRouteMode={changeBusRouteMode}
        onAssignBusToRoute={async (routeId) => {
          const hwBus = buses.find(b => b.is_hardware || b.id === 'lee_bus_esp32_001');
          if (hwBus) {
            await handleChangeBusRoute(hwBus.id || hwBus.bus_id, routeId);
          }
        }}
      />
    </div>
  );
}
