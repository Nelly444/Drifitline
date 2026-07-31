from fastapi import FastAPI

from app.routers import clustering, forecasting, plaid

app = FastAPI(title="Driftline")
app.include_router(plaid.router)
app.include_router(clustering.router)
app.include_router(forecasting.router)


@app.get("/health")
def health():
    return {"status": "ok"}
