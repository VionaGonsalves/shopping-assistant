from pydantic_settings import SettingsConfigDict, BaseSettings

class Settings(BaseSettings):
    database_url: str
    secret_key: str
    access_token_expire_minutes: int =  30
    anthropic_api_key: str
    anthropic_model: str = "claude-sonnet-5-5"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()