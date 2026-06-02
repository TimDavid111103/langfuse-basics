from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    openai_api_key: str
    langfuse_public_key: str
    langfuse_secret_key: str
    langfuse_host: str = "http://localhost:3000"
    database_url: str
    uploads_dir: str = "./uploads"


settings = Settings()
