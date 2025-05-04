from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import signal
import sys

from app.api.routes import router as news_router
from app.api.feed import router as feed_router
from app.api.auth import router as auth_router
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
app.include_router(feed_router)
app.include_router(auth_router)

@app.get("/")
async def root():
    return {"message": "Welcome to AI-Powered News Aggregator API"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 

# Handle termination signal
def signal_handler(sig, frame):
    print("Stopping applications...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)