from fastapi import APIRouter, FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError

app = FastAPI(
    title="Client Service",
    docs_url="/client/docs",
    redoc_url="/client/redoc",
    openapi_url="/client/openapi.json",
)


# Exception handlers
@app.exception_handler(RequestValidationError)
async def handle_request_validation_error(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle FastAPI/Pydantic validation errors (422)."""
    errors = exc.errors()
    if errors:
        first_error = errors[0]
        field = ".".join(str(loc) for loc in first_error["loc"][1:])  # Skip 'body'
        message = f"{field}: {first_error['msg']}" if field else first_error['msg']
    else:
        message = "Validation error"

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error_code": "VALIDATION_ERROR",
            "message": message,
            "type": "validation_error"
        }
    )


@app.exception_handler(PydanticValidationError)
async def handle_pydantic_validation_error(
    request: Request, exc: PydanticValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors (422)."""
    errors = exc.errors()
    if errors:
        first_error = errors[0]
        field = ".".join(str(loc) for loc in first_error["loc"])
        message = f"{field}: {first_error['msg']}"
    else:
        message = "Validation error"

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error_code": "VALIDATION_ERROR",
            "message": message,
            "type": "validation_error"
        }
    )


@app.exception_handler(Exception)
async def handle_unexpected_exception(
    request: Request, exc: Exception
) -> JSONResponse:
    """Handle unexpected exceptions (500)."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred",
            "type": "system_error",
        },
    )


# Create router with /client prefix
router = APIRouter(prefix="/client", tags=["client"])


@router.get("/")
async def read_root():
    return {"name": "Client Service"}


@router.get("/health")
async def read_health():
    return {"status": "ok"}


# Include router
app.include_router(router)
