from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router as news_router
from app.db.database import engine
from app.db import models

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI-Powered News Aggregator",
    description="API for an AI-powered news aggregation service",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Modify in production to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(news_router)

@app.get(
    "/", 
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Root endpoint",
    description="Returns a welcome message for the API",
    tags=["Health"]
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
            "content": {
                "application/json": {
                    "example": {"status": "ok"}
                }
            }
        },
        503: {
            "description": "API is unhealthy",
            "content": {
                "application/json": {
                    "example": {"status": "error", "details": "Database connection failed"}
                }
            }
        }
    }
)
async def health_check():
    """
    Check the health status of the API
    
    This endpoint can be used by monitoring services to check
    if the API is up and running properly.
    
    Returns:
        dict: Health status information
    """
    # In a real-world scenario, you might check database connections,
    # external services, etc. before returning a health status
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 