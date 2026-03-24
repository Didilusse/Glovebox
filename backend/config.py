from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mongodb_uri: str = "mongodb://localhost:27017"
    database_name: str = "glovebox"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()