"""RAG agent for turning client requirements into Fal deployment blueprints."""

from __future__ import annotations

import ast
import hashlib
import os
import re
from collections import OrderedDict
from pathlib import Path
from typing import List

os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

from dotenv import load_dotenv
from chromadb.config import Settings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from pydantic import BaseModel, Field

CHROMA_COLLECTION = "dealforge_docs"
DEFAULT_FAST_CHAT_MODEL = "gemini-3-flash-preview"
DEFAULT_CHAT_MODEL = "gemini-2.5-pro"
DEFAULT_EMBEDDING_MODEL = "models/gemini-embedding-001"
DEFAULT_CHROMA_DIR = "chroma_db"
RETRIEVAL_K = 3  # Fewer chunks = smaller context, faster LLM
MAX_GENERATION_ATTEMPTS = 3
RESULT_CACHE_SIZE = 128

_vector_store: Chroma | None = None
_llms: dict[str, ChatGoogleGenerativeAI] = {}
_result_cache: OrderedDict[str, BlueprintResult] = OrderedDict()

SYSTEM_PROMPT = """You are an elite Forward Deployed Engineer at Fal.ai.
You read client emails and generate exact, flawless Python scripts using fal.App and DistributedRunner.
You ONLY output valid Python code and a brief explanation.
You never hallucinate APIs. Use the retrieved context.

Hard requirements:
- Define the deployment as a `class ... (fal.App)`.
- Use `@fal.endpoint("/")` for the public endpoint.
- Use `ContainerImage.from_dockerfile_str(...)` when a custom container is needed.
- Use `machine_type = "GPU-H100"` and `num_gpus = ...` when the client asks for multi-H100 scale.
- Use `DistributedRunner` and `DistributedWorker` for distributed execution.
- Use documented worker properties such as `self.device`, `self.rank`, and `self.world_size`.
- Do not use undocumented decorators or attributes such as `@fal.app` or `self.worker_id`.
- If the retrieved docs do not show a combined example, compose the final code only from the documented pieces above.

Return your answer in exactly this format:
EXPLANATION:
<one short paragraph>

```python
<valid python code only>
```

README:
```markdown
# Deployment

## Prerequisites
- Save the script as `app.py` (or the filename you used).
- Install fal CLI: `pip install fal`.
- Log in: `fal auth login`.

## Run (test locally on fal)
fal run app.py::<YourAppClassName> --auth private

## Deploy (production)
fal deploy app.py::<YourAppClassName> --auth private
```
Use the actual app class name from your code in the README commands."""


class DealforgeError(RuntimeError):
    """Base exception for user-safe agent failures."""


class BlueprintResult(BaseModel):
    code: str = Field(..., description="Validated Python deployment script.")
    explanation: str = Field(..., description="Short explanation of the design choices.")
    readme: str = Field(default="", description="README with fal run / fal deploy CLI commands.")


def _project_root() -> Path:
    return Path(__file__).resolve().parent


def _get_env(var_name: str) -> str:
    value = os.getenv(var_name)
    if value:
        return value
    raise DealforgeError(
        f"Missing required environment variable `{var_name}`. "
        "Set it before generating a blueprint."
    )


def _get_google_api_key() -> str:
    return os.getenv("GOOGLE_API_KEY") or _get_env("GEMINI_API_KEY")


def _build_vector_store() -> Chroma:
    global _vector_store
    if _vector_store is not None:
        return _vector_store
    chroma_dir = Path(os.getenv("CHROMA_DB_DIR", str(_project_root() / DEFAULT_CHROMA_DIR)))
    if not chroma_dir.exists():
        raise DealforgeError(
            f"Chroma database not found at `{chroma_dir}`. Run `python ingest.py` first."
        )
    embedding_model = os.getenv("DEALFORGE_EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL)
    embeddings = GoogleGenerativeAIEmbeddings(
        model=embedding_model,
        google_api_key=_get_google_api_key(),
    )
    _vector_store = Chroma(
        collection_name=CHROMA_COLLECTION,
        persist_directory=str(chroma_dir),
        embedding_function=embeddings,
        client_settings=Settings(
            anonymized_telemetry=False,
            chroma_product_telemetry_impl="dealforge_chroma.NoOpProductTelemetry",
        ),
    )
    return _vector_store


def _build_llm(model_name: str) -> ChatGoogleGenerativeAI:
    llm = _llms.get(model_name)
    if llm is not None:
        return llm
    llm = ChatGoogleGenerativeAI(
        model=model_name,
        temperature=0.2,
        google_api_key=_get_google_api_key(),
    )
    _llms[model_name] = llm
    return llm


def _candidate_models() -> list[str]:
    primary = os.getenv("DEALFORGE_FAST_CHAT_MODEL", DEFAULT_FAST_CHAT_MODEL)
    fallback = os.getenv("DEALFORGE_CHAT_MODEL", DEFAULT_CHAT_MODEL)
    if primary == fallback:
        return [primary]
    return [primary, fallback]


def _cache_key(client_email: str) -> str:
    normalized = re.sub(r"\s+", " ", client_email.strip())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _get_cached_result(client_email: str) -> BlueprintResult | None:
    key = _cache_key(client_email)
    result = _result_cache.get(key)
    if result is None:
        return None
    _result_cache.move_to_end(key)
    return result


def _store_cached_result(client_email: str, result: BlueprintResult) -> None:
    key = _cache_key(client_email)
    _result_cache[key] = result
    _result_cache.move_to_end(key)
    while len(_result_cache) > RESULT_CACHE_SIZE:
        _result_cache.popitem(last=False)


def _format_docs(documents: List[Document]) -> str:
    return "\n\n".join(
        f"Source: {Path(doc.metadata.get('source', 'unknown')).name}\n{doc.page_content}"
        for doc in documents
    )


def _retrieve_context(client_email: str) -> List[Document]:
    vector_store = _build_vector_store()
    k = int(os.getenv("DEALFORGE_RETRIEVAL_K", RETRIEVAL_K))
    retriever = vector_store.as_retriever(search_kwargs={"k": k})
    documents = retriever.invoke(client_email)

    if not documents:
        raise DealforgeError(
            "No relevant Fal.ai documentation was retrieved. Re-run ingestion or refine the prompt."
        )

    return documents


def _extract_app_class_name(code: str) -> str | None:
    """First class that subclasses fal.App."""
    for m in re.finditer(r"class\s+(\w+)\s*\([^)]*fal\.App", code):
        return m.group(1)
    return None


def _default_readme(code: str) -> str:
    """Fallback README with fal run / fal deploy using detected app class."""
    app_class = _extract_app_class_name(code) or "MyApp"
    return f"""# Deployment

## Prerequisites
- Save the script as `app.py`. Install fal: `pip install fal`. Log in: `fal auth login`.

## Run (test)
```bash
fal run app.py::{app_class} --auth private
```

## Deploy (production)
```bash
fal deploy app.py::{app_class} --auth private
```
"""


def _parse_response(raw_text: str) -> BlueprintResult:
    code_match = re.search(r"```python\s*(.*?)```", raw_text, re.DOTALL | re.IGNORECASE)
    if not code_match:
        raise DealforgeError(
            "The model response did not include a Python code block. Try again."
        )

    code = code_match.group(1).strip()
    explanation_text = re.sub(r"```python\s*.*?```", "", raw_text, flags=re.DOTALL | re.IGNORECASE)
    explanation_text = explanation_text.replace("EXPLANATION:", "").strip()
    # Stop at README / markdown block so explanation is only the short paragraph
    if "README:" in explanation_text:
        explanation_text = explanation_text.split("README:")[0].strip()
    if "```markdown" in explanation_text:
        explanation_text = explanation_text.split("```markdown")[0].strip()
    explanation = explanation_text or "Generated from the retrieved Fal.ai implementation notes."

    readme = ""
    md_match = re.search(r"README:\s*```markdown\s*(.*?)```", raw_text, re.DOTALL | re.IGNORECASE)
    if md_match:
        readme = md_match.group(1).strip()
    if not readme:
        readme = _default_readme(code)

    return BlueprintResult(code=code, explanation=explanation, readme=readme)


def _validate_python(code: str) -> None:
    try:
        ast.parse(code)
    except SyntaxError as exc:  # pragma: no cover - small wrapper
        raise DealforgeError(
            f"Generated Python failed AST validation at line {exc.lineno}: {exc.msg}"
        ) from exc


def _validate_fal_contract(code: str) -> None:
    required_snippets = [
        "fal.App",
        '@fal.endpoint("/")',
        "DistributedRunner",
        "DistributedWorker",
    ]
    banned_snippets = [
        "@fal.app",
        "worker_id",
    ]

    missing = [snippet for snippet in required_snippets if snippet not in code]
    if missing:
        raise DealforgeError(
            "Generated Python is missing required Fal constructs: "
            + ", ".join(missing)
        )

    present_banned = [snippet for snippet in banned_snippets if snippet in code]
    if present_banned:
        raise DealforgeError(
            "Generated Python used undocumented Fal constructs: "
            + ", ".join(present_banned)
        )


def _invoke_generation(
    client_email: str,
    context: str,
    model_name: str,
    feedback: str | None = None,
) -> BlueprintResult:
    llm = _build_llm(model_name)

    human_prompt = f"""Client email:
{client_email}

Retrieved Fal.ai context:
{context}

Requirements:
- Ground the script in the retrieved APIs only.
- Generate a production-ready Fal deployment script that uses distributed H100 inference when relevant.
- Include custom container setup when the client asks for Dockerfile-level dependencies.
- Keep the explanation brief.
- Output a README section (see format above) with the exact CLI commands: fal run and fal deploy with --auth private, using the actual app class name from your code.
"""
    if feedback:
        human_prompt += f"\nPrevious attempt failed AST validation. Fix the script using this parser feedback:\n{feedback}\n"

    response = llm.invoke(
        [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=human_prompt),
        ]
    )

    raw_text = getattr(response, "content", response)
    if isinstance(raw_text, list):
        raw_text = "\n".join(
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in raw_text
        )

    return _parse_response(str(raw_text))


def generate_fal_blueprint_with_notes(client_email: str) -> BlueprintResult:
    """Generate a validated blueprint and a short explanation for the UI."""
    load_dotenv(dotenv_path=_project_root() / ".env")

    if not client_email or not client_email.strip():
        raise DealforgeError("Client requirements cannot be empty.")

    cached_result = _get_cached_result(client_email)
    if cached_result is not None:
        return cached_result

    _get_google_api_key()
    documents = _retrieve_context(client_email)
    context = _format_docs(documents)
    model_candidates = _candidate_models()

    last_error = None
    for attempt in range(MAX_GENERATION_ATTEMPTS):
        model_name = model_candidates[min(attempt, len(model_candidates) - 1)]
        result = _invoke_generation(
            client_email=client_email.strip(),
            context=context,
            model_name=model_name,
            feedback=last_error,
        )
        try:
            _validate_python(result.code)
            _validate_fal_contract(result.code)
            _store_cached_result(client_email, result)
            return result
        except DealforgeError as exc:
            last_error = str(exc)
    raise DealforgeError(
        "The model repeatedly produced invalid Python after AST validation retries. "
        "Try again or rephrase your requirements; you can also use the sample request and then edit it."
    )


def generate_fal_blueprint(client_email: str) -> str:
    """Generate AST-valid Python code only."""

    return generate_fal_blueprint_with_notes(client_email).code
