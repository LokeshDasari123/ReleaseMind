import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / ".env")


class Settings:
    # Any OpenAI-compatible provider key works here (for example, a Groq key).
    llm_api_key = os.getenv("LLM_API_KEY", os.getenv("OPENAI_API_KEY", ""))
    llm_base_url = os.getenv("LLM_BASE_URL", "").strip() or None
    llm_model = os.getenv("LLM_MODEL", "gpt-4o-mini")
    database_path = Path(os.getenv("DATABASE_PATH", str(ROOT_DIR / "data" / "releasemind.sqlite3")))
    retrieval_provider = os.getenv("RETRIEVAL_PROVIDER", "local").lower()
    hindsight_base_url = os.getenv("HINDSIGHT_BASE_URL", "").rstrip("/")
    hindsight_api_key = os.getenv("HINDSIGHT_API_KEY", "")
    hindsight_bank_id = os.getenv("HINDSIGHT_BANK_ID", "releasemind")
    cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")

    @property
    def hindsight_enabled(self) -> bool:
        return self.retrieval_provider == "hindsight" and bool(self.hindsight_base_url)


settings = Settings()
