# import signal
# import sys
import os

from dotenv import load_dotenv
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Load environment variables from .env file
if os.path.exists(".env"):
    load_dotenv()
    print("Loaded environment variables from .env file")

from app.api.auth import router as auth_router
from app.api.feed import router as feed_router
from app.api.routes import router as news_router
from app.core.config import Settings
from app.db import models
from app.db.database import engine

# Get settings
settings = Settings()

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI-Powered News Aggregator",
    description="API for an AI-powered news aggregation service",
    version="0.1.0",
)


# Exception Handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Build a user‑friendly summary for every validation error we care about.
    """
    err_map = {}

    for err in exc.errors():
        field = err["loc"][-1]

        # 1) invalid e‑mail (any value_error on e‑mail field)
        if field == "email":
            err_map["email"] = "Invalid email address"

        # 2) short password
        elif field == "password" and err["type"] == "string_too_short":
            err_map["password"] = "Too short password"

    # If we recognised at least one specific problem – return them all
    if err_map:
        return JSONResponse(status_code=400, content={"message": err_map})

    # Fallback – something else went wrong
    return JSONResponse(status_code=400, content={"message": "Invalid input"})


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,  # Use configured origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(news_router)
app.include_router(feed_router)
app.include_router(auth_router)


@app.get(
    "/",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Root endpoint",
    description="Returns a welcome message for the API",
    tags=["Health"],
)
async def root():
    """
    Root endpoint for the API

    Returns:
        dict: A welcome message
    """
    return {"message": "Welcome to AI-Powered News Aggregator API"}


@app.get(
    "/health",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Health check endpoint",
    description="Returns the current health status of the API",
    tags=["Health"],
    responses={
        200: {
            "description": "API is healthy",
            "content": {"application/json": {"example": {"status": "ok"}}},
        },
        503: {
            "description": "API is unhealthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "error",
                        "details": "Database connection failed",
                    }
                }
            },
        },
    },
)
async def health_check():
    # Check Azure OpenAI credentials
    azure_openai_key = os.environ.get("AZURE_OPENAI_KEY", "")
    azure_openai_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT", "")
    openai_api_key = os.environ.get("OPENAI_API_KEY", "")

    ai_status = {
        "azure_openai_configured": bool(azure_openai_key and azure_openai_endpoint),
        "openai_configured": bool(openai_api_key),
    }

    return {"status": "ok", "ai_status": ai_status}


if __name__ == "__main__":
    import uvicorn

    # Use the host and port from settings
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
