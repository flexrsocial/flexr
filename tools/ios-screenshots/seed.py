"""Testdaten fuer die iOS-Bildschirmfotos (Codemagic-Workflow ios-screenshots).

Legt in einer frischen SQLite-Datenbank ein kleines, immer gleiches Bild der
App an: ein Betrachter (Lukas) mit Deck, Matches mit und ohne Unterhaltung,
einem Chat ueber mehrere Tage und einem offenen Like. Die Konten entstehen
ueber die echte Registrierungs-API (TestClient), Fotos kommen aus
frontend/brand/demo und liegen in der S3-Attrappe (moto).

Aufruf aus backend/ mit gesetzter Umgebung (DATABASE_URL, S3_*, JWT_SECRET,
siehe codemagic.yaml):

    python ../tools/ios-screenshots/seed.py

Erwartet in FLEXR_SHOT_PASSWORD das Passwort aller Testkonten; der Workflow
erzeugt es pro Lauf neu. Nichts hiervon beruehrt eine echte Umgebung.
"""

import json
import os
import pathlib
import sys
import uuid
from datetime import timedelta

import boto3
from fastapi.testclient import TestClient

REPO = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "backend"))

from app.database import Base, SessionLocal, engine
from app.main import app
from app.models import Gym, GymStatus, Match, Message, Photo, PhotoStatus, User
from app.rate_limit import limiter
from app.security import create_access_token
from app.timeutil import utcnow

DEMO = REPO / "frontend" / "brand" / "demo"
PASSWORT = os.environ["FLEXR_SHOT_PASSWORD"]
S3_URL = os.environ["S3_ENDPOINT_URL"]
FOTO_BUCKET = os.environ.get("S3_BUCKET_NAME", "flexr-photos")

# (Schluessel, Name, Geschlecht, Geburtsdatum, PLZ, Fotos, verifiziert)
PERSONEN = [
    ("lukas", "Lukas", "mann", "1993-03-03", "1010",
     ["demo-lukas-v2.jpg", "demo-marco-v2.jpg", "demo-cem-v2.jpg"], True),
    ("lena", "Lena", "frau", "1996-04-02", "1070",
     ["demo-lena.jpg", "demo-hannah-v2.jpg", "demo-sofia-v2.jpg"], True),
    ("mia", "Mia", "frau", "2000-06-14", "1050",
     ["demo-maya-v2.jpg", "demo-emi-v2.jpg", "demo-laura-v2.jpg"], True),
    ("viktoria", "Viktoria", "frau", "1999-01-20", "8010",
     ["demo-viktoria-v2.jpg", "demo-katharina-v2.jpg", "demo-anna-v2.jpg"], False),
    ("theresa", "Theresa", "frau", "1994-09-12", "1100",
     ["demo-theresa-v2.jpg", "demo-melina-v3.jpg", "demo-selin-v3.jpg"], False),
    ("julia", "Julia", "frau", "1997-11-30", "1020",
     ["demo-julia.jpg", "demo-anna-v2.jpg", "demo-hannah-v2.jpg"], True),
    ("anna", "Anna", "frau", "1995-02-08", "1030",
     ["demo-anna-v2.jpg", "demo-laura-v2.jpg", "demo-emi-v2.jpg"], False),
    # Noch nicht freigeschaltet: zeigt nach dem Login das Verifizierungs-Gate
    # (Selfie-Schritt), erscheint in keinem Deck.
    ("nora", "Nora", "frau", "1998-05-21", "1060",
     ["demo-selin-v3.jpg", "demo-melina-v3.jpg", "demo-katharina-v2.jpg"], False),
]

NICHT_FREIGESCHALTET = {"nora"}

BIOS = {
    "lena": "Morgens Kraft, abends Laufen. Suche jemanden, der beim Deadlift mitzählt.",
    "mia": "Neu in Wien, trainiere im FITINN. Kaffee nach dem Leg Day?",
    "julia": "Hyrox im Frühling. Wer läuft mit?",
}


def demo_bild(name: str) -> pathlib.Path:
    pfad = DEMO / name
    if pfad.exists():
        return pfad
    # Nicht jedes Motiv gibt es als .jpg - dann die .webp-Fassung.
    return pfad.with_suffix(".webp")


def main() -> None:
    limiter.enabled = False
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    if db.query(Gym).count() == 0:
        gyms = json.loads((REPO / "backend" / "app" / "data" / "gyms_seed.json").read_text("utf-8"))
        for g in gyms:
            db.add(Gym(name=g["name"], street=g.get("street"), house_number=g.get("house_number"),
                       plz=g.get("plz"), city=g.get("city"), status=GymStatus.approved))
        db.commit()

    s3 = boto3.client("s3", endpoint_url=S3_URL, aws_access_key_id="test",
                      aws_secret_access_key="test", region_name="us-east-1")
    for bucket in (FOTO_BUCKET, os.environ.get("S3_PRIVATE_BUCKET_NAME", "flexr-verification")):
        try:
            s3.create_bucket(Bucket=bucket)
        except Exception:  # existiert schon
            pass
    s3.put_bucket_policy(Bucket=FOTO_BUCKET, Policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{"Effect": "Allow", "Principal": "*", "Action": "s3:GetObject",
                       "Resource": f"arn:aws:s3:::{FOTO_BUCKET}/*"}],
    }))

    client = TestClient(app)
    ids: dict[str, str] = {}
    for key, name, gender, geburt, plz, fotos, verifiziert in PERSONEN:
        email = f"{key}@example.com"
        gym = (db.query(Gym).filter(Gym.plz == plz).first()
               or db.query(Gym).filter(Gym.city == "Wien").first())
        label = f"{gym.name} — {gym.street} {gym.house_number}, {gym.plz} {gym.city}"
        antwort = client.post("/api/auth/register", json={
            "email": email, "password": PASSWORT, "name": name, "birthdate": geburt,
            "plz": plz, "city": gym.city or "Wien", "gender": gender, "gym": label,
            "consent_sensitive_data": True,
        })
        assert antwort.status_code == 200, antwort.text
        db.expire_all()
        user = db.query(User).filter_by(email=email).one()
        if key not in NICHT_FREIGESCHALTET:
            user.activated_at = utcnow()
        user.email_verified_at = utcnow()
        user.bio = BIOS.get(key, f"Hi, ich bin {name} und trainiere gern.")
        # Der blaue Haken hängt an `is_verified` (bis 16.10.2026 stand hier
        # `verified_at` - das Feld gibt es nicht, kein Profil hatte den Haken).
        user.is_verified = verifiziert
        for position, datei in enumerate(fotos):
            pfad = demo_bild(datei)
            endung = pfad.suffix.lstrip(".")
            schluessel = f"users/{user.id}/{uuid.uuid4()}.{endung}"
            s3.put_object(Bucket=FOTO_BUCKET, Key=schluessel, Body=pfad.read_bytes(),
                          ContentType="image/jpeg" if endung == "jpg" else "image/webp")
            db.add(Photo(user_id=user.id, url=f"{S3_URL}/{FOTO_BUCKET}/{schluessel}",
                         position=position, status=PhotoStatus.approved))
        db.commit()
        ids[key] = user.id

    def als(key: str) -> dict:
        return {"Authorization": f"Bearer {create_access_token(ids[key])}"}

    def like(von: str, an: str) -> None:
        r = client.post("/api/swipes", headers=als(von), json={"to_user_id": ids[an], "action": "like"})
        assert r.status_code in (200, 201), r.text

    # Matches: Lena (Chat ueber drei Tage), Viktoria (eine Nachricht), Mia
    # (noch keine Unterhaltung - "Hallo sagen"). Theresa hat Lukas geliked,
    # ohne dass er schon gewischt hat. Julia und Anna liegen im Deck.
    for frau in ("lena", "viktoria", "mia"):
        like(frau, "lukas")
        like("lukas", frau)
    like("theresa", "lukas")

    matches = {m["profile"]["name"]: m["match_id"]
               for m in client.get("/api/matches", headers=als("lukas")).json()}

    def schreibe(von: str, match: str, text: str) -> None:
        r = client.post(f"/api/matches/{matches[match]}/messages", headers=als(von), json={"content": text})
        assert r.status_code in (200, 201), r.text

    schreibe("lena", "Lena", "Hey! Trainierst du eher morgens oder abends?")
    schreibe("lukas", "Lena", "Meistens abends, nach der Arbeit. Und du?")
    schreibe("lena", "Lena", "Morgens vor der Arbeit, um 6. Ganz schön früh 😅")
    schreibe("lukas", "Viktoria", "Was steht bei dir diese Woche auf dem Trainingsplan?")

    # Nachrichten auf mehrere Tage verteilen, damit die Tagestrenner im Bild sind.
    jetzt = utcnow()
    verlauf = (db.query(Message).filter(Message.match_id == matches["Lena"])
               .order_by(Message.created_at).all())
    for nachricht, tage in zip(verlauf, (4, 1, 0)):
        nachricht.created_at = jetzt - timedelta(days=tage, hours=2)
    viktoria = db.query(Message).filter(Message.match_id == matches["Viktoria"]).one()
    viktoria.created_at = jetzt - timedelta(days=1, hours=5)
    db.commit()

    # Passwort-Link fuer den Klicktest (seit iOS 2.4.16): codemagic.yaml reicht
    # den Token als FLEXR_SHOT_RESET_TOKEN an den Test weiter.
    from app import password_reset
    lukas = db.query(User).filter(User.id == ids["lukas"]).one()
    pathlib.Path(os.environ.get("FLEXR_SHOT_RESET_FILE", "/tmp/flexr-shot-reset-token")).write_text(
        password_reset.issue(db, lukas)
    )

    print("Testdaten:", {k: v for k, v in ids.items()},
          "Matches:", list(matches), "Nutzer:", db.query(User).count(), "Gyms:", db.query(Gym).count())
    assert db.query(Match).count() == 3


if __name__ == "__main__":
    main()
