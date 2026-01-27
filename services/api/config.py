import os

class Settings:
    service_name: str = "api-gateway"
    environment: str = os.getenv("ENVIRONMENT", "local")

settings = Settings()
