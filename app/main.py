from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError as PydanticValidationError
import time

from app.config import settings
from app.database import init_db
from app.core.exceptions import AsanaAPIException, RateLimitError
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


@app.exception_handler(RateLimitError)
async def rate_limit_exception_handler(request: Request, exc: RateLimitError):
    """Handle rate limit exceptions with Retry-After header."""
    return JSONResponse(
        status_code=exc.status_code,
        headers={"Retry-After": str(exc.retry_after)},
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


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle FastAPI/Pydantic validation errors in Asana format."""
    errors = exc.errors()
    
    # Build Asana-style error messages
    error_messages = []
    for error in errors:
        loc = error.get("loc", [])
        msg = error.get("msg", "Validation error")
        field = ".".join(str(l) for l in loc if l != "body")
        
        if field:
            error_messages.append(f"{field}: {msg}")
        else:
            error_messages.append(msg)
    
    return JSONResponse(
        status_code=400,
        content={
            "errors": [
                {
                    "message": "; ".join(error_messages) if error_messages else "Invalid request",
                    "help": "For more information on API status codes and how to handle them, read the docs on errors: https://developers.asana.com/docs/errors",
                    "phrase": "invalid_request",
                }
            ]
        },
    )


@app.exception_handler(PydanticValidationError)
async def pydantic_validation_exception_handler(request: Request, exc: PydanticValidationError):
    """Handle Pydantic validation errors (from manual model instantiation) in Asana format."""
    errors = exc.errors()
    
    # Build Asana-style error messages
    error_messages = []
    for error in errors:
        msg = error.get("msg", "Validation error")
        # Clean up the message - remove "Value error, " prefix if present
        if msg.startswith("Value error, "):
            msg = msg[13:]
        error_messages.append(msg)
    
    return JSONResponse(
        status_code=400,
        content={
            "errors": [
                {
                    "message": "; ".join(error_messages) if error_messages else "Invalid request",
                    "help": "For more information on API status codes and how to handle them, read the docs on errors: https://developers.asana.com/docs/errors",
                    "phrase": "invalid_request",
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
                    "message": "Server Error",
                    "help": "An unexpected error occurred. Please try again later. If the problem persists, contact support.",
                    "phrase": "server_error",
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


