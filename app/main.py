from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from contextlib import asynccontextmanager

from app.core.config import settings
from app.api.v1.api import api_router
from app.core.exceptions import CustomException


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting up the application...")
    yield
    # Shutdown
    print("Shutting down the application...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="A modern FastAPI backend application",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.exception_handler(CustomException)
async def custom_exception_handler(request, exc: CustomException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.get("/")
async def root():
    return {"message": "Welcome to the FastAPI Backend API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.VERSION}


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
