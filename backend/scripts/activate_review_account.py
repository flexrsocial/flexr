"""Schaltet ein einzelnes Konto ohne manuelle Prüfung frei — für den Prüfer.

Apple verlangt zur App- und TestFlight-Prüfung ein Konto, mit dem sich die App
vollständig bedienen lässt. Ohne Freischaltung sperrt
``require_activated_account`` Deck, Matches und Chat: Der Prüfer sähe die App
nie und lehnte sie nach Richtlinie 2.1 ab.

Bewusst ein eigenes Skript und keine Hintertür im Produktivcode: Es umgeht die
Alters- und Identitätsprüfung, muss also bewusst auf dem Server aufgerufen
werden, gilt genau einem namentlich genannten Konto und hinterlässt im
Protokoll, was es getan hat.

**Kein Ersatz für die Prüfung normaler Konten.** Für die gibt es den
Freigabe-Knopf im Admin-Dashboard (``routers/admin.approve_verification``), der
zusätzlich die Prüfcheckliste erzwingt und die Aufnahmen löscht.

Voraussetzung: Das Konto ist bereits regulär registriert — über die Web-App
oder Android —, hat also Profil, Studio und Fotos. Dieses Skript ergänzt nur
die Freischaltung.

Ausführen:

    cd /flexr/backend && venv/bin/python scripts/activate_review_account.py --email pruefer@example.com --dry-run
    cd /flexr/backend && venv/bin/python scripts/activate_review_account.py --email pruefer@example.com

Idempotent: Ein bereits freigeschaltetes Konto wird nicht erneut angefasst —
``activated_at`` bleibt der Zeitpunkt der ersten Freischaltung.
"""
import argparse
import sys
from datetime import datetime
from pathlib import Path
from app.timeutil import utcnow

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal  # noqa: E402
from app.models import User, VerificationStatus  # noqa: E402
from app.verification_service import activate_account, open_request  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", required=True, help="E-Mail des Prüfkontos")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Nur anzeigen, was geschähe; nichts schreiben.",
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        # Groß-/Kleinschreibung ignorieren: Bei der Registrierung getippte
        # Adressen weichen sonst von der hier eingegebenen ab.
        user = db.query(User).filter(User.email.ilike(args.email)).first()
        if user is None:
            print(f"Kein Konto mit der Adresse {args.email!r}.")
            print("Erst über die Web-App oder Android registrieren, dann dieses Skript.")
            return 1

        print(f"Konto: {user.name} <{user.email}> (id {user.id})")
        print(f"  freigeschaltet: {user.activated_at or 'nein'}")
        print(f"  E-Mail bestätigt: {user.email_verified_at or 'nein'}")
        print(f"  Alter geprüft: {user.age_verified}")
        print(f"  Fotos: {len(user.photos)}")

        if not user.photos:
            # Ein Konto ohne Foto erscheint im eigenen Profil leer und wird
            # niemandem ausgespielt - der Prüfer sähe wieder nichts.
            print("\nWarnung: Das Konto hat kein Foto. Bitte erst Fotos hochladen.")

        now = utcnow()
        if args.dry_run:
            print("\n--dry-run: nichts geschrieben.")
            return 0

        if user.email_verified_at is None:
            user.email_verified_at = now
        user.is_verified = True
        user.age_verified = True
        if user.age_verified_at is None:
            user.age_verified_at = now
        user.verification_method = "manual_id"
        activate_account(user)

        # Ein offener Vorgang würde den Clients weiterhin einen nächsten
        # Schritt melden - der Prüfer landete im Verifizierungsbildschirm,
        # obwohl das Konto längst frei ist.
        pending = open_request(db, user.id)
        if pending is not None:
            pending.status = VerificationStatus.approved
            pending.decided_at = now
            pending.review_reason = None
            print(f"Offener Vorgang {pending.id} als geprüft geschlossen.")

        db.commit()
        print(f"\nFreigeschaltet: {user.email} (activated_at {user.activated_at}).")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
