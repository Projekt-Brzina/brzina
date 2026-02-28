import os
from pydantic import AnyUrl
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    service_name: str = "auth-service"
    environment: str = os.getenv("ENVIRONMENT", "local")

    database_url: AnyUrl = os.getenv(
        "DATABASE_URL",
        "postgres://brzina_user:changeme@postgres.brzina.svc.cluster.local:5432/brzina",
    )

    jwt_secret: str = os.getenv("JWT_SECRET", "supersecret")
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60

    class Config:
        env_file = ".env"


settings = Settings()