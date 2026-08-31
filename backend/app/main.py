from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from .config import settings
from .rate_limit import limiter
from .routers import (
    admin, auth, billing, email_verify, geo, gyms, matches, messages, notices,
    notifications, profiles, safety, swipes,
    verification, withdrawal,
)

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

@app.middleware("http")
async def security_headers(request, call_next):
    """Schutz-Header für alle API-Antworten.

    Die statischen Seiten bekommen ihre Header von nginx (siehe
    deploy/nginx-flexr.conf); die API antwortet aber auch direkt an Clients und
    soll sich nicht darauf verlassen, hinter genau diesem nginx zu stehen.

    Kein CSP hier: Die API liefert ausschließlich JSON, das nichts ausführt.
    Die Content-Security-Policy gehört zu den HTML-Auslieferungen.
    """
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("X-Frame-Options", "DENY")
    # Antworten mit Profil-, Chat- oder Prüfdaten dürfen nirgends
    # zwischengespeichert werden - weder im Browser noch in einem Proxy.
    if request.url.path.startswith("/api/") and request.url.path != "/api/health":
        response.headers.setdefault("Cache-Control", "no-store")
    return response


app.include_router(auth.router)
app.include_router(email_verify.router)
app.include_router(profiles.router)
app.include_router(swipes.router)
app.include_router(matches.router)
app.include_router(messages.router)
app.include_router(notifications.router)
app.include_router(billing.router)
app.include_router(safety.router)
# Beide ohne Anmeldezwang - siehe die Modulkommentare: § 13a FAGG und
# Art. 16 DSA stehen jedem offen, nicht nur angemeldeten Nutzern.
app.include_router(withdrawal.router)
app.include_router(notices.router)
app.include_router(verification.router)
app.include_router(gyms.router)
app.include_router(geo.router)
app.include_router(admin.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
