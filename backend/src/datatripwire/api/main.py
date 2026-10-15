"""Main FastAPI application entry point for DataTripwire.

Configures application routes, CORS middleware, global exception handlers,
and OpenAPI documentation.
"""

import logging
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from datatripwire.api.routes import datasets, domains, evaluations, health
from datatripwire.config import settings
from datatripwire.exceptions import (
    DatasetNotFoundError,
    DataTripwireError,
    EvaluationNotFoundError,
    FileTooLargeError,
    IncompatibleSchemaError,
    InvalidCSVError,
    LimitExceededError,
    MutationApplicationError,
    StorageCorruptedError,
)

# Configure server-side logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("datatripwire.api")


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    app = FastAPI(
        title=f"{settings.app_name} API",
        version=settings.app_version,
        description=(
            "A data-pipeline crash-testing platform that evaluates whether existing "
            "data-quality safeguards can detect realistic, synthetic data faults."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # 1. CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 2. Domain Exception Handlers
    @app.exception_handler(DatasetNotFoundError)
    async def dataset_not_found_handler(request: Request, exc: DatasetNotFoundError):
        logger.warning(f"Dataset not found: {exc.dataset_id} at {request.url.path}")
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": "Dataset Not Found", "detail": exc.message, "code": exc.code},
        )

    @app.exception_handler(EvaluationNotFoundError)
    async def evaluation_not_found_handler(request: Request, exc: EvaluationNotFoundError):
        logger.warning(f"Evaluation not found: {exc.evaluation_id} at {request.url.path}")
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": "Evaluation Not Found", "detail": exc.message, "code": exc.code},
        )

    @app.exception_handler(FileTooLargeError)
    async def file_too_large_handler(request: Request, exc: FileTooLargeError):
        logger.warning(f"Upload rejected - file too large: {exc.message}")
        return JSONResponse(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            content={"error": "File Too Large", "detail": exc.message, "code": exc.code},
        )

    @app.exception_handler(InvalidCSVError)
    async def invalid_csv_handler(request: Request, exc: InvalidCSVError):
        logger.warning(f"Invalid CSV uploaded: {exc.message}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Invalid CSV", "detail": exc.message, "code": exc.code},
        )

    @app.exception_handler(LimitExceededError)
    async def limit_exceeded_handler(request: Request, exc: LimitExceededError):
        logger.warning(f"Data limit exceeded: {exc.message}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"error": "Limit Exceeded", "detail": exc.message, "code": exc.code},
        )

    @app.exception_handler(IncompatibleSchemaError)
    async def incompatible_schema_handler(request: Request, exc: IncompatibleSchemaError):
        logger.warning(f"Incompatible schema: {exc.message}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"error": "Incompatible Schema", "detail": exc.message, "code": exc.code},
        )

    @app.exception_handler(MutationApplicationError)
    async def mutation_error_handler(request: Request, exc: MutationApplicationError):
        logger.warning(f"Mutation application error: {exc.message}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"error": "Mutation Application Error", "detail": exc.message, "code": exc.code},
        )

    @app.exception_handler(StorageCorruptedError)
    async def storage_corrupted_handler(request: Request, exc: StorageCorruptedError):
        logger.error(f"Storage corrupted error: {exc.message}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Storage Corrupted", "detail": "Persisted record could not be read.", "code": exc.code},
        )

    @app.exception_handler(DataTripwireError)
    async def general_domain_error_handler(request: Request, exc: DataTripwireError):
        logger.warning(f"Domain error: {exc.message}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Application Error", "detail": exc.message, "code": exc.code},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        logger.warning(f"Validation error on {request.url.path}: {exc.errors()}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "Validation Error",
                "detail": str(exc.errors()),
                "code": "REQUEST_VALIDATION_ERROR",
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception on {request.url.path}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "detail": "An unexpected server error occurred while processing your request.",
                "code": "INTERNAL_SERVER_ERROR",
            },
        )

    # 3. Mount Routers
    app.include_router(health.router)
    app.include_router(domains.router)
    app.include_router(datasets.router)
    app.include_router(evaluations.router)

    return app


app = create_app()
