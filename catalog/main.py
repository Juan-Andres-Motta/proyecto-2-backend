from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def read_root():
    return {"name": "Catalog Service"}


@app.get("/health")
async def read_health():
    return {"status": "ok"}
