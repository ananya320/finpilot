from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")
    database_url: str = "sqlite:///./finpilot.db"
    google_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    secret_key: str = ""
    token_days: int = 7

    # fixed login (change these whenever you want)
    default_email: str = "user@gmail.com"
    default_password: str = "1234"
    default_name: str = "User"
    allow_signup: bool = False   # True = anyone can create more accounts


settings = Settings()