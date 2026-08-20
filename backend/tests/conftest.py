import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET", "test-secret-for-pytest")
# Lokale .env-Dateien duerfen die Tests nie mit einem echten oder absichtlich
# ungueltigen SMTP-Relay verbinden. Versandpfade werden gezielt per monkeypatch
# getestet; der Normalfall bleibt rein lokal und dadurch schnell.
os.environ.setdefault("SMTP_HOST", "")
os.environ.setdefault("SMTP_FROM", "")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.rate_limit import limiter

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
limiter.enabled = False


# Die Umkreissuche geht von der Gym-Adresse aus (app/gym_geo.py), nicht mehr
# vom Wohnort. Die Test-Gyms brauchen deshalb echte PLZ, und Tests, die
# Entfernungen prüfen, variieren das Gym statt der Wohn-PLZ.
GYM_WIEN = "John Harris Fitness — Teststraße 12, 1010 Wien"
GYM_WIEN_2 = "FitInn — Favoritenstraße 100, 1100 Wien"
GYM_GRAZ = "Kraftwerk Gym — Annenstraße 5, 8010 Graz"
# Bestandsgym ohne Adresse: nimmt an der Umkreissuche nicht teil
GYM_OHNE_ADRESSE = "Anderes Studio"


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.create_all(bind=engine)
    # Gym-Seed: Registrierung validiert gegen die gyms-Tabelle (in Produktion
    # per Migration befüllt, hier minimal für die Testfälle)
    from app.models import Gym, GymStatus

    db = TestingSessionLocal()
    try:
        for name, street, nr, plz, city in [
            ("John Harris Fitness", "Teststraße", "12", "1010", "Wien"),
            ("FitInn", "Favoritenstraße", "100", "1100", "Wien"),
            ("Kraftwerk Gym", "Annenstraße", "5", "8010", "Graz"),
            ("Holmes Place", "Millennium City", "20", "1200", "Wien"),
        ]:
            db.add(Gym(name=name, street=street, house_number=nr, plz=plz,
                       city=city, status=GymStatus.approved))
        # Ohne Adresse - Bestandsnamen, die aus der Auswahlliste und aus der
        # Umkreissuche herausfallen
        for name in ["McFit", "Clever Fit", "Fitness First", "Iron Gym Wien",
                     "USI Wien", "Anderes Studio"]:
            db.add(Gym(name=name, status=GymStatus.approved))
        db.add(Gym(name="Testgym mit Adresse", street="Teststraße",
                   house_number="12", plz="1010", city="Wien",
                   status=GymStatus.approved))
        db.commit()
    finally:
        db.close()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


DEFAULT_USER = {
    "password": "supersecret123",
    "birthdate": "1997-06-15",
    "plz": "1010",
    "city": "Wien",
    "gender": "mann",
    "gym": GYM_WIEN,
    # consent_withdrawal_waiver steht hier bewusst nicht mehr drin: Der Haken
    # ist am 15.08.2026 weggefallen, und der Normalfall der Tests soll das
    # abbilden, was die aktuellen Clients schicken. Dass ältere App-Fassungen
    # das Feld weiter mitsenden dürfen, prüft test_auth.py gesondert.
    "consent_sensitive_data": True,
}


def register_raw(client, email, name="Test User", confirm_email=True, **overrides):
    """Registrierung ohne Freischaltung - das Konto steht danach vor der
    Alters- und Identitätsprüfung und kann noch nicht swipen/chatten.

    Die E-Mail-Adresse gilt dabei als bestätigt: Sie ist seit der Einführung
    des Aktivierungslinks Voraussetzung für den Start der Prüfung, aber für
    alles andere nur Rauschen. Wer den Link selbst prüfen will, setzt
    ``confirm_email=False`` (siehe test_email_verification.py).
    """
    payload = {**DEFAULT_USER, "email": email, "name": name, **overrides}
    resp = client.post("/api/auth/register", json=payload)
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    if confirm_email:
        mark_email_confirmed(client, headers)
    return headers


def mark_email_confirmed(client, headers):
    """Setzt die Adresse direkt in der Test-DB auf bestätigt.

    Der echte Weg führt über den Token aus der Mail; hier zählt nur, dass die
    Vorbedingung erfüllt ist - analog zu activate_user() und add_approved_photo().
    """
    from datetime import datetime

    from app.models import User

    user_id = client.get("/api/profiles/me", headers=headers).json()["id"]
    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        user.email_verified_at = datetime.utcnow()
        db.commit()
    finally:
        db.close()
    return user_id


def activate_user(client, headers):
    """Setzt ein Konto auf "Prüfung bestanden", ohne den ganzen Ablauf zu
    durchlaufen.

    Alle Tests außerhalb von test_verification.py prüfen andere Funktionen und
    brauchen ein nutzbares Konto. Der echte Weg (Selfies -> Ausweis ->
    Admin-Freigabe) verlangt einen Objekt-Storage, den es im Test nicht gibt -
    deshalb wird der Zustand direkt in die Test-DB geschrieben, analog zu
    add_approved_photo().
    """
    from datetime import datetime

    from app.models import User

    user_id = client.get("/api/profiles/me", headers=headers).json()["id"]
    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        user.activated_at = datetime.utcnow()
        db.commit()
    finally:
        db.close()
    return user_id


def register_user(client, email, name="Test User", **overrides):
    """Registrierung inklusive bestandener Verifizierung - der Normalfall für
    alle Tests, die nicht die Verifizierung selbst prüfen."""
    headers = register_raw(client, email, name=name, **overrides)
    activate_user(client, headers)
    return headers


def add_approved_photo(client, headers, url="https://cdn.example.test/photo.jpg"):
    """Gibt dem Nutzer hinter ``headers`` ein von der Moderation freigegebenes Foto.

    Nötig für alle Deck-Tests: get_deck() überspringt Profile ohne freigegebenes
    Foto. Der echte Weg (Presign -> S3-Upload -> Admin-Freigabe) funktioniert im
    Test nicht, da kein Objekt-Storage vorhanden ist - deshalb wird die
    Photo-Zeile direkt in die Test-DB geschrieben.
    """
    from app.models import Photo, PhotoStatus

    user_id = client.get("/api/profiles/me", headers=headers).json()["id"]
    db = TestingSessionLocal()
    try:
        position = db.query(Photo).filter(Photo.user_id == user_id).count()
        photo = Photo(user_id=user_id, url=url, position=position, status=PhotoStatus.approved)
        db.add(photo)
        db.commit()
        db.refresh(photo)
        return photo.id
    finally:
        db.close()


def register_user_with_photo(client, email, name="Test User", **overrides):
    """Registrierung + freigegebenes Foto - so, wie ein Profil aussehen muss,
    damit es im Swipe-Deck anderer Nutzer auftaucht."""
    headers = register_user(client, email, name=name, **overrides)
    add_approved_photo(client, headers)
    return headers


def create_admin(client, email="admin@example.com", password="adminsecret123", name="Admin"):
    """Legt einen AdminUser direkt in der DB an (kein öffentlicher Registrierungs-
    Endpoint vorgesehen) und loggt sich darüber ein."""
    from app.models import AdminUser
    from app.security import hash_password

    db = TestingSessionLocal()
    try:
        admin = AdminUser(email=email, password_hash=hash_password(password), name=name)
        db.add(admin)
        db.commit()
        db.refresh(admin)
        admin_id = admin.id
    finally:
        db.close()

    resp = client.post("/api/admin/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, admin_id
