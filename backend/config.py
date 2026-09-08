from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr, model_validator


class Settings(BaseSettings):
    mongodb_uri: str = "mongodb://mongodb:27017"
    database_name: str = "glovebox"
    session_ttl_days: int = Field(7, ge=1, le=365)
    api_docs_enabled: bool = False
    setup_token: SecretStr | None = Field(None, description="Operator secret required in X-Setup-Token when configured")
    setup_token_required: bool = Field(True, description="Fail startup unless SETUP_TOKEN is configured; explicitly disable for local/test use")
    login_max_attempts: int = Field(10, ge=1, le=1000)
    login_window_seconds: int = Field(300, ge=1, le=86400)
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    reminder_worker_enabled: bool = True
    reminder_check_seconds: int = Field(60, ge=10, le=3600)
    max_cars_per_user: int = Field(100, ge=1, le=1000)
    max_maintenance_logs_per_car: int = Field(1000, ge=1, le=10000)
    max_mods_per_car: int = Field(500, ge=1, le=5000)
    max_notifications_per_user: int = Field(100, ge=1, le=1000)
    notification_max_delivery_attempts: int = Field(5, ge=1, le=20)
    notification_dispatch_batch: int = Field(10, ge=1, le=50)
    smtp_host: str | None = None
    smtp_port: int = Field(587, ge=1, le=65535)
    smtp_username: str | None = None
    smtp_password: SecretStr | None = None
    smtp_from: str | None = None
    smtp_starttls: bool = True

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @model_validator(mode="after")
    def validate_setup_token(self):
        if self.setup_token is not None and len(self.setup_token.get_secret_value()) < 32:
            raise ValueError("SETUP_TOKEN must contain at least 32 characters")
        if self.setup_token_required and self.setup_token is None:
            raise ValueError("SETUP_TOKEN_REQUIRED requires SETUP_TOKEN")
        return self


settings = Settings()
