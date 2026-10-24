import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Index
)
from sqlalchemy.orm import relationship
from app.db.session import Base

class Provider(Base):
    __tablename__ = "providers"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    status = Column(String, default="demo")  # connected, demo, not_connected, error
    integration_type = Column(String, default="simulated")  # official_oauth, api_key, simulated
    last_synced_at = Column(DateTime, default=datetime.datetime.utcnow)
    status_message = Column(String, default="")
    app_url = Column(String, default="")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    drivers = relationship("Driver", back_populates="provider", cascade="all, delete-orphan")
    ride_options = relationship("RideOption", back_populates="provider")


class Driver(Base):
    __tablename__ = "drivers"
    
    id = Column(String, primary_key=True, index=True)
    provider_id = Column(String, ForeignKey("providers.id"), nullable=False, index=True)
    display_name = Column(String, nullable=False)  # fictional demo label
    rating_mean = Column(Float, default=4.5)
    rating_count = Column(Integer, default=50)
    verified_driver_cancel_count = Column(Integer, default=2)
    eligible_ride_count = Column(Integer, default=100)
    vehicle_model = Column(String, default="Sedan Prime")
    vehicle_number = Column(String, default="RJ-14-EA-1024")
    current_lat = Column(Float, nullable=True)
    current_lng = Column(Float, nullable=True)
    current_zone_id = Column(String, nullable=True, index=True)
    is_available = Column(Boolean, default=True)
    last_updated_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_demo = Column(Boolean, default=True)
    
    provider = relationship("Provider", back_populates="drivers")
    reviews = relationship("DriverReview", back_populates="driver", cascade="all, delete-orphan")


class DriverReview(Base):
    __tablename__ = "driver_reviews"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    driver_id = Column(String, ForeignKey("drivers.id"), nullable=False, index=True)
    rating = Column(Float, nullable=False)
    review_text = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    verification_status = Column(String, default="verified")  # verified, unverified, moderated
    is_demo = Column(Boolean, default=True)
    
    driver = relationship("Driver", back_populates="reviews")


class Zone(Base):
    __tablename__ = "zones"
    
    id = Column(String, primary_key=True, index=True)
    city = Column(String, nullable=False, index=True)
    zone_name = Column(String, nullable=False)
    cell_id = Column(String, nullable=False, unique=True, index=True)
    center_lat = Column(Float, nullable=False)
    center_lng = Column(Float, nullable=False)
    radius_meters = Column(Float, default=1500)
    is_priority_designated = Column(Boolean, default=False)
    priority_category = Column(String, nullable=True)  # hospital, railway_station, airport, transit_hub
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    snapshots = relationship("ZoneMetricSnapshot", back_populates="zone")
    priority_zone = relationship("PriorityZone", back_populates="zone", uselist=False)


class RideOption(Base):
    __tablename__ = "ride_options"
    
    id = Column(String, primary_key=True, index=True)
    provider_id = Column(String, ForeignKey("providers.id"), nullable=False, index=True)
    ride_type = Column(String, nullable=False)  # bike, auto, economy, sedan, suv, priority
    origin_zone_id = Column(String, ForeignKey("zones.id"), nullable=False, index=True)
    destination_zone_id = Column(String, ForeignKey("zones.id"), nullable=False, index=True)
    estimated_fare = Column(Float, nullable=True)
    currency = Column(String, default="INR")
    pickup_eta_minutes = Column(Integer, nullable=True)
    availability_status = Column(String, default="available")  # available, limited, surge, unavailable
    driver_id = Column(String, ForeignKey("drivers.id"), nullable=True, index=True)
    observed_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    source_type = Column(String, default="demo")  # official_api, user_observation, demo
    confidence = Column(String, default="medium")  # high, medium, low
    is_demo = Column(Boolean, default=True)
    
    provider = relationship("Provider", back_populates="ride_options")
    driver = relationship("Driver")


class RideEvent(Base):
    __tablename__ = "ride_events"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    provider_id = Column(String, ForeignKey("providers.id"), nullable=True, index=True)
    zone_id = Column(String, ForeignKey("zones.id"), nullable=False, index=True)
    event_type = Column(String, nullable=False, index=True)  # request, available, accepted, completed, cancelled, timed_out, declined
    cancellation_actor = Column(String, nullable=True)  # driver, passenger, provider, unknown
    occurred_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    source_type = Column(String, default="demo")
    validation_status = Column(String, default="validated")
    is_demo = Column(Boolean, default=True)
    details_json = Column(Text, nullable=True)


class ZoneMetricSnapshot(Base):
    __tablename__ = "zone_metric_snapshots"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    zone_id = Column(String, ForeignKey("zones.id"), nullable=False, index=True)
    window_start = Column(DateTime, nullable=False, index=True)
    window_end = Column(DateTime, nullable=False, index=True)
    available_ride_count = Column(Integer, default=0)
    eligible_request_count = Column(Integer, default=0)
    driver_cancel_count = Column(Integer, default=0)
    passenger_cancel_count = Column(Integer, default=0)
    provider_cancel_count = Column(Integer, default=0)
    completed_count = Column(Integer, default=0)
    demand_estimate = Column(Integer, nullable=True)
    data_freshness_seconds = Column(Integer, default=60)
    confidence = Column(String, default="medium")
    source_type = Column(String, default="demo")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    zone = relationship("Zone", back_populates="snapshots")


class UserObservation(Base):
    __tablename__ = "user_observations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    provider_id = Column(String, ForeignKey("providers.id"), nullable=False)
    zone_id = Column(String, ForeignKey("zones.id"), nullable=False)
    event_type = Column(String, nullable=False)
    cancellation_actor = Column(String, nullable=True)
    observed_at = Column(DateTime, default=datetime.datetime.utcnow)
    optional_fare = Column(Float, nullable=True)
    optional_eta = Column(Integer, nullable=True)
    validation_status = Column(String, default="pending")
    consent_recorded = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


# Priority & Reliability Additions (Section 24)

class PriorityZone(Base):
    __tablename__ = "priority_zones"
    
    id = Column(String, primary_key=True, index=True)
    zone_id = Column(String, ForeignKey("zones.id"), nullable=False, unique=True, index=True)
    category = Column(String, nullable=False)  # hospital, railway_station, airport, transit_hub
    is_enabled = Column(Boolean, default=True)
    verification_source = Column(String, default="Jaipur Municipal & Transport Authority Directory")
    coverage_notes = Column(String, default="")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    zone = relationship("Zone", back_populates="priority_zone")


class PriorityRequest(Base):
    __tablename__ = "priority_requests"
    
    id = Column(String, primary_key=True, index=True)  # request_id uuid
    passenger_id = Column(String, default="guest_passenger")
    pickup_zone_id = Column(String, ForeignKey("zones.id"), nullable=False, index=True)
    destination_zone_id = Column(String, ForeignKey("zones.id"), nullable=False, index=True)
    urgency_category = Column(String, default="medical")  # medical, transit_connection, urgent_meeting, general_priority
    priority_fee = Column(Float, default=50.0)
    base_fare = Column(Float, default=180.0)
    max_total_fare = Column(Float, default=300.0)
    commitment_type = Column(String, default="priority_dispatch")  # priority_dispatch, conditional_ride_commitment
    policy_version = Column(String, default="v1.0")
    status = Column(String, default="searching", index=True)
    # Statuses: draft, quoted, searching, driver_offered, driver_accepted, driver_arriving, completed, retrying, alternative_search, fallback_offered, unavailable, cancelled, expired
    current_attempt = Column(Integer, default=1)
    max_attempts = Column(Integer, default=3)
    confirmed_driver_id = Column(String, ForeignKey("drivers.id"), nullable=True)
    idempotency_key = Column(String, unique=True, nullable=True, index=True)
    refund_status = Column(String, default="none")  # none, eligible, refunded, voided
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    attempts = relationship("DriverOfferAttempt", back_populates="request", cascade="all, delete-orphan")
    recovery_events = relationship("RideRecoveryEvent", back_populates="request", cascade="all, delete-orphan")


class DriverOfferAttempt(Base):
    __tablename__ = "driver_offer_attempts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(String, ForeignKey("priority_requests.id"), nullable=False, index=True)
    driver_id = Column(String, ForeignKey("drivers.id"), nullable=False)
    attempt_number = Column(Integer, nullable=False)
    offered_at = Column(DateTime, default=datetime.datetime.utcnow)
    response_deadline = Column(DateTime, nullable=False)
    responded_at = Column(DateTime, nullable=True)
    outcome = Column(String, default="pending")  # pending, accepted, declined, timed_out, cancelled_after_accept
    failure_reason = Column(String, nullable=True)
    source_type = Column(String, default="demo")
    
    request = relationship("PriorityRequest", back_populates="attempts")
    driver = relationship("Driver")


class RideRiskAssessment(Base):
    __tablename__ = "ride_risk_assessments"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(String, nullable=True, index=True)
    zone_id = Column(String, ForeignKey("zones.id"), nullable=False, index=True)
    risk_score = Column(Float, nullable=False)  # 0 to 100
    risk_level = Column(String, nullable=False)  # Low, Moderate, High, Insufficient data
    confidence = Column(String, default="medium")  # high, medium, low
    reasons_json = Column(Text, nullable=False)  # List of string reasons
    sample_size = Column(Integer, default=0)
    time_window = Column(String, default="last_hour")
    model_version = Column(String, default="rule_engine_v1.0")
    source_type = Column(String, default="demo")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class RideRecoveryEvent(Base):
    __tablename__ = "ride_recovery_events"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(String, ForeignKey("priority_requests.id"), nullable=False, index=True)
    event_type = Column(String, nullable=False)  # retry_triggered, alternative_search, fallback_offered, refund_processed
    from_status = Column(String, nullable=False)
    to_status = Column(String, nullable=False)
    reason = Column(String, nullable=False)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    request = relationship("PriorityRequest", back_populates="recovery_events")


class FareQuote(Base):
    __tablename__ = "fare_quotes"
    
    id = Column(String, primary_key=True, index=True)
    request_id = Column(String, nullable=True, index=True)
    base_estimate = Column(Float, nullable=False)
    priority_fee = Column(Float, nullable=False)
    maximum_total = Column(Float, nullable=False)
    currency = Column(String, default="INR")
    terms_version = Column(String, default="v1.0")
    refund_terms = Column(String, default="100% priority fee refund if no verified ride is secured within dispatch budget.")
    expires_at = Column(DateTime, nullable=False)
    source_type = Column(String, default="demo")


class DemandForecast(Base):
    __tablename__ = "demand_forecasts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    zone_id = Column(String, ForeignKey("zones.id"), nullable=False, index=True)
    forecast_start = Column(DateTime, nullable=False)
    forecast_end = Column(DateTime, nullable=False)
    horizon_minutes = Column(Integer, default=30)
    predicted_demand = Column(Integer, nullable=False)
    observed_supply = Column(Integer, nullable=False)
    demand_shock_detected = Column(Boolean, default=False)
    confidence = Column(String, default="medium")
    source_type = Column(String, default="demo")
    is_demo = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class ReserveCapacity(Base):
    __tablename__ = "reserve_capacity"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    zone_id = Column(String, ForeignKey("zones.id"), nullable=False, index=True)
    fleet_or_demo_source = Column(String, default="Jaipur QuickResponse Transit Fleet (Demo Reserve)")
    vehicle_category = Column(String, default="Sedan Prime")
    available_count = Column(Integer, default=5)
    coverage_start = Column(String, default="00:00")
    coverage_end = Column(String, default="23:59")
    is_demo = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)


class PickupSuggestion(Base):
    __tablename__ = "pickup_suggestions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(String, nullable=False, index=True)
    original_zone_id = Column(String, ForeignKey("zones.id"), nullable=False)
    suggested_zone_id = Column(String, ForeignKey("zones.id"), nullable=False)
    suggested_name = Column(String, nullable=False)
    walking_distance_m = Column(Integer, nullable=False)
    reason = Column(String, nullable=False)
    source_type = Column(String, default="demo")
    accepted_by_passenger = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
