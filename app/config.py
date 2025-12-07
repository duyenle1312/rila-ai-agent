from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GEMINI_API_KEY: str = ""
    NOTION_API_KEY: str
    NOTION_PARENT_PAGE: str
    BREVO_API_KEY: str = ""
    BREVO_SENDER_EMAIL: str = ""
    EMAIL_TO: str = ""
    GEMINI_AI_MODEL: str = "gemini-2.5-flash-lite"

    class Config:
        env_file = ".env"


settings = Settings()