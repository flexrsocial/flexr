from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import settings

# pool_size/max_overflow/pool_timeout gehören zu QueuePool (Postgres & co.) -
# SQLite (die Tests laufen gegen "sqlite:///:memory:", siehe tests/conftest.py)
# verwendet einen eigenen Pool-Typ, der diese Argumente nicht kennt und mit
# TypeError abbricht, sobald man sie übergibt.
_engine_kwargs = dict(
    # pool_pre_ping: verwirft eine Verbindung, statt mit ihr fehlzuschlagen,
    # wenn sie inzwischen tot ist (z.B. nach einem DB-Neustart oder einer
    # Firewall/Load-Balancer-Idle-Trennung).
    pool_pre_ping=True,
)
if not settings.database_url.startswith("sqlite"):
    _engine_kwargs.update(
        # pool_recycle: Verbindungen, die länger als das offenstehen, werden
        # präventiv erneuert statt erst beim nächsten Pre-Ping-Fehlschlag -
        # viele gemanagte Postgres-Anbieter kappen Verbindungen nach einer
        # festen Idle-Zeit serverseitig, unabhängig vom Client.
        pool_recycle=1800,
        # pool_size/max_overflow: Default (5+10=15) war für den einzelnen
        # Uvicorn-Prozess knapp bemessen - Starlette bedient jeden
        # synchronen Endpunkt aus einem eigenen Thread (siehe main.py,
        # Anhebung des Thread-Limits auf denselben Wert), mehr gleichzeitige
        # Anfragen mit DB-Zugriff als Pool-Plätze führen sonst zu
        # pool_timeout-Wartezeiten statt echter Nebenläufigkeit.
        pool_size=20,
        max_overflow=20,
        pool_timeout=30,
    )

engine = create_engine(settings.database_url, **_engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
