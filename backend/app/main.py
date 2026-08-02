from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth import UserCreate, UserRead, UserUpdate, auth_backend, fastapi_users
from app.config import get_settings
from app.routers import account, clustering, dashboard, forecasting, plaid
from app.services.rate_limit import rate_limit
from app.services.scheduler import create_scheduler
from app.ws import router as ws


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = create_scheduler()
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(title="Driftline", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[get_settings().FRONTEND_ORIGIN],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
    dependencies=[Depends(rate_limit(5, 60))],
)
app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
    dependencies=[Depends(rate_limit(10, 60))],
)
app.include_router(account.router)
app.include_router(fastapi_users.get_users_router(UserRead, UserUpdate), prefix="/users", tags=["users"])

app.include_router(plaid.router)
app.include_router(clustering.router)
app.include_router(forecasting.router)
app.include_router(dashboard.router)
app.include_router(ws.router)


@app.get("/health")
def health():
    return {"status": "ok"}
