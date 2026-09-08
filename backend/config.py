from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr, model_validator


class Settings(BaseSettings):
    mongodb_uri: str = "mongodb://mongodb:27017"
    database_name: str = "glovebox"
    session_ttl_days: int = Field(30, ge=1, le=365)
    setup_token: SecretStr | None = Field(None, description="Operator secret required in X-Setup-Token when configured")
    setup_token_required: bool = Field(False, description="Enable in production to fail startup unless SETUP_TOKEN is configured")
    login_max_attempts: int = Field(10, ge=1, le=1000)
    login_window_seconds: int = Field(300, ge=1, le=86400)
    login_max_buckets: int = Field(10000, ge=1, le=100000)
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    reminder_worker_enabled: bool = True
    reminder_check_seconds: int = Field(60, ge=10, le=3600)
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
