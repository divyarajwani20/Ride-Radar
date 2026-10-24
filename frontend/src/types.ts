// ─── Types mirroring backend Pydantic schemas ────────────────────

export interface DriverDetail {
  id: string;
  display_name: string;
  rating_mean: number;
  rating_count: number;
  adjusted_rating: number;
  verified_driver_cancel_count: number;
  eligible_ride_count: number;
  smoothed_driver_cancel_rate: number;
  vehicle_model?: string;
  vehicle_number?: string;
  confidence_label: string;
  is_demo: boolean;
}

export interface ScoreBreakdown {
  rating: number;
  reliability: number;
  eta: number;
  fare: number;
  freshness: number;
  active_weights: Record<string, number>;
}

export interface RideOption {
  id: string;
  provider: string;
  provider_id: string;
  ride_type: string;
  estimated_fare: number | null;
  currency: string;
  pickup_eta_minutes: number | null;
  availability_status: string;
  driver: DriverDetail | null;
  score: number;
  score_breakdown: ScoreBreakdown;
  ranking_explanation: string;
  source_type: string;
  observed_at: string;
  confidence: string;
  is_demo: boolean;
  booking_action_url?: string;
  direct_booking_supported: boolean;
}

export interface RideCompareResponse {
  options: RideOption[];
  summary: {
    best_rated_driver: number | null;
    lowest_estimated_fare: number | null;
    fastest_pickup_eta: number | null;
    total_options: number;
    sort_applied: string;
  };
  origin_zone: { id: string; name: string; lat: number; lng: number; is_priority: boolean };
  destination_zone: { id: string; name: string; lat: number; lng: number; is_priority: boolean };
  providers_checked: number;
  demo_notice: string;
  is_demo: boolean;
  generated_at: string;
}

export interface HotZoneMetric {
  zone_id: string;
  city: string;
  zone_name: string;
  cell_id: string;
  center_lat: number;
  center_lng: number;
  radius_meters: number;
  is_priority_designated: boolean;
  priority_category: string | null;
  description: string | null;
  available_ride_count: number;
  demand_estimate: number | null;
  eligible_request_count: number;
  completed_count: number;
  driver_cancel_count: number;
  passenger_cancel_count: number;
  provider_cancel_count: number;
  driver_cancel_rate: number | null;
  passenger_cancel_rate: number | null;
  provider_cancel_rate: number | null;
  demand_to_availability_ratio: number | null;
  zone_score: number;
  tags: string[];
  confidence: string;
  data_freshness_seconds: number;
  source_type: string;
  is_demo: boolean;
  time_window_label: string;
}

export interface HotZonesResponse {
  zones: HotZoneMetric[];
  time_window: string;
  selected_metric: string;
  city: string;
  data_freshness: string;
  demo_notice: string;
  timestamp: string;
}

export interface TimeSeriesPoint {
  timestamp: string;
  available_rides: number;
  driver_cancels: number;
  passenger_cancels: number;
  demand: number | null;
  zone_score: number;
}

export interface ZoneDetailResponse {
  zone: HotZoneMetric;
  time_series: TimeSeriesPoint[];
  provider_breakdown: {
    provider_name: string;
    provider_id: string;
    status: string;
    estimated_available_cabs: number;
    avg_pickup_eta: number;
  }[];
  active_scenario: string;
  demo_notice: string;
}

export interface InsightsSummary {
  city: string;
  time_window: string;
  total_observed_rides: number;
  total_eligible_requests: number;
  total_driver_cancels: number;
  total_passenger_cancels: number;
  total_provider_cancels: number;
  avg_driver_cancel_rate: number | null;
  avg_passenger_cancel_rate: number | null;
  top_cancellation_hotspots: string[];
  top_availability_zones: string[];
  data_freshness_label: string;
  provenance: Record<string, string>;
  is_demo: boolean;
}

export interface DemoScenario {
  id: string;
  name: string;
  description: string;
  expected_outcome: string;
  category: string;
}

export interface PriorityQuoteResponse {
  request_id: string;
  pickup_zone_name: string;
  is_designated_priority_zone: boolean;
  priority_category: string | null;
  eligibility_explanation: string;
  base_estimate: number;
  priority_fee: number;
  total_payable: number;
  max_acceptable_fare: number;
  currency: string;
  estimated_pickup_range_min: number;
  estimated_pickup_range_max: number;
  commitment_type: string;
  refund_terms: string;
  policy_version: string;
  expires_at: string;
  is_demo: boolean;
}

export interface CandidateMatchExplain {
  driver_id: string;
  driver_name: string;
  score: number;
  eta_minutes: number;
  distance_km: number;
  reliability_rate: number;
  vehicle: string;
  ranking_reason: string;
}

export interface PriorityStatusResponse {
  request_id: string;
  status: string;
  urgency_category: string;
  pickup_zone: string;
  destination_zone: string;
  base_fare: number;
  priority_fee: number;
  total_fare: number;
  refund_status: string;
  current_attempt: number;
  max_attempts: number;
  confirmed_driver: DriverDetail | null;
  candidate_ranking: CandidateMatchExplain[];
  attempt_history: {
    attempt_number: number;
    driver_name: string;
    outcome: string;
    failure_reason: string | null;
    offered_at: string;
    responded_at: string | null;
  }[];
  recovery_events: {
    event_type: string;
    from_status: string;
    to_status: string;
    reason: string;
    timestamp: string;
  }[];
  mobility_alternatives: {
    type: string;
    name: string;
    details: string;
  }[];
  status_timeline_step: number;
  message: string;
  is_demo: boolean;
  updated_at: string;
}

export interface PriorityZone {
  id: number;
  zone_id: string;
  zone_name: string;
  category: string;
  is_enabled: boolean;
  center_lat: number;
  center_lng: number;
  verification_source: string;
  coverage_notes: string;
}

export interface ProviderOut {
  id: string;
  name: string;
  status: string;
  integration_type: string;
  last_synced_at: string | null;
  status_message: string;
  app_url: string | null;
  is_demo: boolean;
}
