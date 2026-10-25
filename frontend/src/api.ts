// ─── API Client — all calls go through Vite proxy ─────────────────

import type {
  RideCompareResponse,
  HotZonesResponse,
  ZoneDetailResponse,
  InsightsSummary,
  DemoScenario,
  PriorityQuoteResponse,
  PriorityStatusResponse,
  PriorityZone,
  ProviderOut,
} from './types';

const API_HOST = import.meta.env.VITE_API_BASE_URL || '';
const BASE = `${API_HOST}/api/v1`;

async function apiFetch<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${url}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API ${res.status}: ${body}`);
  }
  return res.json();
}

// ─── Rides ─────────────────────────────────────────────────────────
export function compareRides(
  origin: string,
  destination: string,
  sortBy = 'best_overall',
  rideCategory = 'all'
) {
  return apiFetch<RideCompareResponse>('/rides/compare', {
    method: 'POST',
    body: JSON.stringify({
      origin,
      destination,
      ride_category: rideCategory,
      sort_by: sortBy,
    }),
  });
}

// ─── Hot Zones ─────────────────────────────────────────────────────
export function getHotZones(
  city = 'Jaipur',
  window = 'last_hour',
  metric = 'zone_score'
) {
  return apiFetch<HotZonesResponse>(
    `/hot-zones?city=${city}&window=${window}&metric=${metric}`
  );
}

export function getZoneDetail(zoneId: string, window = 'last_hour') {
  return apiFetch<ZoneDetailResponse>(
    `/hot-zones/${zoneId}?window=${window}`
  );
}

// ─── Insights ──────────────────────────────────────────────────────
export function getInsights(city = 'Jaipur', window = 'last_hour') {
  return apiFetch<InsightsSummary>(
    `/insights/summary?city=${city}&window=${window}`
  );
}

// ─── Demo Scenarios ────────────────────────────────────────────────
export function getDemoScenarios() {
  return apiFetch<DemoScenario[]>('/demo/scenarios');
}

export function activateScenario(scenarioId: string) {
  return apiFetch<{ scenario_id: string; name: string; message: string; active: boolean }>(
    `/demo/scenarios/${scenarioId}/activate`,
    { method: 'POST' }
  );
}

// ─── Priority Dispatch ─────────────────────────────────────────────
export function getPriorityZones() {
  return apiFetch<PriorityZone[]>('/priority/zones');
}

export function requestPriorityQuote(
  pickupZoneId: string,
  destinationZoneId: string,
  urgencyCategory = 'medical'
) {
  return apiFetch<PriorityQuoteResponse>('/priority/requests', {
    method: 'POST',
    body: JSON.stringify({
      pickup_zone_id: pickupZoneId,
      destination_zone_id: destinationZoneId,
      urgency_category: urgencyCategory,
    }),
  });
}

export function dispatchPriority(
  requestId: string,
  idempotencyKey: string,
  simulateOutcome?: string
) {
  return apiFetch<PriorityStatusResponse>(
    `/priority/requests/${requestId}/dispatch`,
    {
      method: 'POST',
      body: JSON.stringify({
        request_id: requestId,
        idempotency_key: idempotencyKey,
        accept_terms: true,
        simulate_outcome: simulateOutcome || null,
      }),
    }
  );
}

export function getPriorityStatus(requestId: string) {
  return apiFetch<PriorityStatusResponse>(
    `/priority/requests/${requestId}/status`
  );
}

// ─── Providers ─────────────────────────────────────────────────────
export function getProviders() {
  return apiFetch<{ providers: ProviderOut[] }>('/providers');
}

// ─── Health ────────────────────────────────────────────────────────
export function getHealth() {
  return apiFetch<{ status: string; demo_mode: boolean; version: string }>(
    '/health'
  );
}
