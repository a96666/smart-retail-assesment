from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Azure OpenAI
    azure_openai_api_key: Optional[str] = None
    azure_openai_endpoint: Optional[str] = None
    azure_openai_deployment: str = "gpt-4o"
    azure_openai_api_version: str = "2024-02-01"
    azure_openai_embedding_deployment: str = "text-embedding-ada-002"

    # Azure AI Search (vector store for RAG)
    azure_search_endpoint: Optional[str] = None   # e.g. https://my-search.search.windows.net
    azure_search_api_key: Optional[str] = None
    azure_search_index_name: str = "retail-knowledge-base"

    # Azure Blob Storage (document source)
    azure_storage_connection_string: Optional[str] = None
    azure_blob_container: str = "smart-retail-ai"

    # Database – set DATABASE_URL to Neon PostgreSQL connection string in production
    # Local dev fallback: SQLite
    database_url: str = "sqlite+aiosqlite:///./data/retail.db"

    # App
    app_env: str = "development"
    log_level: str = "INFO"
    secret_key: str = "change-me-in-production"

    @property
    def use_azure_openai(self) -> bool:
        return bool(self.azure_openai_api_key and self.azure_openai_endpoint)

    @property
    def use_azure_search(self) -> bool:
        return bool(self.azure_search_endpoint and self.azure_search_api_key)

    @property
    def is_postgres(self) -> bool:
        return "postgresql" in self.database_url or "postgres" in self.database_url

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
