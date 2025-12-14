from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
        
    )
    
    # Application
    PROJECT_NAME: str = "Online Store API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    
    # Database
    DATABASE_URL: str
    DB_NAME: str = "iron_brothers_db"

    # CORS
    BACKEND_CORS_ORIGINS: str = "http://localhost:5173"

    # api key
    GOOGLE_API_KEY: str
    
    """
    @field_validator('BACKEND_CORS_ORIGINS', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v
    """
    

settings = Settings()