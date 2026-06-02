from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import create_db_and_tables
from app.routers import evaluation, experiments
from app.tracing.langfuse_client import flush_langfuse


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await create_db_and_tables()
    yield
    flush_langfuse()


app = FastAPI(title="Pensive — RAG Rubric Evaluation", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(experiments.router, prefix="/api/v1", tags=["experiments"])
app.include_router(evaluation.router, prefix="/api/v1", tags=["evaluation"])


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
