"""Passwort vergessen, Passwort aendern, E-Mail-Adresse aendern.

Bis zum 22.09.2026 gab es nichts davon: Wer sein Passwort vergass, kam nur
noch ueber den Support in sein Konto.
"""

from datetime import datetime, timedelta

from app import mailer
from app.models import PasswordReset, User
from tests.conftest import TestingSessionLocal, register_user
from app.timeutil import utcnow

PW = "supersecret123"


def _mails(monkeypatch):
    verschickt = []

    def fake(to_address, subject, text_body, html_body=None, **_):
        verschickt.append({"to": to_address, "subject": subject, "text": text_body})
        return True

    monkeypatch.setattr(mailer, "send_email_with_retry", fake)
    monkeypatch.setattr(
        mailer, "send_email",
        lambda **kw: verschickt.append(
            {"to": kw["to_address"], "subject": kw["subject"], "text": kw["text_body"]}
        ) or True,
    )
    return verschickt


def _token(mail):
    marke = "?reset="
    start = mail["text"].index(marke) + len(marke)
    return mail["text"][start:].split()[0]


def _login(client, email, pw):
    return client.post("/api/auth/login", json={"email": email, "password": pw})


def test_forgot_verraet_nicht_ob_es_das_konto_gibt(client, monkeypatch):
    mails = _mails(monkeypatch)
    register_user(client, "gibts@example.com")
    mails.clear()
    a = client.post("/api/auth/password/forgot", json={"email": "gibts@example.com"})
    b = client.post("/api/auth/password/forgot", json={"email": "nicht@example.com"})
    assert a.status_code == b.status_code == 200
    assert a.json() == b.json()
    assert [m["to"] for m in mails] == ["gibts@example.com"]


def test_reset_setzt_passwort_und_beendet_alte_sitzungen(client, monkeypatch):
    mails = _mails(monkeypatch)
    alt = register_user(client, "reset@example.com")
    mails.clear()
    client.post("/api/auth/password/forgot", json={"email": "Reset@Example.com"})
    token = _token(mails[-1])

    r = client.post("/api/auth/password/reset", json={"token": token, "new_password": "neuesPasswort99"})
    assert r.status_code == 200
    neu = {"Authorization": f"Bearer {r.json()['access_token']}"}

    assert client.get("/api/profiles/me", headers=neu).status_code == 200
    assert client.get("/api/profiles/me", headers=alt).status_code == 401
    assert _login(client, "reset@example.com", PW).status_code == 401
    assert _login(client, "reset@example.com", "neuesPasswort99").status_code == 200

    # Nur einmal einloesbar
    again = client.post("/api/auth/password/reset", json={"token": token, "new_password": "nochmalAnders1"})
    assert again.status_code == 400


def test_abgelaufener_link_greift_nicht(client, monkeypatch):
    mails = _mails(monkeypatch)
    register_user(client, "alt@example.com")
    client.post("/api/auth/password/forgot", json={"email": "alt@example.com"})
    token = _token(mails[-1])
    with TestingSessionLocal() as db:
        db.query(PasswordReset).update({"expires_at": utcnow() - timedelta(minutes=1)})
        db.commit()
    r = client.post("/api/auth/password/reset", json={"token": token, "new_password": "neuesPasswort99"})
    assert r.status_code == 400
    assert "abgelaufen" in r.json()["detail"]


def test_zu_langes_passwort_wird_abgelehnt(client, monkeypatch):
    mails = _mails(monkeypatch)
    register_user(client, "lang@example.com")
    client.post("/api/auth/password/forgot", json={"email": "lang@example.com"})
    r = client.post("/api/auth/password/reset", json={"token": _token(mails[-1]), "new_password": "ä" * 40})
    assert r.status_code == 422


def test_passwort_aendern(client, monkeypatch):
    mails = _mails(monkeypatch)
    h = register_user(client, "change@example.com")
    mails.clear()
    falsch = client.post("/api/profiles/me/password", headers=h,
                         json={"current_password": "falsch123", "new_password": "neuesPasswort99"})
    assert falsch.status_code == 400
    r = client.post("/api/profiles/me/password", headers=h,
                    json={"current_password": PW, "new_password": "neuesPasswort99"})
    assert r.status_code == 200
    neu = {"Authorization": f"Bearer {r.json()['access_token']}"}
    assert client.get("/api/profiles/me", headers=neu).status_code == 200
    assert client.get("/api/profiles/me", headers=h).status_code == 401
    assert any(m["to"] == "change@example.com" for m in mails)


def test_email_aendern(client, monkeypatch):
    mails = _mails(monkeypatch)
    h = register_user(client, "vorher@example.com")
    register_user(client, "belegt@example.com")
    mails.clear()

    assert client.post("/api/profiles/me/email", headers=h,
                       json={"new_email": "nachher@example.com", "password": "falsch123"}).status_code == 400
    assert client.post("/api/profiles/me/email", headers=h,
                       json={"new_email": "Belegt@example.com", "password": PW}).status_code == 409

    r = client.post("/api/profiles/me/email", headers=h,
                    json={"new_email": "Nachher@Example.com", "password": PW})
    assert r.status_code == 200
    assert r.json()["email"] == "nachher@example.com"
    empfaenger = sorted(m["to"] for m in mails)
    assert empfaenger == ["nachher@example.com", "vorher@example.com"]
    with TestingSessionLocal() as db:
        u = db.query(User).filter(User.email == "nachher@example.com").one()
        assert u.email_verified_at is None
    assert _login(client, "nachher@example.com", PW).status_code == 200



def test_login_sperre_nach_zehn_fehlversuchen(client, monkeypatch):
    mails = _mails(monkeypatch)
    register_user(client, "rate@example.com")
    for _ in range(10):
        assert _login(client, "rate@example.com", "falsch123").status_code == 401
    # Jetzt gesperrt - auch das richtige Passwort kommt nicht durch.
    gesperrt = _login(client, "rate@example.com", PW)
    assert gesperrt.status_code == 429
    assert "Minuten" in gesperrt.json()["detail"]

    # "Passwort vergessen" hebt die Sperre auf.
    client.post("/api/auth/password/forgot", json={"email": "rate@example.com"})
    r = client.post("/api/auth/password/reset",
                    json={"token": _token(mails[-1]), "new_password": "neuesPasswort99"})
    assert r.status_code == 200
    assert _login(client, "rate@example.com", "neuesPasswort99").status_code == 200


def test_erfolgreicher_login_setzt_zaehler_zurueck(client):
    register_user(client, "zaehler@example.com")
    for _ in range(9):
        _login(client, "zaehler@example.com", "falsch123")
    assert _login(client, "zaehler@example.com", PW).status_code == 200
    for _ in range(9):
        _login(client, "zaehler@example.com", "falsch123")
    assert _login(client, "zaehler@example.com", PW).status_code == 200
