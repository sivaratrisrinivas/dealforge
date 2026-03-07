"""Ingest local markdown documentation into a persisted Chroma collection."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

# Disable Chroma telemetry in build/runtime ingestion paths.
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

from dotenv import load_dotenv
from chromadb.config import Settings
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

CHROMA_COLLECTION = "dealforge_docs"
DEFAULT_EMBEDDING_MODEL = "models/gemini-embedding-001"
DEFAULT_DOCS_DIR = "fal_docs"

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logging.getLogger("chromadb.telemetry.product.posthog").disabled = True
logging.getLogger("google_genai.models").setLevel(logging.WARNING)
logging.getLogger("google_genai._api_client").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)


def _require_env(var_name: str) -> str:
    value = os.getenv(var_name)
    if value:
        return value

    message = (
        f"Missing required environment variable `{var_name}`. "
        "Set it before running ingestion."
    )
    raise RuntimeError(message)


def _get_google_api_key() -> str:
    return os.getenv("GOOGLE_API_KEY") or _require_env("GEMINI_API_KEY")


def ingest_documents() -> None:
    project_root = Path(__file__).resolve().parent
    load_dotenv(dotenv_path=project_root / ".env")
    docs_dir = Path(os.getenv("DEALFORGE_DOCS_DIR", str(project_root / DEFAULT_DOCS_DIR)))
    chroma_dir = Path(os.getenv("CHROMA_DB_DIR", str(project_root / "chroma_db")))
    embedding_model = os.getenv("DEALFORGE_EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL)

    api_key = _get_google_api_key()

    if not docs_dir.exists():
        raise RuntimeError(f"Documentation directory not found: {docs_dir}")

    loader = DirectoryLoader(
        str(docs_dir),
        glob="*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    )
    documents = loader.load()
    if not documents:
        raise RuntimeError(f"No markdown documents found in {docs_dir}")

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(documents)

    embeddings = GoogleGenerativeAIEmbeddings(
        model=embedding_model,
        google_api_key=api_key,
    )
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=CHROMA_COLLECTION,
        persist_directory=str(chroma_dir),
        client_settings=Settings(
            anonymized_telemetry=False,
            chroma_product_telemetry_impl="dealforge_chroma.NoOpProductTelemetry",
        ),
    )

    count = vector_store._collection.count()
    print(
        "Ingestion complete.",
        f"Loaded {len(documents)} docs into {len(chunks)} chunks.",
        f"Chroma collection `{CHROMA_COLLECTION}` now contains {count} records at {chroma_dir}.",
    )


if __name__ == "__main__":
    try:
        ingest_documents()
    except Exception as exc:  # pragma: no cover - CLI entrypoint
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
