"""Online-Rücktrittsfunktion nach § 13a FAGG.

Geprüft wird vor allem, was die Vorschrift von einer *Funktion* verlangt und
was ein Formular allein nicht leistet: dass sie ohne Anmeldung erreichbar ist,
dass ein zweiter Schritt bestätigt werden muss, und dass die Bestätigung
Inhalt, Datum und Uhrzeit der Erklärung wiedergibt.
"""

from datetime import datetime

import pytest

from tests.conftest import TestingSessionLocal, register_raw


@pytest.fixture
def mit_smtp(monkeypatch):
    """Tut so, als wäre ein Mailserver eingerichtet.

    Die Testumgebung hat keinen (siehe app/mailer.py). Tests, die die
    Ruecktrittsmechanik prüfen und nicht den Mailversand, sollen deshalb nicht
    stillschweigend im SMTP-losen Zweig landen.
    """
    from app.routers import withdrawal

    monkeypatch.setattr(withdrawal, "email_configured", lambda: True)


def _payload(**overrides):
    basis = {
        "name": "Max Mustermann",
        "email": "max@example.com",
        "contract_reference": "max@example.com",
        "confirmed": True,
    }
    basis.update(overrides)
    return basis


def test_ruecktritt_ohne_anmeldung_moeglich(client, mit_smtp):
    """Wer sein Konto gelöscht hat oder sich nicht einloggen kann, muss
    trotzdem zurücktreten können - ein Login wäre eine Hürde, die § 13a FAGG
    nicht vorsieht."""
    resp = client.post("/api/withdrawal", json=_payload())
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["reference"].startswith("W-")
    assert body["confirmation_sent"] is True


def test_ruecktritt_braucht_getrennte_bestaetigung(client):
    """§ 13a Abs. 3 FAGG verlangt einen eigenen Bestätigungsschritt. Ein
    ausgefülltes Formular ohne Bestätigung ist noch keine Erklärung."""
    resp = client.post("/api/withdrawal", json=_payload(confirmed=False))
    assert resp.status_code == 422


def test_bestaetigungstext_enthaelt_inhalt_datum_uhrzeit(client):
    """Die Bestätigung muss den Inhalt der Erklärung samt Datum und Uhrzeit
    wiedergeben (§ 13a Abs. 4 FAGG) - nicht bloß "wir haben etwas erhalten"."""
    resp = client.post("/api/withdrawal", json=_payload())
    text = resp.json()["declaration_text"]

    assert "widerrufe" in text.lower()
    assert "Max Mustermann" in text
    assert "max@example.com" in text  # Vertrags-/Kontobezug
    heute = datetime.utcnow().strftime("%d.%m.%Y")
    assert heute in text
    assert "Uhr" in text


def test_erklaerung_wird_gespeichert_und_ist_auffindbar(client, mit_smtp):
    from app.models import WithdrawalDeclaration

    resp = client.post("/api/withdrawal", json=_payload(message="Kein Interesse mehr."))
    reference = resp.json()["reference"]

    db = TestingSessionLocal()
    try:
        eintrag = db.query(WithdrawalDeclaration).one()
        assert eintrag.reference == reference
        assert eintrag.email == "max@example.com"
        assert eintrag.message == "Kein Interesse mehr."
        # Der Zeitstempel belegt, dass die Bestätigung ausgelöst wurde.
        assert eintrag.confirmation_sent_at is not None
        assert eintrag.confirmation_channel == "email"
        # Ohne Anmeldung gibt es keine Kontozuordnung - das ist kein Fehler.
        assert eintrag.user_id is None
    finally:
        db.close()


def test_angemeldeter_ruecktritt_wird_dem_konto_zugeordnet(client):
    """Kommt ein gültiger Token mit, ist die Zuordnung geschenkt - Pflicht ist
    sie nicht."""
    from app.models import User, WithdrawalDeclaration

    headers = register_raw(client, "abo@example.com")

    resp = client.post(
        "/api/withdrawal", json=_payload(email="abo@example.com"), headers=headers
    )
    assert resp.status_code == 201

    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.email == "abo@example.com").first()
        eintrag = db.query(WithdrawalDeclaration).one()
        assert eintrag.user_id == user.id
    finally:
        db.close()


def test_kaputter_token_verhindert_den_ruecktritt_nicht(client):
    """Ein abgelaufener Token darf die Erklärung nicht scheitern lassen - er
    bedeutet nur "nicht zugeordnet"."""
    resp = client.post(
        "/api/withdrawal",
        json=_payload(),
        headers={"Authorization": "Bearer voelliger-unsinn"},
    )
    assert resp.status_code == 201


def test_ruecktritt_ueberdauert_die_kontoloeschung():
    """Die Erklärung ist der Nachweis, dass zurückgetreten wurde - sie darf
    nicht mit dem Konto verschwinden.

    Geprüft wird die Fremdschlüsselregel, nicht ihr Ablauf: SQLite setzt
    ``ondelete`` ohne ``PRAGMA foreign_keys=ON`` gar nicht durch, ein Löschtest
    hier wäre also grün, ohne etwas zu zeigen. Maßgeblich ist, dass die Spalte
    SET NULL deklariert - genau das legt auch die Migration an.

    Zum Vergleich: Alle anderen Nutzerbezüge (Fotos, Nachrichten, Meldungen)
    stehen auf CASCADE. Die Rücktrittserklärung ist die bewusste Ausnahme.
    """
    from app.models import WithdrawalDeclaration

    fk = next(iter(WithdrawalDeclaration.__table__.c.user_id.foreign_keys))
    assert fk.ondelete == "SET NULL"
    assert WithdrawalDeclaration.__table__.c.user_id.nullable is True
    # Die Kontaktadresse steht eigenständig in der Zeile - ohne sie wäre die
    # Erklärung nach dem Löschen des Kontos niemandem mehr zuzuordnen.
    assert WithdrawalDeclaration.__table__.c.email.nullable is False


def test_name_ist_pflicht(client):
    resp = client.post("/api/withdrawal", json=_payload(name=""))
    assert resp.status_code == 422


def test_leerzeichen_gelten_nicht_als_name(client):
    resp = client.post("/api/withdrawal", json=_payload(name="   "))
    assert resp.status_code == 422


def test_ohne_smtp_wird_keine_bestaetigung_versprochen(client, monkeypatch):
    """Ohne konfigurierten Mailversand darf die Antwort keine Bestätigung
    zusagen, die nie ankommt.

    § 13a Abs. 4 FAGG verlangt eine Bestätigung auf dauerhaftem Datenträger.
    Kann sie gerade nicht rausgehen, ist die Erklärung trotzdem wirksam - der
    Erklärende muss das aber erfahren und sich den angezeigten Wortlaut selbst
    sichern können. Genau diesen Fall hatte der erste Entwurf verschwiegen: Er
    meldete immer "verschickt", auch auf einem Server ganz ohne SMTP.
    """
    from app.models import WithdrawalDeclaration
    from app.routers import withdrawal

    monkeypatch.setattr(withdrawal, "email_configured", lambda: False)

    resp = client.post("/api/withdrawal", json=_payload())
    assert resp.status_code == 201

    body = resp.json()
    assert body["confirmation_sent"] is False
    assert "keine Bestätigungsmail" in body["message"]
    assert "trotzdem wirksam" in body["message"]
    # Der Wortlaut wird trotzdem angezeigt - er ist der einzige Nachweis, den
    # der Erklärende in diesem Fall bekommt.
    assert body["declaration_text"]

    db = TestingSessionLocal()
    try:
        eintrag = db.query(WithdrawalDeclaration).one()
        # Kein Versandzeitstempel fuer eine Mail, die nie rausging.
        assert eintrag.confirmation_sent_at is None
        assert eintrag.confirmation_channel is None
    finally:
        db.close()


def test_mit_smtp_bleibt_die_zusage_bestehen(client, monkeypatch):
    from app.routers import withdrawal

    monkeypatch.setattr(withdrawal, "email_configured", lambda: True)
    body = client.post("/api/withdrawal", json=_payload()).json()
    assert body["confirmation_sent"] is True
    assert "§ 13a Abs. 4 FAGG" in body["message"]


def test_doppelter_request_id_legt_keine_zweite_erklaerung_an(client, mit_smtp):
    """Ein Doppelklick auf "Widerruf bestätigen" darf nicht zu zwei
    Erklärungen (und zwei Mails) führen - die request_id macht den zweiten
    Versuch serverseitig zu einer Wiederholung derselben Antwort."""
    from app.models import WithdrawalDeclaration

    payload = _payload(request_id="doppelklick-123")
    erste = client.post("/api/withdrawal", json=payload)
    zweite = client.post("/api/withdrawal", json=payload)

    assert erste.status_code == 201
    assert zweite.status_code == 201
    assert erste.json()["reference"] == zweite.json()["reference"]

    db = TestingSessionLocal()
    try:
        assert db.query(WithdrawalDeclaration).count() == 1
    finally:
        db.close()


def test_ohne_request_id_bleibt_jede_erklaerung_eigenstaendig(client, mit_smtp):
    """Ohne request_id (älterer Client, formloser Zweitantrag) darf nichts
    zusammengeführt werden - nur eine gleiche request_id bedeutet Wiederholung."""
    from app.models import WithdrawalDeclaration

    client.post("/api/withdrawal", json=_payload())
    client.post("/api/withdrawal", json=_payload())

    db = TestingSessionLocal()
    try:
        assert db.query(WithdrawalDeclaration).count() == 2
    finally:
        db.close()


def test_lokalzeit_wien_wird_gespeichert(client, mit_smtp):
    from app.models import WithdrawalDeclaration

    client.post("/api/withdrawal", json=_payload())

    db = TestingSessionLocal()
    try:
        eintrag = db.query(WithdrawalDeclaration).one()
        assert eintrag.received_at_vienna
        assert "Uhr" in eintrag.received_at_vienna
    finally:
        db.close()


def test_status_wechselt_auf_bestaetigt_wenn_mail_rausgeht(client, mit_smtp):
    from app.models import WithdrawalDeclaration

    body = client.post("/api/withdrawal", json=_payload()).json()
    assert body["status"] == "bestaetigt"

    db = TestingSessionLocal()
    try:
        assert db.query(WithdrawalDeclaration).one().status == "bestaetigt"
    finally:
        db.close()


def test_status_bleibt_eingegangen_ohne_smtp(client, monkeypatch):
    from app.routers import withdrawal

    monkeypatch.setattr(withdrawal, "email_configured", lambda: False)
    body = client.post("/api/withdrawal", json=_payload()).json()
    assert body["status"] == "eingegangen"


def test_laufendes_abo_wird_beim_ruecktritt_automatisch_gestoppt(client, monkeypatch):
    """Ist die Erklärung einem Konto mit laufendem Stripe-Abo zugeordnet,
    verhindert der Rücktritt automatisch die nächste Abbuchung - niemand soll
    zusätzlich manuell kündigen müssen, um das zu erreichen."""
    from app.database import get_db
    from app.main import app
    from app.models import User, WithdrawalDeclaration
    from app.routers import withdrawal

    headers = register_raw(client, "abomitkonto@example.com")

    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.email == "abomitkonto@example.com").first()
        user.stripe_subscription_id = "sub_test123"
        user.is_subscribed = True
        db.commit()
    finally:
        db.close()

    gestoppte = []
    monkeypatch.setattr(
        withdrawal, "cancel_subscription_immediately", lambda sub_id: gestoppte.append(sub_id)
    )

    resp = client.post(
        "/api/withdrawal", json=_payload(email="abomitkonto@example.com"), headers=headers
    )
    assert resp.status_code == 201
    assert gestoppte == ["sub_test123"]

    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.email == "abomitkonto@example.com").first()
        assert user.is_subscribed is False
        eintrag = db.query(WithdrawalDeclaration).filter(
            WithdrawalDeclaration.email == "abomitkonto@example.com"
        ).one()
        assert eintrag.subscription_stopped_at is not None
    finally:
        db.close()


def test_status_endpunkt_ist_oeffentlich_und_liefert_stichtag(client):
    """Das statische Frontend fragt hierüber ab, ob die hervorgehobene
    Funktion schon Pflicht ist - ohne Anmeldung, jederzeit."""
    resp = client.get("/api/withdrawal/status")
    assert resp.status_code == 200
    body = resp.json()
    assert body["effective_date"] == "2026-10-01"
    assert isinstance(body["legally_required"], bool)


def test_status_vor_dem_stichtag_ist_die_funktion_nicht_pflicht(client, monkeypatch):
    from app import legal
    from datetime import date

    monkeypatch.setattr(legal, "WITHDRAWAL_FUNCTION_EFFECTIVE_DATE", date(2099, 1, 1))
    assert client.get("/api/withdrawal/status").json()["legally_required"] is False


def test_status_nach_dem_stichtag_ist_die_funktion_pflicht(client, monkeypatch):
    from app import legal
    from datetime import date

    monkeypatch.setattr(legal, "WITHDRAWAL_FUNCTION_EFFECTIVE_DATE", date(2020, 1, 1))
    assert client.get("/api/withdrawal/status").json()["legally_required"] is True


def test_stripe_fehler_beim_stoppen_verhindert_den_ruecktritt_nicht(client, monkeypatch):
    """Ein Stripe-Fehler (falscher Schlüssel, Netzwerk) darf die Erklärung
    selbst nicht scheitern lassen - sie ist unabhängig vom Abo wirksam."""
    from app.models import User
    from app.routers import withdrawal

    headers = register_raw(client, "abomitfehler@example.com")

    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.email == "abomitfehler@example.com").first()
        user.stripe_subscription_id = "sub_kaputt"
        db.commit()
    finally:
        db.close()

    def platzt(sub_id):
        raise RuntimeError("Stripe nicht erreichbar")

    monkeypatch.setattr(withdrawal, "cancel_subscription_immediately", platzt)

    resp = client.post(
        "/api/withdrawal", json=_payload(email="abomitfehler@example.com"), headers=headers
    )
    assert resp.status_code == 201
