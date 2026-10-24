import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["demo_mode"] is True
    assert data["city"] == "Jaipur"

def test_providers_endpoint():
    res = client.get("/api/v1/providers")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 3
    provider_ids = [p["id"] for p in data]
    assert "uber" in provider_ids
    assert "ola" in provider_ids
    assert "rapido" in provider_ids

def test_rides_compare_endpoint():
    payload = {
        "origin": "zone_sms_hospital",
        "destination": "zone_c_scheme",
        "departure_time": None,
        "ride_category": "all",
        "passenger_count": 1,
        "sort_by": "best_overall"
    }
    res = client.post("/api/v1/rides/compare", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert len(data["options"]) > 0
    assert "score" in data["options"][0]
    assert "score_breakdown" in data["options"][0]
    assert "ranking_explanation" in data["options"][0]
    assert data["is_demo"] is True

def test_hot_zones_endpoint():
    res = client.get("/api/v1/hot-zones?city=Jaipur&window=last_hour&metric=zone_score")
    assert res.status_code == 200
    data = res.json()
    assert len(data["zones"]) >= 5
    first_zone = data["zones"][0]
    assert "driver_cancel_rate" in first_zone
    assert "passenger_cancel_rate" in first_zone
    assert "zone_score" in first_zone
    assert "tags" in first_zone

def test_priority_flow_endpoints():
    # 1. List priority zones
    pz_res = client.get("/api/v1/priority/zones")
    assert pz_res.status_code == 200
    pz_data = pz_res.json()
    assert len(pz_data) >= 3

    # 2. Request priority quote
    quote_payload = {
        "pickup_zone_id": "zone_sms_hospital",
        "destination_zone_id": "zone_c_scheme",
        "urgency_category": "medical",
        "max_acceptable_fare": 320.0
    }
    quote_res = client.post("/api/v1/priority/requests", json=quote_payload)
    assert quote_res.status_code == 200
    q_data = quote_res.json()
    assert "request_id" in q_data
    assert q_data["is_designated_priority_zone"] is True
    assert q_data["priority_fee"] == 50.0

    # 3. Dispatch priority request
    req_id = q_data["request_id"]
    dispatch_payload = {
        "request_id": req_id,
        "idempotency_key": f"test_idemp_{req_id}",
        "accept_terms": True,
        "simulate_outcome": "force_success"
    }
    dispatch_res = client.post(f"/api/v1/priority/requests/{req_id}/dispatch", json=dispatch_payload)
    assert dispatch_res.status_code == 200
    d_data = dispatch_res.json()
    assert d_data["status"] == "driver_accepted"
    assert d_data["confirmed_driver"] is not None

def test_demo_scenarios_list_and_activate():
    scenarios_res = client.get("/api/v1/demo/scenarios")
    assert scenarios_res.status_code == 200
    scenarios = scenarios_res.json()
    assert len(scenarios) == 14

    # Activate scenario 1
    act_res = client.post("/api/v1/demo/scenarios/scenario_1_successful_match/activate")
    assert act_res.status_code == 200
    assert act_res.json()["active"] is True
