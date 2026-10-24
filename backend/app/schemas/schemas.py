from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

# Health
class HealthResponse(BaseModel):
    status: str
    demo_mode: bool
    version: str
    city: str
    active_scenario: str
    timestamp: datetime

# Provider
class ProviderOut(BaseModel):
    id: str
    name: str
    status: str  # connected, demo, not_connected, error
    integration_type: str
    last_synced_at: Optional[datetime]
    status_message: str
    app_url: Optional[str] = None
    is_demo: bool = True

class DataSourceSettingsOut(BaseModel):
    providers: List[ProviderOut]
    demo_mode: bool
    data_retention_policy: str
    privacy_notice: str
    credential_status: Dict[str, str]

# Driver & Ranking
class DriverDetail(BaseModel):
    id: str
    display_name: str
    rating_mean: float
    rating_count: int
    adjusted_rating: float
    verified_driver_cancel_count: int
    eligible_ride_count: int
    smoothed_driver_cancel_rate: float
    vehicle_model: Optional[str] = None
    vehicle_number: Optional[str] = None
    confidence_label: str  # "High confidence", "Limited rating history", "No verified history"
    is_demo: bool = True

class ScoreBreakdown(BaseModel):
    rating: float = Field(..., description="Normalized rating score (0-100)")
    reliability: float = Field(..., description="Normalized reliability score (0-100)")
    eta: float = Field(..., description="Normalized pickup ETA score (0-100)")
    fare: float = Field(..., description="Normalized fare score (0-100)")
    freshness: float = Field(..., description="Normalized data freshness score (0-100)")
    active_weights: Dict[str, float] = Field(..., description="Renormalized weights applied")

class RideOptionOut(BaseModel):
    id: str
    provider: str
    provider_id: str
    ride_type: str
    estimated_fare: Optional[float]
    currency: str = "INR"
    pickup_eta_minutes: Optional[int]
    availability_status: str
    driver: Optional[DriverDetail]
    score: float
    score_breakdown: ScoreBreakdown
    ranking_explanation: str
    source_type: str  # official_api, user_observation, demo
    observed_at: datetime
    confidence: str  # high, medium, low
    is_demo: bool = True
    booking_action_url: Optional[str] = None
    direct_booking_supported: bool = False

class RideCompareRequest(BaseModel):
    origin: str  # zone_id or location string
    destination: str
    departure_time: Optional[datetime] = None
    ride_category: Optional[str] = "all"  # all, bike, auto, economy, sedan, suv
    passenger_count: Optional[int] = 1
    sort_by: Optional[str] = "best_overall"  # best_overall, best_driver_rating, lowest_fare, fastest_pickup

class RideCompareResponse(BaseModel):
    options: List[RideOptionOut]
    summary: Dict[str, Any]
    origin_zone: Dict[str, Any]
    destination_zone: Dict[str, Any]
    providers_checked: int
    demo_notice: str
    is_demo: bool = True
    generated_at: datetime

# Hot Zones
class HotZoneMetricOut(BaseModel):
    zone_id: str
    city: str
    zone_name: str
    cell_id: str
    center_lat: float
    center_lng: float
    radius_meters: float
    is_priority_designated: bool
    priority_category: Optional[str]
    description: Optional[str]
    
    # Calculated Metrics
    available_ride_count: int
    demand_estimate: Optional[int]
    eligible_request_count: int
    completed_count: int
    driver_cancel_count: int
    passenger_cancel_count: int
    provider_cancel_count: int
    
    driver_cancel_rate: Optional[float]  # None if zero denominator
    passenger_cancel_rate: Optional[float]
    provider_cancel_rate: Optional[float]
    demand_to_availability_ratio: Optional[float]
    
    zone_score: float
    tags: List[str]
    confidence: str  # high, medium, low, insufficient_data
    data_freshness_seconds: int
    source_type: str
    is_demo: bool = True
    time_window_label: str

class HotZonesResponse(BaseModel):
    zones: List[HotZoneMetricOut]
    time_window: str
    selected_metric: str
    city: str
    data_freshness: str
    demo_notice: str
    timestamp: datetime

class TimeSeriesPoint(BaseModel):
    timestamp: str
    available_rides: int
    driver_cancels: int
    passenger_cancels: int
    demand: Optional[int]
    zone_score: float

class ZoneDetailResponse(BaseModel):
    zone: HotZoneMetricOut
    time_series: List[TimeSeriesPoint]
    provider_breakdown: List[Dict[str, Any]]
    active_scenario: str
    demo_notice: str

# Insights
class InsightsSummaryResponse(BaseModel):
    city: str
    time_window: str
    total_observed_rides: int
    total_eligible_requests: int
    total_driver_cancels: int
    total_passenger_cancels: int
    total_provider_cancels: int
    avg_driver_cancel_rate: Optional[float]
    avg_passenger_cancel_rate: Optional[float]
    top_cancellation_hotspots: List[str]
    top_availability_zones: List[str]
    data_freshness_label: str
    provenance: Dict[str, str]
    is_demo: bool = True

# Emergency Priority & Recovery
class PriorityQuoteRequest(BaseModel):
    pickup_zone_id: str
    destination_zone_id: str
    urgency_category: Optional[str] = "medical"  # medical, transit_connection, urgent_meeting, general_priority
    max_acceptable_fare: Optional[float] = 350.0
    passenger_notes: Optional[str] = None

class PriorityQuoteResponse(BaseModel):
    request_id: str
    pickup_zone_name: str
    is_designated_priority_zone: bool
    priority_category: Optional[str]
    eligibility_explanation: str
    base_estimate: float
    priority_fee: float
    total_payable: float
    max_acceptable_fare: float
    currency: str = "INR"
    estimated_pickup_range_min: int
    estimated_pickup_range_max: int
    commitment_type: str  # priority_dispatch, conditional_ride_commitment
    refund_terms: str
    policy_version: str
    expires_at: datetime
    is_demo: bool = True

class PriorityDispatchRequest(BaseModel):
    request_id: str
    idempotency_key: str
    accept_terms: bool = True
    simulate_outcome: Optional[str] = None  # None (use scenario), "force_success", "force_decline", "force_timeout", "force_cancel_after_accept", "force_all_fail"

class CandidateMatchExplain(BaseModel):
    driver_id: str
    driver_name: str
    score: float
    eta_minutes: int
    distance_km: float
    reliability_rate: float
    vehicle: str
    ranking_reason: str

class PriorityStatusResponse(BaseModel):
    request_id: str
    status: str
    urgency_category: str
    pickup_zone: str
    destination_zone: str
    base_fare: float
    priority_fee: float
    total_fare: float
    refund_status: str
    current_attempt: int
    max_attempts: int
    confirmed_driver: Optional[DriverDetail] = None
    candidate_ranking: List[CandidateMatchExplain] = []
    attempt_history: List[Dict[str, Any]] = []
    recovery_events: List[Dict[str, Any]] = []
    mobility_alternatives: List[Dict[str, Any]] = []
    status_timeline_step: int  # 0 to 5 for UI timeline
    message: str
    is_demo: bool = True
    updated_at: datetime

# Reliability & Risk
class ReliabilityRiskResponse(BaseModel):
    zone_id: str
    zone_name: str
    risk_score: float  # 0 to 100
    risk_level: str  # Low, Moderate, High, Insufficient data
    confidence: str
    sample_size: int
    time_window: str
    reasons: List[str]
    model_version: str
    observed_at: datetime
    source_type: str
    is_demo: bool = True

# Forecasting
class DemandForecastResponse(BaseModel):
    city: str
    horizon_minutes: int
    forecasts: List[Dict[str, Any]]
    demand_shocks: List[Dict[str, Any]]
    confidence: str
    source_type: str
    is_demo: bool = True
    generated_at: datetime

# Observations
class ObservationCreate(BaseModel):
    provider_id: str
    zone_id: str
    event_type: str
    cancellation_actor: Optional[str] = None
    optional_fare: Optional[float] = None
    optional_eta: Optional[int] = None
    consent_recorded: bool = True

class ObservationOut(BaseModel):
    id: int
    provider_id: str
    zone_id: str
    event_type: str
    cancellation_actor: Optional[str]
    observed_at: datetime
    validation_status: str
    is_demo: bool = True

# Demo Scenarios
class DemoScenarioOut(BaseModel):
    id: str
    name: str
    description: str
    expected_outcome: str
    category: str

class DemoScenarioActivateResponse(BaseModel):
    scenario_id: str
    name: str
    message: str
    active: bool
