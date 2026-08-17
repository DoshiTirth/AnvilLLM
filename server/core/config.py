"""Application configuration, loaded from environment variables / .env."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", protected_namespaces=("settings_",)
    )

    # llama.cpp server
    llama_server_host: str = "llama-server"
    llama_server_port: int = 8081
    model_path: str = "/models/llama-3.1-8b-instruct.Q4_K_M.gguf"
    context_size: int = 8192

    # API layer
    api_host: str = "0.0.0.0"
    api_port: int = 8080
    api_keys: str = ""  # comma-separated; empty disables auth (local dev default)
    rate_limit_per_minute: int = 60

    @property
    def api_key_list(self) -> list[str]:
        return [k.strip() for k in self.api_keys.split(",") if k.strip()]

    # RAG layer (wired up fully in feat/rag-layer)
    enable_rag: bool = False
    vector_store_path: str = "./data/vectorstore"
    web_search_api_key: str = ""
    web_search_provider: str = ""

    @property
    def llama_server_base_url(self) -> str:
        return f"http://{self.llama_server_host}:{self.llama_server_port}"


settings = Settings()
