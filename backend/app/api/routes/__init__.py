from fastapi import APIRouter
from app.api.routes import (
    health, providers, rides, hot_zones, insights,
    priority, reliability, mobility, forecast, demo, admin, observations
)

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(providers.router, tags=["Providers"])
api_router.include_router(rides.router, tags=["Rides"])
api_router.include_router(hot_zones.router, tags=["Hot Zones"])
api_router.include_router(insights.router, tags=["Insights"])
api_router.include_router(priority.router, tags=["Emergency Priority"])
api_router.include_router(reliability.router, tags=["Reliability & Risk"])
api_router.include_router(mobility.router, tags=["Mobility Alternatives"])
api_router.include_router(forecast.router, tags=["Demand Forecasting"])
api_router.include_router(demo.router, tags=["Demo Scenarios"])
api_router.include_router(admin.router, tags=["Admin Ledger"])
api_router.include_router(observations.router, tags=["Observations"])
