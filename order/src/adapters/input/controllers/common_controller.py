from fastapi import APIRouter

router = APIRouter(tags=["common"])


@router.get("/")
async def read_root():
    return {"name": "Order Service"}


@router.get("/health")
async def read_health():
    return {"status": "ok"}
