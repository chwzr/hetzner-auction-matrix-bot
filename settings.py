from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    This class is used to load environment variables from a .env file.
    """

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, frozen=True)

    bot_token: str | None = Field(None, alias="BOT_TOKEN")
    mongodb_uri: str | None = Field(None, alias="MONGODB_URI")
    hetzner_notifications_channel_id: int | None = Field(None, alias="HETZNER_NOTIFICATIONS_CHANNEL_ID")

settings: Settings = Settings()  # type: ignore[call-arg]
