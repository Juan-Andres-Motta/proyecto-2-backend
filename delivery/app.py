from fastapi import APIRouter, FastAPI

app = FastAPI(
    title="Delivery Service",
    docs_url="/delivery/docs",
    redoc_url="/delivery/redoc",
    openapi_url="/delivery/openapi.json",
)

# Create router with /delivery prefix
router = APIRouter(prefix="/delivery", tags=["delivery"])


@router.get("/")
async def read_root():
    return {"name": "Delivery Service"}


@router.get("/health")
async def read_health():
    return {"status": "ok"}


# Include router
app.include_router(router)
