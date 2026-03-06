"""FastAPI backend: serves static UI and /api/generate for blueprint generation."""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from agent import DealforgeError, generate_fal_blueprint_with_notes

load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

app = FastAPI(title="Dealforge", docs_url=None, redoc_url=None)

STATIC_DIR = Path(__file__).resolve().parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class GenerateRequest(BaseModel):
    client_email: str = Field(..., min_length=1)


class GenerateResponse(BaseModel):
    code: str
    explanation: str
    readme: str


@app.post("/api/generate", response_model=GenerateResponse)
def api_generate(body: GenerateRequest) -> GenerateResponse:
    try:
        result = generate_fal_blueprint_with_notes(body.client_email.strip())
        return GenerateResponse(
            code=result.code,
            explanation=result.explanation,
            readme=result.readme,
        )
    except DealforgeError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected failure while generating the blueprint: {e}",
        )


@app.get("/")
def index() -> FileResponse:
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Static files not found")
    return FileResponse(index_path, media_type="text/html")
