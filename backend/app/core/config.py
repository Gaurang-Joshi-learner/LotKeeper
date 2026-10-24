"""Application settings, loaded from environment variables (or a .env file)."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./lotkeeper.db"
    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60 * 12
    bcrypt_rounds: int = 12  # tests lower this to keep the suite fast

    # How long a "hold" reserves a unit for a shopper, and how often expired holds are swept.
    hold_minutes: int = 10
    hold_sweep_seconds: int = 15

    # The spec makes only DELETE and restock admin-only. Flip this to lock create/update to admins too.
    vehicle_write_admin_only: bool = False

    cors_origins: str = "http://localhost:5173,http://localhost:8080"

    seed_on_startup: bool = False
    seed_demo_vehicles: bool = True  # set false for an empty lot (accounts are still created)
    seed_admin_email: str = "admin@demo.com"
    seed_admin_password: str = "admin12345"
    seed_user_email: str = "shopper@demo.com"
    seed_user_password: str = "shopper12345"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
