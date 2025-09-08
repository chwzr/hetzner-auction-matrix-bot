from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    This class is used to load environment variables from a .env file.
    """

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, frozen=True)

    matrix_homeserver: str = Field(..., alias="MATRIX_HOMESERVER")
    matrix_username: str = Field(..., alias="MATRIX_USERNAME")
    matrix_password: str = Field(..., alias="MATRIX_PASSWORD")
    mongodb_uri: str = Field(..., alias="MONGODB_URI")
    hetzner_notifications_room_id: str = Field(..., alias="HETZNER_NOTIFICATIONS_ROOM_ID")

settings: Settings = Settings()  # type: ignore[call-arg]
