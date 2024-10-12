from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    database_hostname: str
    database_port: str
    database_password: str
    database_name: str
    database_username: str
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    AWS_SERVER_PUBLIC_KEY: str
    AWS_SERVER_SECRET_KEY: str
    google_client_id: str
    google_client_secret: str
    redirect_uri: str
    # mail_pass: str



    class Config:
        env_file = Path("C:/Users/HP/Desktop/tvs_rto/.env")

settings = Settings(_env_file=Path("C:/Users/HP/Desktop/tvs_rto/.env"), _env_file_encoding="utf-8")