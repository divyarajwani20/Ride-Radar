from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.schemas.schemas import DemoScenarioOut, DemoScenarioActivateResponse
from app.services.demo_data import DEMO_SCENARIOS
from app.db.init_db import reset_to_scenario
from app.core.config import settings

router = APIRouter()

@router.get("/demo/scenarios", response_model=List[DemoScenarioOut])
def list_demo_scenarios():
    """Lists the 14 repeatable demo scenarios (Section 31)."""
    return [DemoScenarioOut(**s) for s in DEMO_SCENARIOS]

@router.post("/demo/scenarios/{scenario_id}/activate", response_model=DemoScenarioActivateResponse)
def activate_demo_scenario(scenario_id: str, db: Session = Depends(get_db)):
    """
    Deterministically activates and resets test data for the selected demo scenario.
    Only available in development/demo mode.
    """
    matched = next((s for s in DEMO_SCENARIOS if s["id"] == scenario_id), None)
    if not matched:
        raise HTTPException(status_code=404, detail="Scenario ID not recognized")

    settings.ACTIVE_DEMO_SCENARIO = scenario_id
    reset_to_scenario(scenario_id, db=db)

    return DemoScenarioActivateResponse(
        scenario_id=scenario_id,
        name=matched["name"],
        message=f"Scenario '{matched['name']}' activated successfully. Test data reset deterministically.",
        active=True
    )
