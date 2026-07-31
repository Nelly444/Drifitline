from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import clustering, dashboard, forecasting, plaid

app = FastAPI(title="Driftline")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(plaid.router)
app.include_router(clustering.router)
app.include_router(forecasting.router)
app.include_router(dashboard.router)


@app.get("/health")
def health():
    return {"status": "ok"}
