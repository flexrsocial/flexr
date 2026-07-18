from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from .config import settings
from .rate_limit import limiter
from .routers import admin, auth, billing, matches, messages, profiles, safety, swipes, verification

# Tabellen werden per Alembic-Migration angelegt (siehe backend/alembic/),
# nicht mehr über Base.metadata.create_all().

app = FastAPI(title="FLEXR API")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(profiles.router)
app.include_router(swipes.router)
app.include_router(matches.router)
app.include_router(messages.router)
app.include_router(billing.router)
app.include_router(safety.router)
app.include_router(verification.router)
app.include_router(admin.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
