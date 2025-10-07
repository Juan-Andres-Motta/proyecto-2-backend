from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def read_root():
    return {"name": "Inventory Service"}


@app.get("/health")
async def read_health():
    return {"status": "ok"}
