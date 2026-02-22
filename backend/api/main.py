"""
FastAPI Application - Main Entry Point

Sets up the FastAPI server with:
- RFP processing endpoints
- Middleware and CORS configuration
- Health check and status endpoints
- Structured logging
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from backend.config import settings
from backend.data.embeddings_cache import vector_db
from backend.workflows.rfp_graph import create_rfp_processing_graph

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# ==================== STARTUP/SHUTDOWN EVENTS ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application startup and shutdown events.

    Startup:
    - Initialize FAISS vector DB
    - Compile LangGraph workflow
    - Log configuration

    Shutdown:
    - Clean up resources
    """
    # Startup
    logger.info("Starting RFP Processing API...")
    logger.info(f"LLM Provider: {settings.LLM_PROVIDER}")
    logger.info(f"Model: {settings.MODEL_NAME}")
    logger.info(f"FAISS Index: {settings.FAISS_INDEX_PATH}")

    # Initialize vector DB
    vector_db._initialize()
    if vector_db._is_ready:
        logger.info("FAISS vector DB initialized successfully")
    else:
        logger.warning("FAISS vector DB initialization failed. Using fuzzy matching.")

    # Compile workflow
    try:
        graph = create_rfp_processing_graph()
        logger.info("LangGraph workflow compiled successfully")
    except Exception as e:
        logger.error(f"Failed to compile workflow: {e}")

    logger.info("RFP Processing API started successfully")

    yield

    # Shutdown
    logger.info("Shutting down RFP Processing API...")


# ==================== APPLICATION FACTORY ====================

def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        Configured FastAPI instance
    """
    app = FastAPI(
        title="Agentic RFP Bidding Engine",
        description="Multi-Agent LangGraph system for automated RFP processing",
        version="1.0.0",
        lifespan=lifespan,
    )

    # ==================== MIDDLEWARE ====================

    # CORS Configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, specify allowed origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ==================== BASIC ENDPOINTS ====================

    @app.get("/health")
    async def health_check():
        """Basic health check endpoint."""
        return {
            "status": "healthy",
            "service": "RFP Processing API",
            "version": "1.0.0",
            "vector_db_ready": vector_db._is_ready,
        }

    @app.get("/api/config")
    async def get_configuration():
        """
        Return current system configuration.

        Useful for debugging and verification.
        """
        return {
            "llm": {
                "provider": settings.LLM_PROVIDER,
                "model": settings.MODEL_NAME,
                "temperature": settings.LLM_TEMPERATURE,
                "max_tokens": settings.MAX_TOKENS,
            },
            "vector_db": {
                "ready": vector_db._is_ready,
                "embeddings_model": settings.EMBEDDINGS_MODEL,
                "index_path": settings.FAISS_INDEX_PATH,
            },
            "processing": {
                "smm_threshold": settings.SMM_COMPLIANCE_THRESHOLD,
                "max_retries": settings.TECHNICAL_MAX_RETRIES,
                "size_tolerance_relaxation": settings.SIZE_TOLERANCE_RELAXATION,
                "rfp_qualification_window_days": settings.RFP_QUALIFICATION_WINDOW_DAYS,
            },
            "pricing": {
                "target_margin": settings.TARGET_MARGIN,
                "usd_to_inr_rate": settings.USD_TO_INR_RATE,
            },
        }

    return app


# ==================== APPLICATION INSTANCE ====================

app = create_app()

# Import routes (this adds them to the app)
from backend.api import routes  # noqa: E402, F401

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=settings.API_HOST,
        port=settings.API_PORT,
        log_level="info",
    )


# ==================== EXPORT ====================
__all__ = ["app", "create_app"]
