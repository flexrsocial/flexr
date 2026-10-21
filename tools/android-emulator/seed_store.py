"""Demo-Daten fuer Emulator-Tests, Store-Screenshots und Promo-Video (nur lokal,
SQLite + Moto). Datenbank unter $FLEXR_TEST_HOME (Standard ~/.cache/flexr-test).
Anmelden: <name>@store.example / store-demo-1234 (z. B. lukas, Match mit Laura).

    seed_store.py neu            DB neu anlegen, Konten, Fotos, Likes, Chat (Deutsch)
    seed_store.py sprache en     Bios und Chat auf Englisch (de zurueck)
    seed_store.py online         alle Profile "online" (last_seen_at = jetzt)
    seed_store.py antwort de|en  Hannah antwortet im Chat (fuer das Video)
    seed_store.py like-zurueck   Hannah/Miriam-Likes und Lukas' Swipes zuruecksetzen
"""
import io
import os
import sys
from datetime import date, timedelta

S = os.environ.get("FLEXR_TEST_HOME", os.path.expanduser("~/.cache/flexr-test"))
os.makedirs(S, exist_ok=True)
REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB = f"{S}/store.db"
ENV = {
    "DATABASE_URL": f"sqlite:///{DB}",
    "JWT_SECRET": "store-demo-only",
    "S3_ENDPOINT_URL": "http://localhost:5055",
    "S3_ACCESS_KEY_ID": "test",
    "S3_SECRET_ACCESS_KEY": "test",
    "S3_BUCKET_NAME": "flexr-photos",
    "S3_PRIVATE_BUCKET_NAME": "flexr-verification",
    "S3_REGION": "us-east-1",
    "S3_PUBLIC_BASE_URL": "http://localhost:5055/flexr-photos",
    "ENV": "development",
    "PREMIUM_ENABLED": "false",
}
os.environ.update(ENV)
sys.path.insert(0, os.path.join(REPO, "backend"))

DEMO = os.path.join(REPO, "frontend", "brand", "demo")
PASSWORT = "store-demo-1234"

GYMS = {
    "iron": ("Ironclub", "Burggasse", "5", "1070", "Wien"),
    "plate": ("Plates", "Ungargasse", "9", "1030", "Wien"),
    "kraft": ("Barbell", "Webgasse", "8", "1060", "Wien"),
    "urban": ("Urban Strength", "Favoritenstraße", "100", "1100", "Wien"),
    "nord": ("Nordlicht Fitness", "Brünner Straße", "30", "1210", "Wien"),
    "donau": ("Donau Athletics", "Wagramer Straße", "20", "1220", "Wien"),
}


def gym_label(k):
    n, s, nr, plz, ort = GYMS[k]
    return f"{n} — {s} {nr}, {plz} {ort}"


# key, Name, Geschlecht, Alter, Gym, Foto, Bio DE, Bio EN
PERSONEN = [
    ("lukas", "Lukas", "mann", 29, "iron", "lukas-v2",
     "Montag ist Beintag. Dienstag auch, wenn's sein muss.",
     "Monday is leg day. Tuesday too, if it has to be."),
    ("sofia", "Sofia", "frau", 30, "iron", "sofia-v2",
     "Battle Ropes am Morgen, Pasta am Abend.",
     "Battle ropes in the morning, pasta at night."),
    ("hannah", "Hannah", "frau", 27, "iron", "hannah-v2",
     "Kraftsport & Kaffee. Spottest du mich?",
     "Strength training & coffee. Spot me?"),
    ("miriam", "Miriam", "frau", 29, "plate", "miriam-v2",
     "Push, Pull, Legs – 5x die Woche. Am Wochenende am Berg.",
     "Push, pull, legs – 5x a week. Mountains at the weekend."),
    ("laura", "Laura", "frau", 28, "iron", "laura-v2",
     "Laufband-Hasserin, Langhantel-Liebhaberin.",
     "Treadmill hater, barbell lover."),
    ("anna", "Anna", "frau", 26, "kraft", "anna-v2",
     "Powerlifting-Anfängerin mit großen Plänen. Erst Squat, dann Schnitzel.",
     "Powerlifting beginner with big plans. Squats first, schnitzel second."),
    ("katharina", "Katharina", "frau", 31, "nord", "katharina-v2",
     "Spinning um 7, Büro um 9. Morgenmensch sucht Morgenmensch.",
     "Spinning at 7, office at 9. Morning person seeks morning person."),
    ("maya", "Maya", "frau", 27, "urban", "maya-v2",
     "Calisthenics & Sonnenuntergänge.",
     "Calisthenics & sunsets."),
    ("julia", "Julia", "frau", 25, "donau", "julia",
     "Yoga am Sonntag, Beintag am Montag.",
     "Yoga on Sunday, leg day on Monday."),
    ("emi", "Emi", "frau", 26, "plate", "emi-v2",
     "Rudergerät-Queen. Ramen-Expertin.",
     "Rowing machine queen. Ramen expert."),
    ("tobias", "Tobias", "mann", 30, "iron", "tobias",
     "Bodybuilding seit 8 Jahren. Koche gern für zwei – Meal Prep inklusive.",
     "Bodybuilding for 8 years. Happy to cook for two – meal prep included."),
    ("elias", "Elias", "mann", 28, "kraft", "elias-v2",
     "CrossFit, Klettern, schlechte Wortwitze.",
     "CrossFit, climbing, bad puns."),
    ("kenji", "Kenji", "mann", 29, "plate", "kenji-v2",
     "Hypertrophie-Nerd. Frag mich nach meinem Trainingsplan (lieber nicht).",
     "Hypertrophy nerd. Ask me about my training plan (better not)."),
    ("noah", "Noah", "mann", 27, "donau", "noah-v2",
     "Calisthenics im Park, Kaffee danach.",
     "Calisthenics in the park, coffee afterwards."),
    ("cem", "Cem", "mann", 31, "urban", "cem-v2",
     "Battle Ropes & Börek.",
     "Battle ropes & börek."),
]

CHAT = {  # Laura <-> Lukas, (Absender, DE, EN)
    "laura_lukas": [
        ("laura", "Hey! Du trainierst auch im Ironclub? 😄", "Hey! You train at Ironclub too? 😄"),
        ("lukas", "Ja, meistens abends. Hab dich beim Kreuzheben gesehen – Respekt!",
         "Yes, mostly in the evenings. Saw you deadlifting – respect!"),
        ("laura", "Haha danke 💪 Montag ist Beintag, falls du mitmachen willst",
         "Haha thanks 💪 Monday is leg day, if you want to join"),
        ("lukas", "Bin dabei. Und danach Kaffee?", "I'm in. Coffee afterwards?"),
        ("laura", "Deal ☕", "Deal ☕"),
    ],
}
ANTWORT = ("Klar! Mittwoch 18 Uhr im Ironclub? 🏋️‍♀️", "Sure! Wednesday 6 pm at Ironclub? 🏋️‍♀️")


def geburtstag(alter):
    heute = date(2026, 10, 17)
    return date(heute.year - alter, 3, 14)


def foto_varianten(datei):
    from PIL import Image, ImageOps
    im = Image.open(f"{DEMO}/demo-{datei}.jpg").convert("RGB")
    w, h = im.size
    v1 = im.crop((int(w * .12), int(h * .04), int(w * .88), int(h * .04) + int(h * .76))).resize((w, h))
    v2 = ImageOps.mirror(im.crop((int(w * .06), int(h * .10), int(w * .94), int(h * .10) + int(h * .88))).resize((w, h)))
    out = []
    for v in (im, v1, v2):
        b = io.BytesIO(); v.save(b, "JPEG", quality=90); gross = b.getvalue()
        seite = min(v.size)
        t = v.crop((0, 0, seite, seite)).resize((256, 256))
        b2 = io.BytesIO(); t.save(b2, "JPEG", quality=88)
        out.append((gross, b2.getvalue()))
    return out


def neu():
    import boto3
    from fastapi.testclient import TestClient
    if os.path.exists(DB):
        os.remove(DB)
    from app.database import Base, SessionLocal, engine
    from app import models
    from app.models import Gym, GymStatus, Match, Message, Photo, PhotoStatus, Swipe, User
    from app.timeutil import utcnow
    Base.metadata.create_all(bind=engine)

    s3 = boto3.client("s3", endpoint_url=ENV["S3_ENDPOINT_URL"], aws_access_key_id="test",
                      aws_secret_access_key="test", region_name="us-east-1")
    for b in ("flexr-photos", "flexr-verification"):
        try:
            s3.create_bucket(Bucket=b)
        except Exception:
            pass

    db = SessionLocal()
    for n, s, nr, plz, ort in GYMS.values():
        db.add(Gym(name=n, street=s, house_number=nr, plz=plz, city=ort, status=GymStatus.approved))
    db.commit()

    from app.main import app
    from app.rate_limit import limiter
    limiter.enabled = False
    ids = {}
    with TestClient(app) as c:
        for key, name, g, alter, gym, foto, bio_de, _ in PERSONEN:
            plz = GYMS[gym][3]
            r = c.post("/api/auth/register", json={
                "email": f"{key}@store.example", "password": PASSWORT, "name": name,
                "birthdate": geburtstag(alter).isoformat(), "plz": plz, "city": "Wien",
                "gender": g, "gym": gym_label(gym), "bio": bio_de, "consent_sensitive_data": True,
            })
            assert r.status_code == 200, r.text
            tok = r.json()["access_token"]
            ids[key] = c.get("/api/profiles/me", headers={"Authorization": f"Bearer {tok}"}).json()["id"]

    jetzt = utcnow()
    for key, name, g, alter, gym, foto, bio_de, _ in PERSONEN:
        u = db.query(User).filter(User.id == ids[key]).one()
        u.interest = models.Gender("frau" if g == "mann" else "mann")
        u.email_verified_at = jetzt
        u.activated_at = jetzt - timedelta(days=3)
        u.is_verified = True
        u.age_verified = True
        u.age_verified_at = jetzt
        u.verification_method = "manual_id"
        u.search_radius_km = 25
        u.last_seen_at = jetzt
        for pos, (gross, thumb) in enumerate(foto_varianten(foto)):
            k = f"users/{u.id}/demo-{pos}.jpg"
            kt = f"users/{u.id}/demo-{pos}-thumb.jpg"
            s3.put_object(Bucket="flexr-photos", Key=k, Body=gross, ContentType="image/jpeg", ACL="public-read")
            s3.put_object(Bucket="flexr-photos", Key=kt, Body=thumb, ContentType="image/jpeg", ACL="public-read")
            db.add(Photo(user_id=u.id, url=f"{ENV['S3_PUBLIC_BASE_URL']}/{k}",
                         thumb_url=f"{ENV['S3_PUBLIC_BASE_URL']}/{kt}", position=pos,
                         status=PhotoStatus.approved))
    db.commit()

    # Likes an Lukas: Miriam zuerst im Deck (juengster Like), dann Hannah.
    db.add(Swipe(from_user_id=ids["hannah"], to_user_id=ids["lukas"], action="like",
                 created_at=jetzt - timedelta(hours=3)))
    db.add(Swipe(from_user_id=ids["miriam"], to_user_id=ids["lukas"], action="like",
                 created_at=jetzt - timedelta(hours=1)))
    # Bestehendes Match Laura <-> Lukas mit Chat
    for a, b in (("laura", "lukas"), ("lukas", "laura")):
        db.add(Swipe(from_user_id=ids[a], to_user_id=ids[b], action="like", created_at=jetzt - timedelta(days=1)))
    x, y = sorted([ids["laura"], ids["lukas"]])
    m = Match(user_a_id=x, user_b_id=y, created_at=jetzt - timedelta(days=1))
    db.add(m); db.flush()
    for i, (von, de, _en) in enumerate(CHAT["laura_lukas"]):
        db.add(Message(match_id=m.id, sender_id=ids[von], content=de,
                       created_at=jetzt - timedelta(minutes=50 - i * 7), read_at=jetzt))
    # Sofia (Frau) hat ein Match mit Tobias - fuer die Profilansicht eines Mannes
    for a, b in (("sofia", "tobias"), ("tobias", "sofia")):
        db.add(Swipe(from_user_id=ids[a], to_user_id=ids[b], action="like", created_at=jetzt - timedelta(days=2)))
    x, y = sorted([ids["sofia"], ids["tobias"]])
    db.add(Match(user_a_id=x, user_b_id=y, created_at=jetzt - timedelta(days=2)))
    db.commit()
    print("angelegt:", len(ids), "Konten; Passwort", PASSWORT)


def sprache(lang):
    from app.database import SessionLocal
    from app.models import Match, Message, User
    db = SessionLocal()
    i = 7 if lang == "en" else 6
    by_key = {}
    for p in PERSONEN:
        u = db.query(User).filter(User.email == f"{p[0]}@store.example").one()
        u.bio = p[i]; u.language = lang
        by_key[p[0]] = u
    laura, lukas = by_key["laura"], by_key["lukas"]
    x, y = sorted([laura.id, lukas.id])
    m = db.query(Match).filter(Match.user_a_id == x, Match.user_b_id == y).one()
    msgs = db.query(Message).filter(Message.match_id == m.id).order_by(Message.created_at).all()
    for msg, (_von, de, en) in zip(msgs, CHAT["laura_lukas"]):
        msg.content = en if lang == "en" else de
        msg.display_content = None
    db.commit(); print("Sprache", lang)


def online():
    from app.database import SessionLocal
    from app.models import User
    from app.timeutil import utcnow
    db = SessionLocal()
    for u in db.query(User).all():
        u.last_seen_at = utcnow()
    db.commit(); print("online")


def antwort(lang):
    from app.database import SessionLocal
    from app.models import Match, Message, User
    from app.timeutil import utcnow
    db = SessionLocal()
    h = db.query(User).filter(User.email == "hannah@store.example").one()
    l = db.query(User).filter(User.email == "lukas@store.example").one()
    x, y = sorted([h.id, l.id])
    m = db.query(Match).filter(Match.user_a_id == x, Match.user_b_id == y).one()
    db.add(Message(match_id=m.id, sender_id=h.id, content=ANTWORT[1 if lang == "en" else 0], created_at=utcnow()))
    h.last_seen_at = utcnow()
    db.commit(); print("Antwort gesendet")


def like_zurueck():
    """Fuer einen neuen Videodurchlauf: Lukas' Swipes auf Hannah/Miriam weg,
    Match Hannah<->Lukas samt Nachrichten weg."""
    from app.database import SessionLocal
    from app.models import Match, Message, Swipe, User
    db = SessionLocal()
    k = {e: db.query(User).filter(User.email == f"{e}@store.example").one() for e in ("hannah", "miriam", "lukas")}
    for e in ("hannah", "miriam"):
        db.query(Swipe).filter(Swipe.from_user_id == k["lukas"].id, Swipe.to_user_id == k[e].id).delete()
    for e in ("hannah", "miriam"):
        x, y = sorted([k[e].id, k["lukas"].id])
        m = db.query(Match).filter(Match.user_a_id == x, Match.user_b_id == y).first()
        if m:
            db.query(Message).filter(Message.match_id == m.id).delete()
            db.delete(m)
    db.commit(); print("zurueckgesetzt")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "neu":
        neu()
    elif cmd == "sprache":
        sprache(sys.argv[2])
    elif cmd == "online":
        online()
    elif cmd == "antwort":
        antwort(sys.argv[2])
    elif cmd == "like-zurueck":
        like_zurueck()
