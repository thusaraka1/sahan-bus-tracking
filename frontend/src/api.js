/**
 * API service for communicating with the Flask backend.
 */

const API_BASE = 'http://localhost:5000/api';

/**
 * Generic fetch wrapper with error handling.
 */
async function apiFetch(endpoint, options = {}) {
  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    });
    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    console.error(`[API] ${endpoint} failed:`, error);
    throw error;
  }
}

export const api = {
  /** Health check */
  getHealth: () => apiFetch('/health'),

  /** Get all buses with live positions */
  getBuses: () => apiFetch('/buses'),

  /** Get detailed bus info including ETA */
  getBusDetail: (busId) => apiFetch(`/buses/${busId}`),

  /** Get bus location history */
  getBusHistory: (busId, limit = 50) => apiFetch(`/buses/${busId}/history?limit=${limit}`),

  /** Get all routes with stops */
  getRoutes: () => apiFetch('/routes'),

  /** Get stops for a route */
  getRouteStops: (routeId) => apiFetch(`/routes/${routeId}/stops`),

  /** Get ETA predictions for a bus */
  getETA: (busId) => apiFetch(`/eta/${busId}`),

  /** Get system analytics */
  getAnalytics: () => apiFetch('/analytics'),

  /** Get simulator status */
  getSimulatorStatus: () => apiFetch('/simulator/status'),

  /** Get detailed AI model metrics & active learning status */
  getAIMetrics: () => apiFetch('/ai/metrics'),

  /** Get stream of active learning ground truth training events */
  getAIHistory: (limit = 20) => apiFetch(`/ai/history?limit=${limit}`),

  /** Start the bus simulator */
  startSimulator: () => apiFetch('/simulator/start', { method: 'POST' }),

  /** Stop the bus simulator */
  stopSimulator: () => apiFetch('/simulator/stop', { method: 'POST' }),

  /** Search routes directly by route number (e.g. 04, 138, 177) or name */
  lookupRoutes: (query = '') => apiFetch(`/routes/lookup?q=${encodeURIComponent(query)}`),

  /** Search for bus routes via Google Maps Directions API (transit mode) */
  searchRoute: (origin, destination) =>
    apiFetch('/routes/search', {
      method: 'POST',
      body: JSON.stringify({ origin, destination }),
    }),

  /** Add a new route (from Google search results or manual) */
  addRoute: (routeData) =>
    apiFetch('/routes/add', {
      method: 'POST',
      body: JSON.stringify(routeData),
    }),

  /** Delete a route */
  deleteRoute: (routeId) =>
    apiFetch(`/routes/${routeId}`, { method: 'DELETE' }),

  /** Change a bus's assigned route */
  changeBusRoute: (busId, routeId) =>
    apiFetch(`/buses/${busId}/route`, {
      method: 'PUT',
      body: JSON.stringify({ route_id: routeId }),
    }),

  /** Add intermediate stops to an existing route via geocoding */
  addStopsToRoute: (routeId, stopNames) =>
    apiFetch(`/routes/${routeId}/add-stops`, {
      method: 'POST',
      body: JSON.stringify({ stops: stopNames }),
    }),

  /** Geocode a place name */
  geocode: (query) => apiFetch(`/geocode?q=${encodeURIComponent(query)}`),
};

export default api;
