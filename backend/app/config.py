from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./dev.sqlite3"
    secret_key: str = "dev-secret-change-me"
    environment: str = "development"           # development | production | test
    public_base_url: str = "http://localhost:8088"   # used in email links
    storage_dir: str = "./storage"
    default_installer_slug: str = "demo"

    # email
    email_provider: str = "log"                 # log | resend | brevo
    resend_api_key: str = ""
    brevo_api_key: str = ""
    email_send_inline: bool = True              # try to send right after queueing
    email_max_attempts: int = 5

    # sms / otp
    sms_provider: str = "log"                   # log only for now (no SMS credentials yet)
    otp_ttl_minutes: int = 10

    # public form protection
    public_rate_limit_per_hour: int = 10

    # vision model for bill-photo reading (Phase 3)
    anthropic_api_key: str = ""
    bill_reader_model: str = "claude-opus-5-5"

    access_token_minutes: int = 60 * 12

    @property
    def is_dev(self) -> bool:
        return self.environment in ("development", "test")


@lru_cache
def get_config() -> Config:
    return Config()
