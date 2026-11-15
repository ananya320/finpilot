from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")
    environment: str = "development"       # set to "production" on Render
    database_url: str = "sqlite:///./finpilot.db"
    google_api_key: str = ""
    gemini_model: str = "gemini-3.8-flash"
    secret_key: str = ""
    token_days: int = 7

    # the login account (set in .env locally, in Render's dashboard online)
    default_email: str = ""
    default_password: str = ""
    default_name: str = "User"
    allow_signup: bool = False

    cors_origins: str = "http://localhost:5173,http://localhost:3000"  # comma-separated
    enable_vector_search: bool = True      # set to false on the free server


settings = Settings()