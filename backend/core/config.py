from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    amazon_access_key: str = ""
    amazon_secret_key: str = ""
    amazon_partner_tag: str = ""
    amazon_host: str = "webservices.amazon.com"
    keepa_api_key: str = ""
    database_url: str = "postgresql+asyncpg://tracker:tracker@localhost:5432/amazon_tracker"
    redis_url: str = "redis://localhost:6379/0"
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    telegram_bot_token: str = ""
    vapid_private_key: str = ""
    vapid_public_key: str = ""
    vapid_claim_email: str = ""


settings = Settings()
