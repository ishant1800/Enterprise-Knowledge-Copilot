from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import logger
from app.core.database import init_db
from app.api.v1.endpoints import health, documents, chat, retrieval, evaluations

# Initialize SQLite tables
init_db()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.PROJECT_VERSION}")
    logger.info(f"OpenAI status: {'Configured' if settings.has_openai_key else 'Offline Fallback Mode'}")
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="Production-grade AI Knowledge Copilot using Retrieval-Augmented Generation (RAG) with grounded answers and strict hallucination prevention.",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception at {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please check logs for details."},
    )


# Mount API V1 routes
app.include_router(health.router, prefix=settings.API_V1_STR, tags=["Health"])
app.include_router(documents.router, prefix=f"{settings.API_V1_STR}/documents", tags=["Documents"])
app.include_router(chat.router, prefix=f"{settings.API_V1_STR}/chat", tags=["Chat"])
app.include_router(retrieval.router, prefix=f"{settings.API_V1_STR}/retrieval", tags=["Retrieval"])
app.include_router(evaluations.router, prefix=f"{settings.API_V1_STR}/eval", tags=["Evaluation"])


@app.get("/")
def root():
    return {
        "app": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION,
        "status": "online",
        "docs_url": "/docs",
        "openai_configured": settings.has_openai_key,
    }
