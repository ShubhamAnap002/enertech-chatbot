from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Engyne"
    app_env: str = "development"
    debug: bool = True
    secret_key: str = "change-me-to-a-long-random-string"
    access_token_expire_minutes: int = 480
    device_token_expire_days: int = 365

    database_url: str = "sqlite:///./engyne.db"
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # Supabase metadata / future API usage (app DB uses database_url)
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    supabase_jwt_secret: str = ""
    supabase_project_ref: str = ""
    supabase_db_host: str = ""
    supabase_db_port: str = "6543"
    supabase_db_name: str = "postgres"
    supabase_db_user: str = "postgres"
    supabase_db_password: str = ""

    admin_email: str = "admin@engyne.example"
    admin_password: str = "changeme123"

    email_provider: str = "console"
    email_from: str = "noreply@engyne.local"
    admin_report_email: str = "ops@engyne.local"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""

    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    razorpay_webhook_secret: str = ""

    invoice_prefix: str = "ENGY"
    tax_rate_percent: float = 18.0
    company_name: str = "Engyne"
    company_address: str = ""
    company_gstin: str = ""

    redis_url: str = ""

    refresh_interval_min: int = 15
    refresh_interval_max: int = 300

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
