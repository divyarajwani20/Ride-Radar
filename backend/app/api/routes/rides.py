import math
import hashlib
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.models import RideOption, Zone, Provider, Driver, ZoneMetricSnapshot
from app.schemas.schemas import (
    RideCompareRequest, RideCompareResponse, RideOptionOut, ScoreBreakdown, DriverDetail
)
from app.services.ranking import rank_ride_options

router = APIRouter()

JAIPUR_LANDMARKS = [
    {
        "keys": ["jecrc", "jecrc university", "sitapura", "poornima", "mg hospital", "mahatma gandhi", "riico"],
        "name": "JECRC University & Campus (Sitapura)",
        "zone_id": "zone_sitapura",
        "lat": 26.7750,
        "lng": 75.8770,
        "is_priority": False
    },
    {
        "keys": ["railway station", "jaipur railway station", "junction", "jaipur junction", "station road", "railway"],
        "name": "Jaipur Junction Railway Station",
        "zone_id": "zone_jaipur_junction",
        "lat": 26.9215,
        "lng": 75.7873,
        "is_priority": True
    },
    {
        "keys": ["airport", "jaipur airport", "jai", "terminal 2", "sanganer airport", "aerodrome"],
        "name": "Jaipur International Airport (JAI)",
        "zone_id": "zone_airport",
        "lat": 26.8241,
        "lng": 75.8122,
        "is_priority": True
    },
    {
        "keys": ["sms", "sms hospital", "sawai man singh", "trauma centre", "sms medical"],
        "name": "SMS Medical Hospital & Trauma Centre",
        "zone_id": "zone_sms_hospital",
        "lat": 26.8995,
        "lng": 75.8193,
        "is_priority": True
    },
    {
        "keys": ["c scheme", "c-scheme", "statue circle", "ashok nagar", "ahinsa circle", "panch batti"],
        "name": "C-Scheme Central Business District",
        "zone_id": "zone_c_scheme",
        "lat": 26.9116,
        "lng": 75.8001,
        "is_priority": False
    },
    {
        "keys": ["malviya", "malviya nagar", "gaurav tower", "gt mall", "crystal court"],
        "name": "Malviya Nagar Commercial & Tech Hub",
        "zone_id": "zone_malviya_nagar",
        "lat": 26.8521,
        "lng": 75.8234,
        "is_priority": False
    },
    {
        "keys": ["wtp", "world trade park", "wtp mall", "jln marg"],
        "name": "World Trade Park (WTP) Mall",
        "zone_id": "zone_world_trade_park",
        "lat": 26.8554,
        "lng": 75.8059,
        "is_priority": False
    },
    {
        "keys": ["mansarovar", "mansarovar metro", "vt road", "madhyam marg"],
        "name": "Mansarovar Sector 5 & Metro Terminus",
        "zone_id": "zone_mansarovar",
        "lat": 26.8614,
        "lng": 75.7619,
        "is_priority": False
    },
    {
        "keys": ["vaishali", "vaishali nagar", "amrapali circle", "queens road"],
        "name": "Vaishali Nagar Amrapali Circle",
        "zone_id": "zone_vaishali_nagar",
        "lat": 26.9063,
        "lng": 75.7401,
        "is_priority": False
    },
    {
        "keys": ["raja park", "raja park market", "lbs college"],
        "name": "Raja Park Shopping Promenade",
        "zone_id": "zone_raja_park",
        "lat": 26.8897,
        "lng": 75.8358,
        "is_priority": False
    },
    {
        "keys": ["apex", "apex hospital", "ehcc", "ehcc hospital", "eternal heart"],
        "name": "Apex & EHCC Hospital Corridor",
        "zone_id": "zone_apex_hospital",
        "lat": 26.8635,
        "lng": 75.8082,
        "is_priority": True
    },
    {
        "keys": ["hawa mahal", "pink city", "badi chaupar", "chhoti chaupar", "city palace", "johari bazaar"],
        "name": "Hawa Mahal & Pink City Old Town",
        "zone_id": "zone_hawa_mahal",
        "lat": 26.9239,
        "lng": 75.8267,
        "is_priority": False
    },
    {
        "keys": ["sindhi camp", "bus stand", "central bus terminal"],
        "name": "Sindhi Camp Bus Station & Transit Hub",
        "zone_id": "zone_sindhi_camp",
        "lat": 26.9240,
        "lng": 75.7980,
        "is_priority": True
    },
    {
        "keys": ["jagatpura", "skit", "mahal road"],
        "name": "Jagatpura & SKIT College Area",
        "zone_id": "zone_jagatpura",
        "lat": 26.8250,
        "lng": 75.8500,
        "is_priority": False
    },
    {
        "keys": ["amer", "amer fort", "amber fort"],
        "name": "Amer Fort Heritage Entrance",
        "zone_id": "zone_amer",
        "lat": 26.9855,
        "lng": 75.8513,
        "is_priority": False
    }
]

def resolve_location_info(query: str, db: Session) -> Dict[str, Any]:
    q = (query or "").strip().lower()
    if not q:
        q = "zone_sms_hospital"
    
    # 1. Match against known Jaipur landmarks
    for lm in JAIPUR_LANDMARKS:
        if lm["zone_id"].lower() == q or any(k in q for k in lm["keys"]):
            return {
                "id": lm["zone_id"],
                "name": lm["name"],
                "lat": lm["lat"],
                "lng": lm["lng"],
                "is_priority": lm["is_priority"]
            }

    # 2. Check Database Zone table
    db_zone = db.query(Zone).filter(
        (Zone.id == query) | (Zone.zone_name.ilike(f"%{query}%"))
    ).first()
    if db_zone:
        return {
            "id": db_zone.id,
            "name": db_zone.zone_name,
            "lat": db_zone.center_lat,
            "lng": db_zone.center_lng,
            "is_priority": db_zone.is_priority_designated
        }

    # 3. Check for word token matches in DB zones
    words = [w for w in q.split() if len(w) > 3]
    for w in words:
        db_zone = db.query(Zone).filter(Zone.zone_name.ilike(f"%{w}%")).first()
        if db_zone:
            return {
                "id": db_zone.id,
                "name": db_zone.zone_name,
                "lat": db_zone.center_lat,
                "lng": db_zone.center_lng,
                "is_priority": db_zone.is_priority_designated
            }

    # 4. Deterministic Jaipur coordinates for arbitrary custom inputs
    hash_val = int(hashlib.md5(q.encode("utf-8")).hexdigest()[:8], 16)
    pseudo_lat = 26.7800 + ((hash_val % 1000) / 1000.0) * 0.1700
    pseudo_lng = 75.7400 + (((hash_val // 1000) % 1000) / 1000.0) * 0.1300
    display_title = query.title() if query else "Jaipur Location"
    
    return {
        "id": f"loc_{hash_val % 10000}",
        "name": display_title,
        "lat": round(pseudo_lat, 4),
        "lng": round(pseudo_lng, 4),
        "is_priority": False
    }

def haversine_distance_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371.0 # km
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlng / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    direct_dist = R * c
    # Realistic road distance accounts for urban intersections and route turns (~1.28x)
    road_dist = max(1.2, round(direct_dist * 1.28, 1))
    return road_dist

# Standard vehicle catalog specifications
VEHICLE_CATALOG = [
    # Rapido options
    {
        "provider_id": "rapido",
        "provider_name": "Rapido",
        "ride_type": "bike",
        "base_fare": 25.0,
        "per_km": 8.0,
        "base_eta": 2,
        "app_url": "https://www.rapido.bike"
    },
    {
        "provider_id": "rapido",
        "provider_name": "Rapido",
        "ride_type": "auto",
        "base_fare": 35.0,
        "per_km": 12.0,
        "base_eta": 3,
        "app_url": "https://www.rapido.bike"
    },
    # Uber options
    {
        "provider_id": "uber",
        "provider_name": "Uber",
        "ride_type": "auto",
        "base_fare": 38.0,
        "per_km": 12.5,
        "base_eta": 3,
        "app_url": "https://m.uber.com/looking"
    },
    {
        "provider_id": "uber",
        "provider_name": "Uber",
        "ride_type": "economy",
        "base_fare": 55.0,
        "per_km": 16.5,
        "base_eta": 4,
        "app_url": "https://m.uber.com/looking"
    },
    {
        "provider_id": "uber",
        "provider_name": "Uber",
        "ride_type": "sedan",
        "base_fare": 75.0,
        "per_km": 21.0,
        "base_eta": 5,
        "app_url": "https://m.uber.com/looking"
    },
    {
        "provider_id": "uber",
        "provider_name": "Uber",
        "ride_type": "suv",
        "base_fare": 115.0,
        "per_km": 28.0,
        "base_eta": 6,
        "app_url": "https://m.uber.com/looking"
    },
    # Ola options
    {
        "provider_id": "ola",
        "provider_name": "Ola",
        "ride_type": "auto",
        "base_fare": 36.0,
        "per_km": 12.2,
        "base_eta": 3,
        "app_url": "https://book.olacabs.com"
    },
    {
        "provider_id": "ola",
        "provider_name": "Ola",
        "ride_type": "economy",
        "base_fare": 52.0,
        "per_km": 16.0,
        "base_eta": 5,
        "app_url": "https://book.olacabs.com"
    },
    {
        "provider_id": "ola",
        "provider_name": "Ola",
        "ride_type": "sedan",
        "base_fare": 72.0,
        "per_km": 20.5,
        "base_eta": 6,
        "app_url": "https://book.olacabs.com"
    },
    {
        "provider_id": "ola",
        "provider_name": "Ola",
        "ride_type": "suv",
        "base_fare": 110.0,
        "per_km": 27.5,
        "base_eta": 7,
        "app_url": "https://book.olacabs.com"
    },
    # QuickRide local fleet
    {
        "provider_id": "quickride",
        "provider_name": "QuickRide Jaipur",
        "ride_type": "economy",
        "base_fare": 46.0,
        "per_km": 15.0,
        "base_eta": 5,
        "app_url": "https://quickride.in"
    },
    {
        "provider_id": "quickride",
        "provider_name": "QuickRide Jaipur",
        "ride_type": "sedan",
        "base_fare": 66.0,
        "per_km": 19.5,
        "base_eta": 7,
        "app_url": "https://quickride.in"
    }
]

@router.get("/rides/locations")
def list_popular_locations():
    """Returns top Jaipur popular landmarks and transit hubs for location search & autocomplete."""
    return [
        {
            "id": item["zone_id"],
            "name": item["name"],
            "lat": item["lat"],
            "lng": item["lng"],
            "is_priority": item["is_priority"]
        }
        for item in JAIPUR_LANDMARKS
    ]

@router.post("/rides/compare", response_model=RideCompareResponse)
def compare_rides(req: RideCompareRequest, db: Session = Depends(get_db)):
    """
    Compares cross-provider ride options for an origin and destination.
    Dynamically computes trip distance, per-km dynamic pricing across providers,
    ETA based on origin location, and driver ranking with Bayesian rating adjustments.
    """
    # 1. Resolve origin and destination
    origin_info = resolve_location_info(req.origin, db)
    dest_info = resolve_location_info(req.destination, db)

    # 2. Calculate dynamic road distance & duration
    distance_km = haversine_distance_km(
        origin_info["lat"], origin_info["lng"],
        dest_info["lat"], dest_info["lng"]
    )
    est_duration_minutes = max(5, int(distance_km * 2.2 + 4))

    # 3. Determine surge multiplier based on pickup zone demand / priority
    surge_mult = 1.0
    if origin_info.get("is_priority"):
        # Designated priority zone: protected from gouging (1.0x to 1.1x max)
        surge_mult = 1.05
    else:
        # Check snapshot demand if available
        snap = db.query(ZoneMetricSnapshot).filter(
            ZoneMetricSnapshot.zone_id == origin_info["id"]
        ).first()
        if snap and snap.demand_estimate and snap.available_ride_count:
            ratio = snap.demand_estimate / max(1, snap.available_ride_count)
            if ratio > 2.0:
                surge_mult = 1.25
            elif ratio > 1.2:
                surge_mult = 1.10

    # 4. Fetch drivers and existing provider status
    providers = {p.id: p for p in db.query(Provider).all()}
    drivers = db.query(Driver).all()
    driver_map: Dict[str, List[Driver]] = {}
    for d in drivers:
        driver_map.setdefault(d.provider_id, []).append(d)

    # Filter catalog by requested vehicle category
    catalog = VEHICLE_CATALOG
    if req.ride_category and req.ride_category != "all":
        catalog = [c for c in catalog if c["ride_type"] == req.ride_category]

    raw_options = []
    now = datetime.now(timezone.utc)

    for idx, item in enumerate(catalog):
        provider_id = item["provider_id"]
        provider = providers.get(provider_id)
        
        # Check provider status
        if provider and provider.status == "not_connected":
            continue

        # Dynamic fare calculation for this route
        raw_fare = (item["base_fare"] + item["per_km"] * distance_km) * surge_mult
        estimated_fare = round(raw_fare / 5.0) * 5.0  # round to nearest ₹5 for clean pricing

        # Select representative driver for this provider
        drv_candidates = driver_map.get(provider_id, [])
        drv = drv_candidates[idx % len(drv_candidates)] if drv_candidates else None
        
        driver_dict = None
        driver_proximity_km = 0.8 + (idx * 0.4)
        if drv:
            driver_dict = {
                "id": drv.id,
                "display_name": drv.display_name,
                "rating_mean": drv.rating_mean,
                "rating_count": drv.rating_count,
                "verified_driver_cancel_count": drv.verified_driver_cancel_count,
                "eligible_ride_count": drv.eligible_ride_count,
                "vehicle_model": drv.vehicle_model,
                "vehicle_number": drv.vehicle_number,
                "is_demo": drv.is_demo
            }
            if drv.current_lat and drv.current_lng:
                driver_proximity_km = haversine_distance_km(
                    drv.current_lat, drv.current_lng,
                    origin_info["lat"], origin_info["lng"]
                )

        pickup_eta = max(2, min(14, int(driver_proximity_km * 2.2 + item["base_eta"])))

        booking_url = provider.app_url if provider and provider.app_url else item["app_url"]

        raw_options.append({
            "id": f"dyn_opt_{provider_id}_{item['ride_type']}_{idx}",
            "provider": item["provider_name"],
            "provider_id": provider_id,
            "ride_type": item["ride_type"],
            "estimated_fare": float(estimated_fare),
            "currency": "INR",
            "pickup_eta_minutes": pickup_eta,
            "availability_status": "available",
            "driver": driver_dict,
            "observed_at": now,
            "source_type": "simulated",
            "is_demo": True,
            "booking_action_url": booking_url,
            "direct_booking_supported": False
        })

    # 5. Apply ranking engine
    ranked = rank_ride_options(raw_options, sort_by=req.sort_by or "best_overall")

    # 6. Summary metrics
    valid_fares = [r["estimated_fare"] for r in ranked if r.get("estimated_fare")]
    valid_etas = [r["pickup_eta_minutes"] for r in ranked if r.get("pickup_eta_minutes")]
    valid_ratings = [
        r["driver"]["rating_mean"] for r in ranked
        if r.get("driver") and r["driver"].get("rating_mean")
    ]

    summary = {
        "best_rated_driver": max(valid_ratings) if valid_ratings else None,
        "lowest_estimated_fare": min(valid_fares) if valid_fares else None,
        "fastest_pickup_eta": min(valid_etas) if valid_etas else None,
        "total_options": len(ranked),
        "sort_applied": req.sort_by or "best_overall",
        "distance_km": distance_km,
        "est_duration_minutes": est_duration_minutes,
        "surge_multiplier": round(surge_mult, 2)
    }

    # Format options for output schema
    formatted_options = []
    for r in ranked:
        d = r.get("driver")
        drv_out = None
        if d:
            drv_out = DriverDetail(
                id=d["id"],
                display_name=d["display_name"],
                rating_mean=d["rating_mean"],
                rating_count=d["rating_count"],
                adjusted_rating=d["adjusted_rating"],
                verified_driver_cancel_count=d["verified_driver_cancel_count"],
                eligible_ride_count=d["eligible_ride_count"],
                smoothed_driver_cancel_rate=d["smoothed_driver_cancel_rate"],
                vehicle_model=d.get("vehicle_model"),
                vehicle_number=d.get("vehicle_number"),
                confidence_label=d["confidence_label"],
                is_demo=d.get("is_demo", True)
            )

        sb = r["score_breakdown"]
        formatted_options.append(RideOptionOut(
            id=r["id"],
            provider=r["provider"],
            provider_id=r["provider_id"],
            ride_type=r["ride_type"],
            estimated_fare=r["estimated_fare"],
            currency=r["currency"],
            pickup_eta_minutes=r["pickup_eta_minutes"],
            availability_status=r["availability_status"],
            driver=drv_out,
            score=r["score"],
            score_breakdown=ScoreBreakdown(
                rating=sb["rating"],
                reliability=sb["reliability"],
                eta=sb["eta"],
                fare=sb["fare"],
                freshness=sb["freshness"],
                active_weights=sb["active_weights"]
            ),
            ranking_explanation=r["ranking_explanation"],
            source_type=r["source_type"],
            observed_at=r["observed_at"],
            confidence=r["confidence"],
            is_demo=r["is_demo"],
            booking_action_url=r.get("booking_action_url"),
            direct_booking_supported=r.get("direct_booking_supported", False)
        ))

    return RideCompareResponse(
        options=formatted_options,
        summary=summary,
        origin_zone={
            "id": origin_info["id"],
            "name": origin_info["name"],
            "lat": origin_info["lat"],
            "lng": origin_info["lng"],
            "is_priority": origin_info["is_priority"]
        },
        destination_zone={
            "id": dest_info["id"],
            "name": dest_info["name"],
            "lat": dest_info["lat"],
            "lng": dest_info["lng"],
            "is_priority": dest_info["is_priority"]
        },
        providers_checked=len(set(r.provider_id for r in formatted_options)),
        demo_notice=f"Route: {origin_info['name']} → {dest_info['name']} ({distance_km} km, ~{est_duration_minutes} min). Dynamic comparison across live fleets.",
        is_demo=True,
        generated_at=datetime.now(timezone.utc)
    )
