from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time

from app.config import settings
from app.database import init_db
from app.core.exceptions import AsanaAPIException
from app.api.v1 import router as api_v1_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    await init_db()
    yield
    # Shutdown
    pass


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="A backend service replicating core Asana API functionalities",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add X-Process-Time header to responses."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.exception_handler(AsanaAPIException)
async def asana_exception_handler(request: Request, exc: AsanaAPIException):
    """Handle Asana-style API exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "errors": [
                {
                    "message": exc.message,
                    "help": exc.help_text,
                    "phrase": exc.phrase,
                }
            ]
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    return JSONResponse(
        status_code=500,
        content={
            "errors": [
                {
                    "message": "Internal server error",
                    "help": "An unexpected error occurred. Please try again later.",
                    "phrase": "internal_error",
                }
            ]
        },
    )


# Include API routers
app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Asana Backend Replica API",
        "docs": "/docs",
        "api_version": "1.0",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

