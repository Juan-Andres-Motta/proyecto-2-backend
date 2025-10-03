from fastapi import FastAPI

from src.adapters.input.controllers.common_controller import router as common_router
from src.adapters.input.controllers.provider_controller import router as provider_router

app = FastAPI()

app.include_router(common_router)
app.include_router(provider_router)
