import os
from pydantic import BaseSettings, AnyUrl


class Settings(BaseSettings):
    service_name: str = "booking-service"
    environment: str = os.getenv("ENVIRONMENT", "local")

    database_url: AnyUrl = os.getenv(
        "DATABASE_URL",
        "postgres://carshare_user:changeme@postgres.carshare.svc.cluster.local:5432/carshare",
    )
    kafka_bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")

    class Config:
        env_file = ".env"

settings = Settings()