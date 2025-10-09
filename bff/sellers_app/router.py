from fastapi import APIRouter

router = APIRouter(prefix="/sellers", tags=["sellers"])


@router.get("/")
async def sellers_root():
    """Sellers app root endpoint."""
    return {"module": "sellers_app", "status": "ready"}
