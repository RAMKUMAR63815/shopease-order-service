
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application settings
    APP_NAME: str = "ShopEase Order Management Service"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    # MySQL database settings
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 3306
    DATABASE_USER: str = "root"
    DATABASE_PASSWORD: str
    DATABASE_NAME: str = "shopease_order_db"

    # Other microservice URLs
    AUTH_SERVICE_URL: str
    USER_SERVICE_URL: str
    PRODUCT_SERVICE_URL: str
    # Internal service authentication token
    INTERNAL_SERVICE_TOKEN: str

    # Read values from the .env file
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",#support all character
        extra="ignore"
    )


settings = Settings()
