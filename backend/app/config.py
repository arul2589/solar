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

    # document knowledge base (RAG) - OpenAI
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_chat_model: str = "gpt-5.4-mini"
    openai_vision_model: str = "gpt-5.4-mini"
    openai_embed_model: str = "text-embedding-3-small"
    openai_embed_dims: int = 512

    access_token_minutes: int = 60 * 12

    @property
    def is_dev(self) -> bool:
        """Dev helpers (OTP codes in API responses, API docs, links in responses) are on only for tests and
        for development on a local address - never on a real domain, even if ENVIRONMENT was left unset."""
        if self.environment == "test":
            return True
        if self.environment != "development":
            return False
        from urllib.parse import urlparse
        host = (urlparse(self.public_base_url).hostname or "").lower()
        return host in ("localhost", "127.0.0.1", "::1") or host.endswith((".localhost", ".test", ".local"))

    def production_problems(self) -> list[str]:
        """Settings that must be changed before the site is put on the internet."""
        probs = []
        weak = {"dev-secret-change-me", "dev-only-secret-key-change-me-0123456789abcdef",
                "change-me-to-a-long-random-string-at-least-32-chars"}
        if self.secret_key in weak or len(self.secret_key) < 32:
            probs.append("SECRET_KEY is a default or shorter than 32 characters")
        if "solar-dev-password" in self.database_url or ":change-me@" in self.database_url:
            probs.append("POSTGRES_PASSWORD is the default value")
        if not self.public_base_url.startswith("https://"):
            probs.append("PUBLIC_BASE_URL must start with https://")
        return probs


@lru_cache
def get_config() -> Config:
    return Config()
