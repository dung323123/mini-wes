from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str
    CORS_ORIGINS: str = "http://127.0.0.1:5173,http://localhost:5173,http://0.0.0.0:5173"
    CORS_ORIGIN_REGEX: str = r"https://.*\.vercel\.app"


settings = Settings()
