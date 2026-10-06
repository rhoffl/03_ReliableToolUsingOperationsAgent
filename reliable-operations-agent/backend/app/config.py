from decimal import Decimal
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "sqlite:///./opsagent.db"
    cors_origins: str = "http://localhost:3003"
    max_tool_calls: int = 20
    max_incident_cost_usd: Decimal = Decimal("0.25")
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
