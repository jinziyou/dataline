"""应用配置，通过环境变量加载"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "DATALINE_"}

    APP_NAME: str = "DataLine Server"
    DEBUG: bool = False

    DATABASE_URL: str = "postgresql://dataline:dataline@localhost:5432/dataline"

    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    PREFECT_API_URL: str = "http://localhost:4200/api"


settings = Settings()
