from fastapi import APIRouter, FastAPI

app = FastAPI(
    title="Client Service",
    docs_url="/client/docs",
    redoc_url="/client/redoc",
    openapi_url="/client/openapi.json",
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
