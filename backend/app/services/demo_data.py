from typing import List, Dict, Any
from datetime import datetime, timedelta, timezone

# 14 Documented Demo Scenarios (Section 31)
DEMO_SCENARIOS = [
    {
        "id": "scenario_1_successful_match",
        "name": "1. Successful Emergency Match",
        "description": "Nearest eligible top-ranked driver accepts immediately. Full quote, score breakdown, and arrival ETA.",
        "expected_outcome": "Immediate confirmation with top candidate (Driver B - 4.88 stars, 340 rides).",
        "category": "Priority Dispatch"
    },
    {
        "id": "scenario_2_first_declines",
        "name": "2. First Driver Declines -> Automatic Retry",
        "description": "First candidate driver is busy and declines offer. System immediately retries next candidate who accepts.",
        "expected_outcome": "Seamless automatic retry without passenger manual re-entry.",
        "category": "Automatic Recovery"
    },
    {
        "id": "scenario_3_first_times_out",
        "name": "3. First Driver Times Out",
        "description": "Candidate driver fails to respond within 20s deadline. Recorded as timeout, system transitions to next candidate.",
        "expected_outcome": "Timeout tracked separately from decline in accountability ledger.",
        "category": "Accountability"
    },
    {
        "id": "scenario_4_accepted_cancels",
        "name": "4. Driver Cancels After Acceptance -> Recovery",
        "description": "Driver accepted but encounters breakdown 2 mins in. Automatic recovery triggers backup driver dispatch.",
        "expected_outcome": "Recovery panel updates ETA and dispatches backup candidate without extra fee.",
        "category": "Automatic Recovery"
    },
    {
        "id": "scenario_5_all_candidates_fail",
        "name": "5. All Candidates Fail -> Mobility Switch & Refund",
        "description": "All 3 retry attempts fail. System marks unavailable, suggests prepaid auto/metro, and refunds priority fee.",
        "expected_outcome": "Transparent unavailable state with 100% priority fee refund + local transport suggestions.",
        "category": "Last-Resort Mobility"
    },
    {
        "id": "scenario_6_fare_exceeds_cap",
        "name": "6. Fare Exceeds Passenger Cap",
        "description": "Only available backup is luxury SUV exceeding passenger's ₹300 max cap. Halts auto-dispatch and prompts passenger.",
        "expected_outcome": "Price protection prevents unauthorized fare increase.",
        "category": "Price Protection"
    },
    {
        "id": "scenario_7_no_reliable_history",
        "name": "7. Driver with No Rating History",
        "description": "Newly onboarded driver with 0 reviews. Uses Bayesian shrinkage to global mean and flags 'Limited rating history'.",
        "expected_outcome": "Fair ranking without inventing fake reviews or treating as zero.",
        "category": "Driver Ranking"
    },
    {
        "id": "scenario_8_stale_availability",
        "name": "8. Stale Availability Signal",
        "description": "A driver's position has not refreshed in 45 minutes. Freshness score drops significantly.",
        "expected_outcome": "Stale candidate penalized in score with visible freshness warning.",
        "category": "Data Freshness"
    },
    {
        "id": "scenario_9_priority_zone",
        "name": "9. Designated Priority Zone (SMS Hospital)",
        "description": "Pickup located at verified hospital trauma centre. Qualifies for high-need priority allocation.",
        "expected_outcome": "Hospital priority badge and policy terms displayed clearly.",
        "category": "Emergency Priority"
    },
    {
        "id": "scenario_10_non_designated_pickup",
        "name": "10. Urgent Non-Designated Pickup",
        "description": "Priority requested from a regular commercial street (Raja Park). Permitted subject to available supply.",
        "expected_outcome": "App explains that priority dispatch is attempted without designated hospital benefits.",
        "category": "Emergency Priority"
    },
    {
        "id": "scenario_11_demand_spike",
        "name": "11. Demand Spike Shock Forecast",
        "description": "High demand pressure (2.2x ratio) detected in Malviya Nagar due to evening transit peak.",
        "expected_outcome": "Demand Shock warning tag with suggested reserve vehicle mobilization.",
        "category": "Demand Forecasting"
    },
    {
        "id": "scenario_12_provider_not_connected",
        "name": "12. Provider Not Connected (Honest Handoff)",
        "description": "No unverified fake API calls. Shows Rapido as Not Connected with direct deep link.",
        "expected_outcome": "Displays honest 'Not connected' badge and 'Open Provider App' button.",
        "category": "Integration Honesty"
    },
    {
        "id": "scenario_13_duplicate_dispatch",
        "name": "13. Duplicate Dispatch Idempotency",
        "description": "Submitting identical idempotency key returns existing request without duplicate charge or offers.",
        "expected_outcome": "Idempotent response with HTTP 200 and existing booking status.",
        "category": "Reliability"
    },
    {
        "id": "scenario_14_passenger_cancels",
        "name": "14. Passenger Cancels During Search",
        "description": "Passenger cancels priority request before driver acceptance. Validates transition and applies 100% refund.",
        "expected_outcome": "Request status moves to CANCELLED; priority fee voided.",
        "category": "Accountability"
    }
]

JAIPUR_ZONES_SEED = [
    {
        # Real: SMS Medical College & Hospital main gate entrance, Sawai Ram Singh Road
        "id": "zone_sms_hospital",
        "city": "Jaipur",
        "zone_name": "SMS Medical Hospital & Trauma Centre",
        "cell_id": "JPR-CELL-01",
        "center_lat": 26.8995,
        "center_lng": 75.8193,
        "radius_meters": 1200,
        "is_priority_designated": True,
        "priority_category": "hospital",
        "description": "State medical college & premier tertiary trauma emergency facility."
    },
    {
        # Real: Jaipur Junction Railway Station main entrance, Station Road
        "id": "zone_jaipur_junction",
        "city": "Jaipur",
        "zone_name": "Jaipur Junction Railway Station",
        "cell_id": "JPR-CELL-02",
        "center_lat": 26.9215,
        "center_lng": 75.7873,
        "radius_meters": 1500,
        "is_priority_designated": True,
        "priority_category": "railway_station",
        "description": "Primary interstate rail gateway and metro transit interchange."
    },
    {
        # Real: Jaipur International Airport (JAI), Sanganer — terminal entrance
        "id": "zone_airport",
        "city": "Jaipur",
        "zone_name": "Jaipur International Airport (JAI)",
        "cell_id": "JPR-CELL-03",
        "center_lat": 26.8241,
        "center_lng": 75.8122,
        "radius_meters": 2000,
        "is_priority_designated": True,
        "priority_category": "airport",
        "description": "International & domestic aviation terminal (Sanganer)."
    },
    {
        # Real: Apex Hospital, Lal Kothi, Tonk Road — main gate
        "id": "zone_apex_hospital",
        "city": "Jaipur",
        "zone_name": "Apex & EHCC Hospital Corridor",
        "cell_id": "JPR-CELL-04",
        "center_lat": 26.8635,
        "center_lng": 75.8082,
        "radius_meters": 1200,
        "is_priority_designated": True,
        "priority_category": "hospital",
        "description": "Malviya Nagar medical hub housing multi-speciality cardiac & emergency hospitals."
    },
    {
        # Real: C-Scheme, Ashok Nagar Circle, Jaipur
        "id": "zone_c_scheme",
        "city": "Jaipur",
        "zone_name": "C-Scheme Central Business District",
        "cell_id": "JPR-CELL-05",
        "center_lat": 26.9116,
        "center_lng": 75.8001,
        "radius_meters": 1400,
        "is_priority_designated": False,
        "priority_category": None,
        "description": "Central commercial, banking, government offices, and dining boulevard."
    },
    {
        # Real: Malviya Nagar, Jaipur — South-East hub near Riddhi Siddhi Circle
        "id": "zone_malviya_nagar",
        "city": "Jaipur",
        "zone_name": "Malviya Nagar Commercial & Tech Hub",
        "cell_id": "JPR-CELL-06",
        "center_lat": 26.8521,
        "center_lng": 75.8234,
        "radius_meters": 1600,
        "is_priority_designated": False,
        "priority_category": None,
        "description": "Major southeastern residential, retail mall, and tech park cluster."
    },
    {
        # Real: Mansarovar Metro Station, Sector 5, Jaipur
        "id": "zone_mansarovar",
        "city": "Jaipur",
        "zone_name": "Mansarovar Sector 5 & Metro Terminus",
        "cell_id": "JPR-CELL-07",
        "center_lat": 26.8614,
        "center_lng": 75.7619,
        "radius_meters": 1800,
        "is_priority_designated": False,
        "priority_category": None,
        "description": "High-density residential colony and southern Metro terminal."
    },
    {
        # Real: Vaishali Nagar, Amrapali Circle, Jaipur
        "id": "zone_vaishali_nagar",
        "city": "Jaipur",
        "zone_name": "Vaishali Nagar Amrapali Circle",
        "cell_id": "JPR-CELL-08",
        "center_lat": 26.9063,
        "center_lng": 75.7401,
        "radius_meters": 1600,
        "is_priority_designated": False,
        "priority_category": None,
        "description": "Western affluent residential & bustling commercial avenue."
    },
    {
        # Real: Raja Park Market, Gopalpura Bypass junction, Jaipur
        "id": "zone_raja_park",
        "city": "Jaipur",
        "zone_name": "Raja Park Shopping Promenade",
        "cell_id": "JPR-CELL-09",
        "center_lat": 26.8897,
        "center_lng": 75.8358,
        "radius_meters": 1300,
        "is_priority_designated": False,
        "priority_category": None,
        "description": "Eastern residential quarter with vibrant street shopping and eateries."
    },
    {
        # Real: Sitapura Industrial Area, RIICO, near MNIT junction
        "id": "zone_sitapura",
        "city": "Jaipur",
        "zone_name": "Sitapura Industrial & Educational Zone",
        "cell_id": "JPR-CELL-10",
        "center_lat": 26.7714,
        "center_lng": 75.8445,
        "radius_meters": 2200,
        "is_priority_designated": False,
        "priority_category": None,
        "description": "Southern industrial belt, SEZ, and major university campuses."
    },
    {
        # Real: Hawa Mahal (Palace of Winds) — Badi Chaupar, Pink City
        "id": "zone_hawa_mahal",
        "city": "Jaipur",
        "zone_name": "Hawa Mahal & Pink City Old Town",
        "cell_id": "JPR-CELL-11",
        "center_lat": 26.9239,
        "center_lng": 75.8267,
        "radius_meters": 1100,
        "is_priority_designated": False,
        "priority_category": None,
        "description": "Historic walled city core — high tourist footfall, narrow lanes, peak demand evenings."
    },
    {
        # Real: World Trade Park (WTP), Malviya Nagar — premium mall & office complex
        "id": "zone_world_trade_park",
        "city": "Jaipur",
        "zone_name": "World Trade Park (WTP) Mall",
        "cell_id": "JPR-CELL-12",
        "center_lat": 26.8554,
        "center_lng": 75.8059,
        "radius_meters": 900,
        "is_priority_designated": False,
        "priority_category": None,
        "description": "Largest premium mall & office tower complex in Rajasthan — high ride-out demand on weekends."
    }
]

PROVIDERS_SEED = [
    {
        "id": "uber",
        "name": "Uber",
        "status": "demo",
        "integration_type": "official_oauth",
        "status_message": "Demo Mode active. Connect official OAuth credentials in Settings to switch to live partner API.",
        "app_url": "https://m.uber.com/looking"
    },
    {
        "id": "ola",
        "name": "Ola Cabs",
        "status": "demo",
        "integration_type": "api_key",
        "status_message": "Demo Mode active. Official Ola developer credentials can be provided in Settings.",
        "app_url": "https://book.olacabs.com"
    },
    {
        "id": "rapido",
        "name": "Rapido",
        "status": "demo",
        "integration_type": "api_key",
        "status_message": "Demo Mode active. Direct app link available for booking completion.",
        "app_url": "https://www.rapido.bike"
    },
    {
        "id": "quickride",
        "name": "QuickRide Jaipur",
        "status": "demo",
        "integration_type": "simulated",
        "status_message": "Synthetic local fleet provider for demonstration testing.",
        "app_url": "https://quickride.in"
    }
]

DRIVERS_SEED = [
    {
        "id": "driver_01_veteran",
        "provider_id": "uber",
        "display_name": "Rajesh K. (Demo Driver)",
        "rating_mean": 4.88,
        "rating_count": 340,
        "verified_driver_cancel_count": 4,
        "eligible_ride_count": 280,
        "vehicle_model": "Maruti Dzire Prime (White)",
        "vehicle_number": "RJ-14-TA-3829",
        "current_zone_id": "zone_sms_hospital",
        "current_lat": 26.8995,
        "current_lng": 75.8160,
        "is_available": True
    },
    {
        "id": "driver_02_perfect_new",
        "provider_id": "ola",
        "display_name": "Amit V. (Demo Driver)",
        "rating_mean": 5.00,
        "rating_count": 2,  # Tiny review count: Bayesian shrinkage will adjust this to ~4.58!
        "verified_driver_cancel_count": 0,
        "eligible_ride_count": 6,
        "vehicle_model": "Hyundai Aura (Silver)",
        "vehicle_number": "RJ-14-TB-9102",
        "current_zone_id": "zone_sms_hospital",
        "current_lat": 26.8970,
        "current_lng": 75.8190,
        "is_available": True
    },
    {
        "id": "driver_03_steady",
        "provider_id": "quickride",
        "display_name": "Sunil S. (Demo Driver)",
        "rating_mean": 4.65,
        "rating_count": 140,
        "verified_driver_cancel_count": 3,
        "eligible_ride_count": 120,
        "vehicle_model": "Tata Tigor EV (Teal)",
        "vehicle_number": "RJ-14-EV-4411",
        "current_zone_id": "zone_c_scheme",
        "current_lat": 26.9080,
        "current_lng": 75.8030,
        "is_available": True
    },
    {
        "id": "driver_04_high_cancel",
        "provider_id": "rapido",
        "display_name": "Mahesh P. (Demo Driver)",
        "rating_mean": 4.25,
        "rating_count": 85,
        "verified_driver_cancel_count": 18,  # High cancellation history!
        "eligible_ride_count": 90,
        "vehicle_model": "Bajaj Auto CNG",
        "vehicle_number": "RJ-14-AR-7821",
        "current_zone_id": "zone_jaipur_junction",
        "current_lat": 26.9215,
        "current_lng": 75.7865,
        "is_available": True
    },
    {
        "id": "driver_05_unrated",
        "provider_id": "uber",
        "display_name": "Vikram N. (Demo Driver)",
        "rating_mean": 4.50,
        "rating_count": 0,  # Zero reviews: tests unrated driver behavior
        "verified_driver_cancel_count": 0,
        "eligible_ride_count": 0,
        "vehicle_model": "Toyota Etios (Grey)",
        "vehicle_number": "RJ-14-TA-1100",
        "current_zone_id": "zone_malviya_nagar",
        "current_lat": 26.8520,
        "current_lng": 75.8195,
        "is_available": True
    },
    {
        "id": "driver_06_top_rated",
        "provider_id": "ola",
        "display_name": "Dinesh J. (Demo Driver)",
        "rating_mean": 4.93,
        "rating_count": 520,
        "verified_driver_cancel_count": 2,
        "eligible_ride_count": 480,
        "vehicle_model": "Honda Amaze Sedan (Gold)",
        "vehicle_number": "RJ-14-TA-5592",
        "current_zone_id": "zone_airport",
        "current_lat": 26.8295,
        "current_lng": 75.8040,
        "is_available": True
    }
]
