import os
from pydantic import BaseSettings, AnyUrl


class Settings(BaseSettings):
    service_name: str = os.getenv("SERVICE_NAME", "template-service")
    environment: str = os.getenv("ENVIRONMENT", "local")

    database_url: AnyUrl = os.getenv(
        "DATABASE_URL",
        "postgres://carshare_user:changeme@postgres.carshare.svc.cluster.local:5432/carshare",
    )

    # For auth-enabled services you can add:
    # jwt_public_key: str | None = os.getenv("JWT_PUBLIC_KEY")
    # or jwt_secret: str | None = os.getenv("JWT_SECRET")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()