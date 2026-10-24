import { useState, useEffect, useCallback } from 'react';
import api from './api.js';

const ROUTE_COLOR_PRESETS = [
  '#3B82F6', // Blue
  '#10B981', // Emerald
  '#F59E0B', // Amber
  '#EF4444', // Red
  '#8B5CF6', // Purple
  '#06B6D4', // Cyan
  '#EC4899', // Pink
];

const POPULAR_ROUTE_PRESETS = [
  { number: '04', label: 'Route 04 (Chilaw)' },
  { number: '01', label: 'Route 01 (Kandy)' },
  { number: '02', label: 'Route 02 (Galle / Matara)' },
  { number: '138', label: 'Route 138 (Maharagama)' },
  { number: '177', label: 'Route 177 (Kaduwela)' },
  { number: '120', label: 'Route 120 (Horana)' },
  { number: '187', label: 'Route 187 (Airport)' },
  { number: '87', label: 'Route 87 (Jaffna / Vavuniya)' },
  { number: '240', label: 'Route 240 (Negombo)' },
  { number: '100', label: 'Route 100 (Panadura)' },
  { number: '05', label: 'Route 05 (Kurunegala)' },
  { number: '99', label: 'Route 99 (Badulla)' },
];

const SRI_LANKA_PRESETS = [
  { origin: 'Colombo Fort', destination: 'Kandy' },
  { origin: 'Colombo Fort', destination: 'Galle' },
  { origin: 'Colombo Fort', destination: 'Negombo' },
  { origin: 'Pettah', destination: 'Maharagama' },
  { origin: 'Kollupitiya', destination: 'Kaduwela' },
  { origin: 'Chilaw', destination: 'Colombo Fort' },
];

export default function RouteStudio({ isOpen, onClose, routes, onRouteUpdated, onFocusRoute, changeBusRouteMode, onAssignBusToRoute }) {
  const [activeTab, setActiveTab] = useState('discover'); // 'discover' | 'custom' | 'manage'
  
  // Search Mode inside Discover Tab: 'byNumber' (Default!) or 'byLocation'
  const [discoverMode, setDiscoverMode] = useState('byNumber');

  // Route Number Search State (Default)
  const [routeNumberQuery, setRouteNumberQuery] = useState('');
  const [numberResults, setNumberResults] = useState([]);
  const [isNumberSearching, setIsNumberSearching] = useState(false);
  const [numberConfigs, setNumberConfigs] = useState({});

  // Google Point-to-Point State
  const [origin, setOrigin] = useState('Colombo Fort');
  const [destination, setDestination] = useState('Kandy');
  const [isSearching, setIsSearching] = useState(false);
  const [searchResults, setSearchResults] = useState(null);
  const [searchError, setSearchError] = useState(null);
  const [addingRouteIndex, setAddingRouteIndex] = useState(null);
  const [customConfigs, setCustomConfigs] = useState({}); // { [idx]: { name, color, busCount } }

  // Custom Route Creator State
  const [customName, setCustomName] = useState('');
  const [customStopsText, setCustomStopsText] = useState('');
  const [customColor, setCustomColor] = useState('#3B82F6');
  const [customBuses, setCustomBuses] = useState(2);
  const [isCreatingCustom, setIsCreatingCustom] = useState(false);
  const [customError, setCustomError] = useState(null);

  // Manage Routes State
  const [expandedRouteId, setExpandedRouteId] = useState(null);
  const [inlineNewStop, setInlineNewStop] = useState({});
  const [actionLoading, setActionLoading] = useState({});

  // Fetch Route Catalog by Number on query change or mount
  const fetchRoutesByNumber = useCallback(async (query) => {
    setIsNumberSearching(true);
    try {
      const data = await api.lookupRoutes(query);
      if (data.routes) {
        setNumberResults(data.routes);
        // Pre-fill configs
        const configs = {};
        data.routes.forEach((r, idx) => {
          configs[idx] = {
            name: r.name,
            color: r.color || ROUTE_COLOR_PRESETS[idx % ROUTE_COLOR_PRESETS.length],
            busCount: 2,
          };
        });
        setNumberConfigs(configs);
      }
    } catch (err) {
      console.warn('Failed to lookup routes by number:', err);
    } finally {
      setIsNumberSearching(false);
    }
  }, []);

  useEffect(() => {
    if (isOpen) {
      fetchRoutesByNumber(routeNumberQuery);
    }
  }, [isOpen, fetchRoutesByNumber, routeNumberQuery]);

  // Auto-configure tabs when opened in bus route change mode
  useEffect(() => {
    if (isOpen && changeBusRouteMode) {
      setActiveTab('discover');
      setDiscoverMode('byLocation');
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen]);

  if (!isOpen) return null;

  /* ── Search Google Maps Transit (Point to Point) ── */
  const handleSearchGoogleRoutes = async (e) => {
    if (e) e.preventDefault();
    if (!origin.trim() || !destination.trim()) return;

    setIsSearching(true);
    setSearchError(null);
    setSearchResults(null);

    try {
      const data = await api.searchRoute(origin.trim(), destination.trim());
      if (data.routes && data.routes.length > 0) {
        setSearchResults(data.routes);
        const configs = {};
        data.routes.forEach((r, idx) => {
          configs[idx] = {
            name: r.route_name,
            color: r.color || ROUTE_COLOR_PRESETS[idx % ROUTE_COLOR_PRESETS.length],
            busCount: 2,
          };
        });
        setCustomConfigs(configs);
      } else {
        setSearchError('No transit routes returned. Try another pair of towns.');
      }
    } catch (err) {
      setSearchError(err.message || 'Failed to search Google Maps transit directions');
    } finally {
      setIsSearching(false);
    }
  };

  /* ── Add Route from Catalog (By Number) ── */
  const handleAddCatalogRoute = async (route, idx) => {
    setAddingRouteIndex(`num_${idx}`);
    const config = numberConfigs[idx] || {
      name: route.name,
      color: route.color || '#10B981',
      busCount: 2,
    };

    try {
      await api.addRoute({
        route_name: config.name || route.name,
        color: config.color,
        bus_count: config.busCount,
        stops: route.stops,
      });
      await onRouteUpdated();
      setActiveTab('manage');
    } catch (err) {
      alert('Error adding route: ' + (err.message || 'Unknown error'));
    } finally {
      setAddingRouteIndex(null);
    }
  };

  /* ── Add Discovered Route (Point to Point) ── */
  const handleAddDiscoveredRoute = async (route, idx, assignBus = false) => {
    setAddingRouteIndex(`pt_${idx}`);
    const config = customConfigs[idx] || {
      name: route.route_name,
      color: route.color || '#3B82F6',
      busCount: assignBus ? 0 : 2,  // 0 simulated buses when assigning real bus
    };

    try {
      const result = await api.addRoute({
        route_name: config.name || route.route_name,
        color: config.color,
        bus_count: config.busCount,
        stops: route.stops,
      });
      await onRouteUpdated();

      // If assigning bus, call the assign callback with the new route ID
      if (assignBus && onAssignBusToRoute && result?.route_id) {
        await onAssignBusToRoute(result.route_id);
        onClose();
      } else {
        setActiveTab('manage');
      }
    } catch (err) {
      alert('Error adding route: ' + (err.message || 'Unknown error'));
    } finally {
      setAddingRouteIndex(null);
    }
  };

  /* ── Create Custom Route with Geocoding ── */
  const handleCreateCustomRoute = async (e) => {
    e.preventDefault();
    if (!customName.trim() || !customStopsText.trim()) return;

    setIsCreatingCustom(true);
    setCustomError(null);

    try {
      const stopNames = customStopsText
        .split(',')
        .map(s => s.trim())
        .filter(s => s.length > 0);

      if (stopNames.length < 2) {
        setCustomError('Please provide at least 2 stops separated by commas (e.g. Colombo, Peliyagoda, Kandy)');
        setIsCreatingCustom(false);
        return;
      }

      // Geocode all stops in sequence
      const resolvedStops = [];
      for (const name of stopNames) {
        try {
          const geoData = await api.geocode(name);
          if (geoData.results && geoData.results.length > 0) {
            resolvedStops.push({
              name: name,
              latitude: geoData.results[0].latitude,
              longitude: geoData.results[0].longitude,
            });
          }
        } catch (gErr) {
          console.warn(`Could not geocode stop: ${name}`, gErr);
        }
      }

      if (resolvedStops.length < 2) {
        setCustomError('Google Maps could not resolve enough stop locations. Check your stop names.');
        setIsCreatingCustom(false);
        return;
      }

      await api.addRoute({
        route_name: customName.trim(),
        color: customColor,
        bus_count: parseInt(customBuses, 10) || 1,
        stops: resolvedStops,
      });

      setCustomName('');
      setCustomStopsText('');
      await onRouteUpdated();
      setActiveTab('manage');
    } catch (err) {
      setCustomError(err.message || 'Failed to create custom route');
    } finally {
      setIsCreatingCustom(false);
    }
  };

  /* ── Delete a Route ── */
  const handleDeleteRoute = async (routeId, routeName) => {
    if (!window.confirm(`Are you sure you want to delete "${routeName}" and its assigned buses?`)) {
      return;
    }

    setActionLoading(prev => ({ ...prev, [routeId]: true }));
    try {
      await api.deleteRoute(routeId);
      await onRouteUpdated();
    } catch (err) {
      alert('Failed to delete route: ' + err.message);
    } finally {
      setActionLoading(prev => ({ ...prev, [routeId]: false }));
    }
  };

  /* ── Add Intermediate Stop to existing route ── */
  const handleAddStopToRoute = async (routeId) => {
    const stopName = (inlineNewStop[routeId] || '').trim();
    if (!stopName) return;

    setActionLoading(prev => ({ ...prev, [`stop_${routeId}`]: true }));
    try {
      await api.addStopsToRoute(routeId, [stopName]);
      setInlineNewStop(prev => ({ ...prev, [routeId]: '' }));
      await onRouteUpdated();
    } catch (err) {
      alert('Failed to add stop: ' + err.message);
    } finally {
      setActionLoading(prev => ({ ...prev, [`stop_${routeId}`]: false }));
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose} id="route-studio-overlay">
      <div className="modal-dialog" onClick={(e) => e.stopPropagation()} id="route-studio-modal">
        {/* Modal Header */}
        <div className="modal-header">
          <div className="modal-title-wrap">
            <div className="modal-icon-badge">{changeBusRouteMode ? '🚌' : '🗺️'}</div>
            <div>
              <div className="modal-title">
                {changeBusRouteMode ? 'Change My Bus Route' : 'Google Maps Route Studio & Fleet Manager'}
              </div>
              <div className="modal-subtitle">
                {changeBusRouteMode
                  ? 'Select an existing route or discover a new one to assign your ESP32 bus'
                  : 'Search by Route Number or Google Maps Point-to-Point Transit'}
              </div>
            </div>
          </div>
          <button className="modal-close-btn" onClick={onClose} id="route-studio-close-btn">✕</button>
        </div>

        {/* Modal Tabs */}
        <div className="modal-nav">
          <button
            className={`modal-nav-tab ${activeTab === 'discover' ? 'active' : ''}`}
            onClick={() => setActiveTab('discover')}
            id="tab-discover-routes"
          >
            <span>🔍</span>
            <span>Route Discovery</span>
          </button>
          <button
            className={`modal-nav-tab ${activeTab === 'custom' ? 'active' : ''}`}
            onClick={() => setActiveTab('custom')}
            id="tab-custom-routes"
          >
            <span>✏️</span>
            <span>Custom Geocoded Route</span>
          </button>
          <button
            className={`modal-nav-tab ${activeTab === 'manage' ? 'active' : ''}`}
            onClick={() => setActiveTab('manage')}
            id="tab-manage-routes"
          >
            <span>📋</span>
            <span>Active Routes ({routes.length})</span>
          </button>
        </div>

        {/* Modal Body */}
        <div className="modal-body">
          {/* ════════ TAB 1: ROUTE DISCOVERY ════════ */}
          {activeTab === 'discover' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
              {/* Search Mode Switcher: By Number (Default) vs By Point-to-Point */}
              <div className="search-mode-bar">
                <button
                  type="button"
                  className={`search-mode-btn ${discoverMode === 'byNumber' ? 'active' : ''}`}
                  onClick={() => setDiscoverMode('byNumber')}
                  id="btn-mode-by-number"
                >
                  <span>🔢</span>
                  <span>Search by Bus Route Number (Default)</span>
                </button>
                <button
                  type="button"
                  className={`search-mode-btn ${discoverMode === 'byLocation' ? 'active' : ''}`}
                  onClick={() => setDiscoverMode('byLocation')}
                  id="btn-mode-by-location"
                >
                  <span>📍</span>
                  <span>Point-to-Point Search (Google Maps API)</span>
                </button>
              </div>

              {/* ────── MODE A: SEARCH BY ROUTE NUMBER (DEFAULT) ────── */}
              {discoverMode === 'byNumber' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                  {/* Search input */}
                  <div className="form-group">
                    <label className="form-label" style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span>Bus Route Number or Town</span>
                      <span style={{ textTransform: 'none', color: 'var(--primary-light)', fontWeight: 500 }}>
                        e.g. Type "04" for Chilaw, "138" for Maharagama, "177" for Kaduwela
                      </span>
                    </label>
                    <div style={{ position: 'relative' }}>
                      <input
                        type="text"
                        className="form-input"
                        style={{ paddingLeft: 38, fontSize: '0.94rem' }}
                        placeholder="Search by Route Number (e.g. 04, 138, 177, 01, 02) or City Name..."
                        value={routeNumberQuery}
                        onChange={(e) => setRouteNumberQuery(e.target.value)}
                        id="input-route-number-search"
                        autoFocus
                      />
                      <span style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', fontSize: 16, opacity: 0.6 }}>
                        🔍
                      </span>
                      {routeNumberQuery && (
                        <button
                          type="button"
                          onClick={() => setRouteNumberQuery('')}
                          style={{ position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
                        >
                          ✕
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Popular Route Presets */}
                  <div>
                    <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', marginBottom: 6 }}>
                      Popular Sri Lankan Bus Routes (Click to Select):
                    </div>
                    <div className="search-presets">
                      {POPULAR_ROUTE_PRESETS.map((p) => (
                        <button
                          key={p.number}
                          type="button"
                          className={`preset-chip ${routeNumberQuery === p.number ? 'active' : ''}`}
                          style={routeNumberQuery === p.number ? { borderColor: 'var(--primary)', background: 'rgba(59, 130, 246, 0.2)', color: 'white' } : {}}
                          onClick={() => setRouteNumberQuery(p.number)}
                        >
                          🚌 {p.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Results list */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginTop: 4 }}>
                    <div style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
                      {isNumberSearching
                        ? 'Searching Sri Lankan routes...'
                        : numberResults.length > 0
                        ? `Found ${numberResults.length} matching bus routes:`
                        : `No routes found matching "${routeNumberQuery}". Try typing "04", "138", or switch to Point-to-Point.`}
                    </div>

                    <div className="route-results-list">
                      {numberResults.map((r, idx) => {
                        const cfg = numberConfigs[idx] || {
                          name: r.name,
                          color: r.color || '#10B981',
                          busCount: 2,
                        };

                        return (
                          <div key={idx} className="route-card-discovered" style={{ borderLeft: `4px solid ${cfg.color}` }}>
                            <div className="route-card-header">
                              <div>
                                <div className="route-card-title">
                                  <span className="route-number-badge" style={{ background: cfg.color }}>
                                    Route {r.route_number}
                                  </span>
                                  <input
                                    type="text"
                                    className="form-input"
                                    style={{ padding: '4px 8px', fontSize: '0.9rem', fontWeight: 600, width: '100%', maxWidth: 420 }}
                                    value={cfg.name}
                                    onChange={(e) => {
                                      const val = e.target.value;
                                      setNumberConfigs(prev => ({
                                        ...prev,
                                        [idx]: { ...cfg, name: val },
                                      }));
                                    }}
                                  />
                                </div>
                                <div className="route-metrics-row" style={{ marginTop: 8 }}>
                                  <span className="route-metric-item">
                                    <span>📏</span>
                                    <span className="route-metric-val">{r.estimated_distance || '—'}</span>
                                  </span>
                                  <span className="route-metric-item">
                                    <span>⏱️</span>
                                    <span className="route-metric-val">{r.estimated_duration || '—'}</span>
                                  </span>
                                  {r.corridor && (
                                    <span className="route-corridor-badge">
                                      🛣️ {r.corridor}
                                    </span>
                                  )}
                                  {r.agency && (
                                    <span className="route-meta-badge" style={{ background: 'rgba(59, 130, 246, 0.15)', color: '#60A5FA' }}>
                                      {r.agency}
                                    </span>
                                  )}
                                </div>
                              </div>

                              <button
                                className="btn-primary"
                                style={{ whiteSpace: 'nowrap', background: cfg.color }}
                                disabled={addingRouteIndex === `num_${idx}`}
                                onClick={() => handleAddCatalogRoute(r, idx)}
                                id={`btn-import-catalog-${r.route_number}`}
                              >
                                {addingRouteIndex === `num_${idx}` ? 'Deploying...' : `➕ Deploy Route ${r.route_number}`}
                              </button>
                            </div>

                            {/* Stops timeline preview */}
                            <div className="route-stops-preview">
                              {r.stops.map((stop, sIdx) => (
                                <div key={sIdx} style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                                  <span className={`stop-pill ${sIdx === 0 ? 'dep' : sIdx === r.stops.length - 1 ? 'arr' : ''}`}>
                                    {sIdx === 0 ? '🟢 ' : sIdx === r.stops.length - 1 ? '🏁 ' : '📍 '}
                                    {stop.name}
                                  </span>
                                  {sIdx < r.stops.length - 1 && <span className="stop-arrow">➔</span>}
                                </div>
                              ))}
                            </div>

                            {/* Customization controls */}
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12, borderTop: '1px solid var(--border-color)', paddingTop: 10 }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                                <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>Color:</span>
                                <div className="color-picker-row">
                                  {ROUTE_COLOR_PRESETS.map((color) => (
                                    <button
                                      key={color}
                                      type="button"
                                      className={`color-dot-btn ${cfg.color === color ? 'selected' : ''}`}
                                      style={{ background: color }}
                                      onClick={() => {
                                        setNumberConfigs(prev => ({
                                          ...prev,
                                          [idx]: { ...cfg, color },
                                        }));
                                      }}
                                    />
                                  ))}
                                </div>
                              </div>

                              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                                  <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>Fleet Buses:</span>
                                  <select
                                    className="form-input"
                                    style={{ padding: '4px 10px', fontSize: '0.8rem' }}
                                    value={cfg.busCount}
                                    onChange={(e) => {
                                      const count = parseInt(e.target.value, 10);
                                      setNumberConfigs(prev => ({
                                        ...prev,
                                        [idx]: { ...cfg, busCount: count },
                                      }));
                                    }}
                                  >
                                    <option value={1}>1 Bus</option>
                                    <option value={2}>2 Buses</option>
                                    <option value={3}>3 Buses</option>
                                    <option value={4}>4 Buses</option>
                                  </select>
                                </div>

                                <button
                                  type="button"
                                  className="btn-secondary"
                                  style={{ fontSize: '0.74rem', padding: '4px 10px' }}
                                  onClick={() => {
                                    setOrigin(r.origin);
                                    setDestination(r.destination);
                                    setDiscoverMode('byLocation');
                                    handleSearchGoogleRoutes();
                                  }}
                                  title="Query Google Maps Directions for live road transit between these endpoints"
                                >
                                  🌐 Live Google API
                                </button>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              )}

              {/* ────── MODE B: POINT-TO-POINT SEARCH (GOOGLE MAPS API) ────── */}
              {discoverMode === 'byLocation' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                  <form onSubmit={handleSearchGoogleRoutes} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                    <div className="form-row">
                      <div className="form-group">
                        <label className="form-label">Origin Location</label>
                        <input
                          type="text"
                          className="form-input"
                          placeholder="e.g. Colombo Fort"
                          value={origin}
                          onChange={(e) => setOrigin(e.target.value)}
                          id="input-route-origin"
                          required
                        />
                      </div>
                      <div className="form-group">
                        <label className="form-label">Destination Location</label>
                        <input
                          type="text"
                          className="form-input"
                          placeholder="e.g. Kandy"
                          value={destination}
                          onChange={(e) => setDestination(e.target.value)}
                          id="input-route-destination"
                          required
                        />
                      </div>
                    </div>

                    <div>
                      <div style={{ fontSize: '0.74rem', color: 'var(--text-muted)', marginBottom: 4 }}>
                        Quick presets (Sri Lanka):
                      </div>
                      <div className="search-presets">
                        {SRI_LANKA_PRESETS.map((p, i) => (
                          <button
                            key={i}
                            type="button"
                            className="preset-chip"
                            onClick={() => {
                              setOrigin(p.origin);
                              setDestination(p.destination);
                            }}
                          >
                            {p.origin} ➔ {p.destination}
                          </button>
                        ))}
                      </div>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 4 }}>
                      <button
                        type="submit"
                        className="btn-primary"
                        disabled={isSearching}
                        id="btn-search-google-routes"
                      >
                        {isSearching ? (
                          <>
                            <span className="spinner" style={{ width: 14, height: 14, border: '2px solid white', borderTopColor: 'transparent', borderRadius: '50%', display: 'inline-block', animation: 'spin 0.8s linear infinite' }} />
                            <span>Querying Google Maps Transit...</span>
                          </>
                        ) : (
                          <>
                            <span>🔍</span>
                            <span>Find Routes with Google Maps</span>
                          </>
                        )}
                      </button>
                    </div>
                  </form>

                  {searchError && (
                    <div style={{ padding: '12px 16px', background: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.4)', borderRadius: 'var(--radius-sm)', color: '#F87171', fontSize: '0.84rem' }}>
                      ⚠️ {searchError}
                    </div>
                  )}

                  {searchResults && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                      <div style={{ fontSize: '0.84rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
                        Found {searchResults.length} route options from Google Maps:
                      </div>

                      <div className="route-results-list">
                        {searchResults.map((r, idx) => {
                          const cfg = customConfigs[idx] || {
                            name: r.route_name,
                            color: r.color || '#3B82F6',
                            busCount: 2,
                          };

                          return (
                            <div key={idx} className="route-card-discovered">
                              <div className="route-card-header">
                                <div>
                                  <div className="route-card-title">
                                    <span>🚌</span>
                                    <input
                                      type="text"
                                      className="form-input"
                                      style={{ padding: '4px 8px', fontSize: '0.9rem', fontWeight: 600, width: '100%', maxWidth: 420 }}
                                      value={cfg.name}
                                      onChange={(e) => {
                                        const val = e.target.value;
                                        setCustomConfigs(prev => ({
                                          ...prev,
                                          [idx]: { ...cfg, name: val },
                                        }));
                                      }}
                                    />
                                  </div>
                                  <div className="route-metrics-row" style={{ marginTop: 8 }}>
                                    <span className="route-metric-item">
                                      <span>📏</span>
                                      <span className="route-metric-val">{r.total_distance || '—'}</span>
                                    </span>
                                    <span className="route-metric-item">
                                      <span>⏱️</span>
                                      <span className="route-metric-val">{r.total_duration || '—'}</span>
                                    </span>
                                    {r.bus_lines && r.bus_lines.length > 0 && (
                                      <span className="route-meta-badge" style={{ background: 'rgba(59, 130, 246, 0.15)', color: '#60A5FA' }}>
                                        Line {r.bus_lines.map(b => b.line_name).join(' / ')} • {r.bus_lines[0]?.agency || 'Transit'}
                                      </span>
                                    )}
                                  </div>
                                </div>

                                <button
                                  className="btn-primary"
                                  style={{ whiteSpace: 'nowrap' }}
                                  disabled={addingRouteIndex === `pt_${idx}`}
                                  onClick={() => handleAddDiscoveredRoute(r, idx)}
                                  id={`btn-import-route-${idx}`}
                                >
                                  {addingRouteIndex === `pt_${idx}` ? 'Deploying...' : '➕ Add to System'}
                                </button>
                                {changeBusRouteMode && onAssignBusToRoute && (
                                  <button
                                    className="btn-assign-bus"
                                    style={{ whiteSpace: 'nowrap' }}
                                    disabled={addingRouteIndex === `pt_${idx}`}
                                    onClick={() => handleAddDiscoveredRoute(r, idx, true)}
                                    id={`btn-assign-route-${idx}`}
                                  >
                                    {addingRouteIndex === `pt_${idx}` ? 'Assigning...' : '🚌 Add & Assign My Bus'}
                                  </button>
                                )}
                              </div>

                              {/* Stops timeline preview */}
                              <div className="route-stops-preview">
                                {r.stops.map((stop, sIdx) => (
                                  <div key={sIdx} style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                                    <span className={`stop-pill ${sIdx === 0 ? 'dep' : sIdx === r.stops.length - 1 ? 'arr' : ''}`}>
                                      {sIdx === 0 ? '🟢 ' : sIdx === r.stops.length - 1 ? '🏁 ' : '📍 '}
                                      {stop.name}
                                    </span>
                                    {sIdx < r.stops.length - 1 && <span className="stop-arrow">➔</span>}
                                  </div>
                                ))}
                              </div>

                              {/* Route Customization Controls */}
                              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12, borderTop: '1px solid var(--border-color)', paddingTop: 10 }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                                  <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>Color:</span>
                                  <div className="color-picker-row">
                                    {ROUTE_COLOR_PRESETS.map((color) => (
                                      <button
                                        key={color}
                                        type="button"
                                        className={`color-dot-btn ${cfg.color === color ? 'selected' : ''}`}
                                        style={{ background: color }}
                                        onClick={() => {
                                          setCustomConfigs(prev => ({
                                            ...prev,
                                            [idx]: { ...cfg, color },
                                          }));
                                        }}
                                      />
                                    ))}
                                  </div>
                                </div>

                                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                  <span style={{ fontSize: '0.74rem', color: 'var(--text-muted)' }}>Fleet Buses:</span>
                                  <select
                                    className="form-input"
                                    style={{ padding: '4px 10px', fontSize: '0.8rem' }}
                                    value={cfg.busCount}
                                    onChange={(e) => {
                                      const count = parseInt(e.target.value, 10);
                                      setCustomConfigs(prev => ({
                                        ...prev,
                                        [idx]: { ...cfg, busCount: count },
                                      }));
                                    }}
                                  >
                                    <option value={1}>1 Bus</option>
                                    <option value={2}>2 Buses</option>
                                    <option value={3}>3 Buses</option>
                                    <option value={4}>4 Buses</option>
                                  </select>
                                </div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* ════════ TAB 2: CUSTOM WAYPOINT BUILDER ════════ */}
          {activeTab === 'custom' && (
            <form onSubmit={handleCreateCustomRoute} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <div className="form-group">
                <label className="form-label">Route Display Name</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g. Route 177: Kollupitiya - Kaduwela"
                  value={customName}
                  onChange={(e) => setCustomName(e.target.value)}
                  id="custom-route-name"
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Intermediate Stops (Comma-Separated Place Names)</label>
                <textarea
                  className="form-input"
                  style={{ minHeight: 90, resize: 'vertical' }}
                  placeholder="e.g. Kollupitiya, Town Hall, Borella, Rajagiriya, Battaramulla, Malabe, Kaduwela"
                  value={customStopsText}
                  onChange={(e) => setCustomStopsText(e.target.value)}
                  id="custom-route-stops"
                  required
                />
                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                  Google Geocoding API will automatically resolve GPS coordinates for every stop in sequence.
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Theme Color</label>
                  <div className="color-picker-row" style={{ marginTop: 6 }}>
                    {ROUTE_COLOR_PRESETS.map((color) => (
                      <button
                        key={color}
                        type="button"
                        className={`color-dot-btn ${customColor === color ? 'selected' : ''}`}
                        style={{ background: color }}
                        onClick={() => setCustomColor(color)}
                      />
                    ))}
                  </div>
                </div>

                <div className="form-group">
                  <label className="form-label">Initial Fleet Allocation</label>
                  <select
                    className="form-input"
                    value={customBuses}
                    onChange={(e) => setCustomBuses(parseInt(e.target.value, 10))}
                    id="custom-fleet-size"
                  >
                    <option value={1}>1 Bus</option>
                    <option value={2}>2 Buses</option>
                    <option value={3}>3 Buses</option>
                    <option value={4}>4 Buses</option>
                  </select>
                </div>
              </div>

              {customError && (
                <div style={{ padding: '10px 14px', background: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.4)', borderRadius: 'var(--radius-sm)', color: '#F87171', fontSize: '0.82rem' }}>
                  ⚠️ {customError}
                </div>
              )}

              <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 8 }}>
                <button
                  type="submit"
                  className="btn-primary"
                  disabled={isCreatingCustom}
                  id="btn-submit-custom-route"
                >
                  {isCreatingCustom ? (
                    <>
                      <span className="spinner" style={{ width: 14, height: 14, border: '2px solid white', borderTopColor: 'transparent', borderRadius: '50%', display: 'inline-block', animation: 'spin 0.8s linear infinite' }} />
                      <span>Geocoding Stops & Creating...</span>
                    </>
                  ) : (
                    <>
                      <span>✨</span>
                      <span>Geocode & Deploy Route</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          )}

          {/* ════════ TAB 3: FLEET & ROUTE MANAGER ════════ */}
          {activeTab === 'manage' && (
            <div className="existing-routes-grid">
              {routes.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--text-muted)' }}>
                  No routes configured. Use the "Route Discovery" tab to search and add a route!
                </div>
              ) : (
                routes.map((route) => {
                  const isExpanded = expandedRouteId === route.id;
                  const isLoading = actionLoading[route.id];
                  const isAddingStop = actionLoading[`stop_${route.id}`];

                  return (
                    <div
                      key={route.id}
                      className="existing-route-card"
                      style={{ '--route-color': route.color || '#3B82F6' }}
                    >
                      <div className="existing-route-top">
                        <div>
                          <div className="existing-route-title">
                            <span style={{ width: 12, height: 12, borderRadius: '50%', background: route.color || '#3B82F6', display: 'inline-block', boxShadow: `0 0 8px ${route.color || '#3B82F6'}` }} />
                            <span>{route.name}</span>
                            <span style={{ fontSize: '0.72rem', padding: '2px 8px', borderRadius: 'var(--radius-full)', background: 'rgba(255, 255, 255, 0.08)', color: 'var(--text-secondary)' }}>
                              {route.id}
                            </span>
                          </div>
                          <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginTop: 4 }}>
                            {route.stops?.length || 0} stops configured
                          </div>
                        </div>

                        <div className="existing-route-actions">
                          {changeBusRouteMode && onAssignBusToRoute && (
                            <button
                              className="btn-assign-bus"
                              onClick={() => {
                                onAssignBusToRoute(route.id);
                                onClose();
                              }}
                              title={`Assign your ESP32 bus to ${route.name}`}
                              id={`assign-bus-${route.id}`}
                            >
                              🚌 Assign My Bus
                            </button>
                          )}
                          {onFocusRoute && (
                            <button
                              className="btn-secondary"
                              onClick={() => {
                                onFocusRoute(route);
                                onClose();
                              }}
                              title="Fly to Route on Map"
                            >
                              📍 View on Map
                            </button>
                          )}
                          <button
                            className="btn-secondary"
                            onClick={() => setExpandedRouteId(isExpanded ? null : route.id)}
                          >
                            {isExpanded ? 'Hide Stops' : 'Stops & Waypoints'}
                          </button>
                          <button
                            className="btn-danger"
                            disabled={isLoading}
                            onClick={() => handleDeleteRoute(route.id, route.name)}
                          >
                            {isLoading ? '...' : '🗑️ Delete'}
                          </button>
                        </div>
                      </div>

                      {/* Expanded Stops Accordion */}
                      {isExpanded && (
                        <div style={{ marginTop: 8, padding: 12, background: 'rgba(0, 0, 0, 0.25)', borderRadius: 'var(--radius-sm)' }}>
                          <div style={{ fontSize: '0.76rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 8 }}>
                            Ordered Stops & Coordinates:
                          </div>

                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 12 }}>
                            {route.stops?.map((stop, sIdx) => (
                              <div
                                key={stop.id || sIdx}
                                className="stop-pill"
                                title={`Lat: ${stop.latitude?.toFixed(4)}, Lon: ${stop.longitude?.toFixed(4)}`}
                              >
                                <span style={{ color: route.color || 'var(--primary)' }}>#{stop.stop_order || sIdx + 1}</span>
                                <span>{stop.name}</span>
                              </div>
                            ))}
                          </div>

                          {/* Add Intermediate Stop inline */}
                          <div className="add-stop-inline">
                            <input
                              type="text"
                              className="add-stop-input"
                              placeholder="Add intermediate town / stop via Google Geocoding (e.g. Kadawatha)..."
                              value={inlineNewStop[route.id] || ''}
                              onChange={(e) => {
                                const val = e.target.value;
                                setInlineNewStop(prev => ({ ...prev, [route.id]: val }));
                              }}
                              onKeyDown={(e) => {
                                if (e.key === 'Enter') {
                                  e.preventDefault();
                                  handleAddStopToRoute(route.id);
                                }
                              }}
                            />
                            <button
                              type="button"
                              className="btn-primary"
                              style={{ padding: '6px 14px', fontSize: '0.8rem' }}
                              disabled={isAddingStop || !inlineNewStop[route.id]}
                              onClick={() => handleAddStopToRoute(route.id)}
                            >
                              {isAddingStop ? 'Geocoding...' : '➕ Add Stop'}
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
