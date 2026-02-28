
import os
from pydantic import AnyUrl
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
	service_name: str = "payment-service"
	environment: str = os.getenv("ENVIRONMENT", "local")

	database_url: AnyUrl = os.getenv(
		"DATABASE_URL",
		"postgres://brzina_user:changeme@postgres.brzina.svc.cluster.local:5432/brzina",
	)
	kafka_bootstrap_servers: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")

	class Config:
		env_file = ".env"

settings = Settings()
