from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str
    chat_room_link: str
    chat_room_code: str
    time_tolerance_minutes: int = 10
    model: str = "claude-haiku-4-5-20251001"
    admin_user_key: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
