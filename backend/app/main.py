from fastapi import FastAPI

from app.routers import plaid

app = FastAPI(title="Driftline")
app.include_router(plaid.router)


@app.get("/health")
def health():
    return {"status": "ok"}
