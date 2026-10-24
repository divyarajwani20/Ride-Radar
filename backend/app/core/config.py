import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "RideRadar"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    DEMO_MODE: bool = True
    DEFAULT_CITY: str = "Jaipur"
    ACTIVE_DEMO_SCENARIO: str = "scenario_1_successful_match"
    
    _BACKEND_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    DATABASE_URL: str = f"sqlite:///{os.path.join(_BACKEND_DIR, 'rideradar.db')}"
    
    # Provider Integration Credentials (Optional — leave empty for Demo/Not-connected status)
    UBER_CLIENT_ID: str = ""
    UBER_CLIENT_SECRET: str = ""
    OLA_API_KEY: str = ""
    RAPIDO_API_KEY: str = ""
    
    # Allowed CORS origins
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
