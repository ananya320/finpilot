from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")
    database_url: str = "sqlite:///./finpilot.db"
    google_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

settings = Settings()