from fastapi import APIRouter

router = APIRouter(prefix="/clients", tags=["clients"])


@router.get("/")
async def clients_root():
    """Client app root endpoint."""
    return {"module": "client_app", "status": "ready"}
