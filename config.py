import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    APP_NAME: str = "Vajra"
    APP_SUBTITLE: str = "Drone Service Management"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./vajra.db",
    )
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    ITEMS_PER_PAGE: int = int(os.getenv("ITEMS_PER_PAGE", "20"))


settings = Settings()
