from fastapi import FastAPI

from app.routers import clustering, plaid

app = FastAPI(title="Driftline")
app.include_router(plaid.router)
app.include_router(clustering.router)


@app.get("/health")
def health():
    return {"status": "ok"}
