from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Project metadata
    PROJECT_NAME: str = "Enterprise Knowledge Copilot"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # OpenAI configuration
    OPENAI_API_KEY: str = ""
    OPENAI_CHAT_MODEL: str = "gpt-4o-mini"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

    # Storage paths
    CHROMA_PERSIST_DIRECTORY: str = str(BASE_DIR / "data" / "chromadb")
    CHROMA_COLLECTION_NAME: str = "enterprise_knowledge"
    DATABASE_URL: str = f"sqlite:///{BASE_DIR}/data/copilot.db"
    UPLOAD_DIRECTORY: str = str(BASE_DIR / "data" / "uploads")
    SAMPLE_DOCS_DIRECTORY: str = str(BASE_DIR / "data" / "sample_docs")

    # Ingestion params
    DEFAULT_CHUNK_SIZE: int = 800
    DEFAULT_CHUNK_OVERLAP: int = 150
    MAX_UPLOAD_SIZE_MB: int = 25

    # Retrieval params
    TOP_K_RETRIEVAL: int = 6
    SIMILARITY_THRESHOLD: float = 0.20
    ENABLE_RERANKING: bool = True

    # Server & CORS
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    @property
    def has_openai_key(self) -> bool:
        return bool(self.OPENAI_API_KEY and self.OPENAI_API_KEY.strip() and not self.OPENAI_API_KEY.startswith("your_"))


settings = Settings()
