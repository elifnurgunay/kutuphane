from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Ortam değişkenlerinden okunan altyapı ayarları.

    İş kuralı değerleri (ödünç süresi, ceza tutarı vb.) burada değil,
    veritabanındaki `settings` tablosunda tutulur.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Kütüphane Otomasyon Sistemi"
    database_url: str = "sqlite:///./kutuphane.db"
    cors_origins: list[str] = ["http://localhost:5173"]


settings = Settings()
