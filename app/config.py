from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "TenderAI"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "sqlite:///./tender_ai.db"
    
    # Storage
    UPLOAD_DIR: str = "data/uploads"
    OCR_DIR: str = "data/ocr"
    NLP_DIR: str = "data/nlp"
    EVALUATION_DIR: str = "data/evaluation"
    HITL_DIR: str = "data/hitl"
    AUDIT_DIR: str = "data/audit"
    
    # OCR Settings (Placeholders for real integration)
    OCR_ENGINE: str = "mock"  # choices: mock, tesseract, azure, aws
    TESSERACT_CMD: Optional[str] = None
    AZURE_OCR_KEY: Optional[str] = None
    AZURE_OCR_ENDPOINT: Optional[str] = None
    
    # LLM Settings (Placeholders for real integration)
    LLM_PROVIDER: str = "gemini"  # choices: mock, openai, azure_openai, gemini
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4-turbo"
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-flash"
    
    # Data files
    CRITERIA_FILE: str = "data/criteria.json"

    # Security
    SECRET_KEY: str = "super-secret-key-for-development-only"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7 days

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

settings = Settings()
