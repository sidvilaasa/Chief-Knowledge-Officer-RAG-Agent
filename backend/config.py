from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    openai_api_key: str
    tavily_api_key: str
    supabase_url: str
    supabase_service_key: str
    chroma_persist_dir: str = "./chroma_db"

    # Embedding / retrieval
    embedding_model: str = "text-embedding-3-small"
    chat_model: str = "gpt-4o-mini"
    retrieval_top_k: int = 3
    chunk_size: int = 1000
    chunk_overlap: int = 150


settings = Settings()
