import datetime
import random
from sqlalchemy.orm import Session
from app.db.session import engine, Base, SessionLocal
from app.models.models import (
    Provider, Driver, DriverReview, Zone, RideOption, RideEvent,
    ZoneMetricSnapshot, PriorityZone, ReserveCapacity, DemandForecast
)
from app.services.demo_data import (
    JAIPUR_ZONES_SEED, PROVIDERS_SEED, DRIVERS_SEED, DEMO_SCENARIOS
)

def init_db(db: Session = None):
    """Initializes tables and seeds initial data."""
    Base.metadata.create_all(bind=engine)
    close_after = False
    if db is None:
        db = SessionLocal()
        close_after = True

    try:
        # 1. Seed Zones
        for z_data in JAIPUR_ZONES_SEED:
            existing = db.query(Zone).filter(Zone.id == z_data["id"]).first()
            if not existing:
                zone = Zone(**z_data)
                db.add(zone)
                
                # If priority designated, add PriorityZone record
                if z_data.get("is_priority_designated"):
                    pz = PriorityZone(
                        id=f"pz_{z_data['id']}",
                        zone_id=z_data["id"],
                        category=z_data["priority_category"],
                        is_enabled=True,
                        verification_source="Jaipur Municipal Transport Registry",
                        coverage_notes="Verified designated emergency transit zone with continuous monitoring."
                    )
                    db.add(pz)

        # 2. Seed Providers
        for p_data in PROVIDERS_SEED:
            existing = db.query(Provider).filter(Provider.id == p_data["id"]).first()
            if not existing:
                provider = Provider(**p_data)
                db.add(provider)

        # 3. Seed Drivers
        for d_data in DRIVERS_SEED:
            existing = db.query(Driver).filter(Driver.id == d_data["id"]).first()
            if not existing:
                driver = Driver(**d_data)
                db.add(driver)

        db.commit()

        # 4. Seed Zone Metric Snapshots for realistic Hot Zones (now, last_15_mins, last_hour, today)
        seed_zone_snapshots(db)

        # 5. Seed Reserve Fleet Capacity
        seed_reserve_capacity(db)

        # 6. Seed Sample Ride Options for Cross-Provider Comparison
        seed_ride_options(db)

        db.commit()
    finally:
        if close_after:
            db.close()

def seed_zone_snapshots(db: Session):
    """Seeds deterministic zone snapshots with varied availability and cancellation patterns."""
    zones = db.query(Zone).all()
    now = datetime.datetime.utcnow()

    # Clear existing demo snapshots
    db.query(ZoneMetricSnapshot).delete()

    for idx, z in enumerate(zones):
        # Configure distinctive hot zone patterns for each Jaipur zone
        if z.id == "zone_sms_hospital":
            # High availability, high demand, moderate cancellations
            avail, eligible, driver_cancels, pass_cancels, demand = 24, 60, 4, 3, 52
        elif z.id == "zone_jaipur_junction":
            # Cancellation hotspot! High demand, high driver cancels due to station traffic
            avail, eligible, driver_cancels, pass_cancels, demand = 16, 75, 15, 9, 68
        elif z.id == "zone_airport":
            # High availability, low cancellations, premium demand
            avail, eligible, driver_cancels, pass_cancels, demand = 28, 45, 2, 1, 38
        elif z.id == "zone_malviya_nagar":
            # High demand pressure, moderate availability
            avail, eligible, driver_cancels, pass_cancels, demand = 14, 50, 7, 6, 42
        elif z.id == "zone_sitapura":
            # Low availability, low sample size (tests 'Insufficient data' & 'Low confidence')
            avail, eligible, driver_cancels, pass_cancels, demand = 2, 4, 1, 0, 8
        elif z.id == "zone_c_scheme":
            # Balanced central zone
            avail, eligible, driver_cancels, pass_cancels, demand = 22, 55, 3, 4, 45
        else:
            avail, eligible, driver_cancels, pass_cancels, demand = 15, 35, 3, 2, 28

        snapshot = ZoneMetricSnapshot(
            zone_id=z.id,
            window_start=now - datetime.timedelta(hours=1),
            window_end=now,
            available_ride_count=avail,
            eligible_request_count=eligible,
            driver_cancel_count=driver_cancels,
            passenger_cancel_count=pass_cancels,
            provider_cancel_count=1 if eligible > 30 else 0,
            completed_count=eligible - driver_cancels - pass_cancels,
            demand_estimate=demand,
            data_freshness_seconds=45 + (idx * 30),
            confidence="high" if eligible > 30 else "medium",
            source_type="demo"
        )
        db.add(snapshot)

def seed_reserve_capacity(db: Session):
    """Seeds reserve fleet vehicles near high-priority zones."""
    db.query(ReserveCapacity).delete()
    reserves = [
        ("zone_sms_hospital", "Jaipur QuickResponse Transit Fleet", "Sedan Prime", 6),
        ("zone_jaipur_junction", "Rajasthan Rapid Mobility Reserve", "Sedan Prime", 5),
        ("zone_airport", "Airport Dedicated Transit Reserve", "SUV / Prime", 8),
        ("zone_apex_hospital", "Malviya Emergency Transit Unit", "Economy / Hatchback", 4),
    ]
    for zone_id, source, category, count in reserves:
        rc = ReserveCapacity(
            zone_id=zone_id,
            fleet_or_demo_source=source,
            vehicle_category=category,
            available_count=count,
            coverage_start="00:00",
            coverage_end="23:59",
            is_demo=True,
            updated_at=datetime.datetime.utcnow()
        )
        db.add(rc)

def seed_ride_options(db: Session):
    """Seeds representative ride options across Uber, Ola, Rapido, and QuickRide."""
    db.query(RideOption).delete()
    now = datetime.datetime.utcnow()
    
    options = [
        # Option 1: Uber Premier with Top Veteran Driver (Driver 01)
        {
            "id": "opt_uber_premier_01",
            "provider_id": "uber",
            "ride_type": "sedan",
            "origin_zone_id": "zone_sms_hospital",
            "destination_zone_id": "zone_c_scheme",
            "estimated_fare": 210.0,
            "currency": "INR",
            "pickup_eta_minutes": 4,
            "availability_status": "available",
            "driver_id": "driver_01_veteran",
            "observed_at": now - datetime.timedelta(minutes=2),
            "source_type": "demo",
            "confidence": "high",
            "is_demo": True
        },
        # Option 2: Ola Prime with High Raw Rating Driver but Low Review Count (Driver 02 - Bayesian shrinkage showcase!)
        {
            "id": "opt_ola_prime_02",
            "provider_id": "ola",
            "ride_type": "sedan",
            "origin_zone_id": "zone_sms_hospital",
            "destination_zone_id": "zone_c_scheme",
            "estimated_fare": 195.0,
            "currency": "INR",
            "pickup_eta_minutes": 5,
            "availability_status": "available",
            "driver_id": "driver_02_perfect_new",
            "observed_at": now - datetime.timedelta(minutes=4),
            "source_type": "demo",
            "confidence": "low",
            "is_demo": True
        },
        # Option 3: QuickRide EV (Lowest fare, steady driver)
        {
            "id": "opt_quickride_ev_03",
            "provider_id": "quickride",
            "ride_type": "economy",
            "origin_zone_id": "zone_sms_hospital",
            "destination_zone_id": "zone_c_scheme",
            "estimated_fare": 160.0,
            "currency": "INR",
            "pickup_eta_minutes": 7,
            "availability_status": "available",
            "driver_id": "driver_03_steady",
            "observed_at": now - datetime.timedelta(minutes=1),
            "source_type": "demo",
            "confidence": "medium",
            "is_demo": True
        },
        # Option 4: Rapido Auto (Fastest pickup in traffic, but higher cancellation history)
        {
            "id": "opt_rapido_auto_04",
            "provider_id": "rapido",
            "ride_type": "auto",
            "origin_zone_id": "zone_sms_hospital",
            "destination_zone_id": "zone_c_scheme",
            "estimated_fare": 115.0,
            "currency": "INR",
            "pickup_eta_minutes": 2,
            "availability_status": "available",
            "driver_id": "driver_04_high_cancel",
            "observed_at": now - datetime.timedelta(minutes=3),
            "source_type": "demo",
            "confidence": "medium",
            "is_demo": True
        },
        # Option 5: Uber Go with unrated driver (Driver 05)
        {
            "id": "opt_uber_go_05",
            "provider_id": "uber",
            "ride_type": "economy",
            "origin_zone_id": "zone_sms_hospital",
            "destination_zone_id": "zone_c_scheme",
            "estimated_fare": 175.0,
            "currency": "INR",
            "pickup_eta_minutes": 6,
            "availability_status": "available",
            "driver_id": "driver_05_unrated",
            "observed_at": now - datetime.timedelta(minutes=8),
            "source_type": "demo",
            "confidence": "low",
            "is_demo": True
        }
    ]

    for opt_data in options:
        opt = RideOption(**opt_data)
        db.add(opt)

def reset_to_scenario(scenario_id: str, db: Session = None):
    """
    Deterministically resets the database state for the selected demo scenario (Section 31).
    """
    close_after = False
    if db is None:
        db = SessionLocal()
        close_after = True

    try:
        # Re-initialize baseline tables and seed
        init_db(db)
        
        # Apply specific scenario overrides
        now = datetime.datetime.utcnow()
        if scenario_id == "scenario_7_no_reliable_history":
            # Ensure unrated driver is the primary candidate
            d = db.query(Driver).filter(Driver.id == "driver_05_unrated").first()
            if d:
                d.is_available = True
                d.current_zone_id = "zone_sms_hospital"
        elif scenario_id == "scenario_8_stale_availability":
            # Set observation time to 45 mins ago
            opt = db.query(RideOption).filter(RideOption.id == "opt_uber_premier_01").first()
            if opt:
                opt.observed_at = now - datetime.timedelta(minutes=48)
        elif scenario_id == "scenario_11_demand_spike":
            # Increase demand to 2.5x in Malviya Nagar
            snap = db.query(ZoneMetricSnapshot).filter(ZoneMetricSnapshot.zone_id == "zone_malviya_nagar").first()
            if snap:
                snap.demand_estimate = 65
                snap.available_ride_count = 10
        elif scenario_id == "scenario_12_provider_not_connected":
            # Set Rapido to not_connected
            p = db.query(Provider).filter(Provider.id == "rapido").first()
            if p:
                p.status = "not_connected"
                p.status_message = "Rapido API credentials not configured. Open Rapido app directly."

        db.commit()
    finally:
        if close_after:
            db.close()
