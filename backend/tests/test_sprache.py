"""Profilsprache und zweisprachiger Versand.

Die Sprachwahl lebte bis zum 11.09.2026 nur im Client. Fuer die Oberflaeche
reicht das - der Server verschickt aber E-Mails, die ohne Zutun des Clients
entstehen: die Inaktivitaets-Erinnerung aus dem Tagesjob, die
Moderationsmitteilung aus dem Admin-Bereich, die Zahlungsmail aus einem
Stripe-Webhook. Damit die in der Sprache des Empfaengers ankommen, steht sie
jetzt am Nutzer (``User.language``).

Geprueft wird beides: dass die Sprache ueberhaupt ankommt und stehen bleibt,
und dass der Mailer ihr folgt. Der Wortlaut selbst steht in
app/message_texts.py; hier zaehlt, dass die richtige Fassung gewaehlt wird.
"""

import pytest

from app.message_texts import TEXTE, normalise, t
from tests.conftest import DEFAULT_USER, create_admin, register_raw, register_user


@pytest.fixture
def admin_headers(client):
    headers, _ = create_admin(client, email="sprach-admin@example.com")
    return headers


def _gefangene_mails(monkeypatch):
    """Statt zu versenden: einsammeln. Gibt die Liste zurueck."""
    from app import mailer

    gesammelt = []

    def falle(to_address, subject, text_body, html_body=None, **kw):
        gesammelt.append(
            {"to": to_address, "subject": subject, "text": text_body, "html": html_body}
        )
        return True

    monkeypatch.setattr(mailer, "send_email", falle)
    monkeypatch.setattr(mailer, "send_email_with_retry", falle)
    monkeypatch.setattr(mailer, "email_configured", lambda: True)
    # Zwei Router holen sich `email_configured` beim Import als eigenen Namen -
    # sie sehen den Ersatz oben sonst nicht und landen im SMTP-losen Zweig.
    from app.routers import notices, withdrawal

    monkeypatch.setattr(notices, "email_configured", lambda: True)
    monkeypatch.setattr(withdrawal, "email_configured", lambda: True)
    return gesammelt


# ---------------------------------------------------------------------------
# Die Sprache am Profil
# ---------------------------------------------------------------------------


def test_registrierung_ohne_sprache_bleibt_deutsch(client):
    """Aeltere App-Fassungen schicken das Feld nicht - das darf kein leeres
    Kuerzel ergeben, sondern die Ausgangssprache."""
    headers = register_raw(client, "ohne-sprache@example.com")
    profil = client.get("/api/profiles/me", headers=headers).json()
    assert profil["language"] == "de"


def test_registrierung_merkt_die_sprache(client):
    headers = register_raw(client, "englisch@example.com", language="en")
    profil = client.get("/api/profiles/me", headers=headers).json()
    assert profil["language"] == "en"


def test_sprachwechsel_laeuft_ueber_das_profil(client):
    """Der Regler in der Oberflaeche schickt genau dieses eine Feld - die
    uebrigen Profildaten duerfen dabei unberuehrt bleiben."""
    headers = register_raw(client, "wechsel@example.com")
    vorher = client.get("/api/profiles/me", headers=headers).json()

    resp = client.patch("/api/profiles/me", json={"language": "en"}, headers=headers)
    assert resp.status_code == 200, resp.text
    nachher = resp.json()

    assert nachher["language"] == "en"
    for feld in ("plz", "city", "gym", "bio", "search_radius_km"):
        assert nachher[feld] == vorher[feld], feld


def test_unbekannte_sprache_wird_abgewiesen(client):
    """Es gibt genau zwei Sprachen. Ein 'fr' waere sonst stillschweigend
    gespeichert und der Mailer fiele fuer immer auf Deutsch zurueck, ohne dass
    jemand den Grund saehe."""
    headers = register_raw(client, "franzoesisch@example.com")
    resp = client.patch("/api/profiles/me", json={"language": "fr"}, headers=headers)
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Der Versand folgt der Sprache
# ---------------------------------------------------------------------------


def test_bestaetigungsmail_folgt_der_registrierungssprache(client, monkeypatch):
    mails = _gefangene_mails(monkeypatch)

    client.post(
        "/api/auth/register",
        json={
            **DEFAULT_USER,
            "email": "welcome-en@example.com",
            "name": "Alex",
            "language": "en",
        },
    )

    assert mails, "keine Bestaetigungsmail verschickt"
    assert mails[0]["subject"] == TEXTE["verify.subject"]["en"]
    assert "Welcome to FLEXR" in mails[0]["html"]
    assert '<html lang="en">' in mails[0]["html"]


def test_kontoloeschung_bestaetigt_in_der_profilsprache(client, monkeypatch):
    headers = register_user(client, "loeschen-en@example.com", language="en")
    mails = _gefangene_mails(monkeypatch)

    resp = client.request(
        "DELETE",
        "/api/profiles/me",
        json={"password": "supersecret123"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text

    assert mails, "keine Loeschbestaetigung verschickt"
    assert mails[-1]["subject"] == TEXTE["deletion.subject"]["en"]
    assert "grace period" in mails[-1]["text"]


def test_moderationsmitteilung_folgt_der_profilsprache(
    client, admin_headers, monkeypatch
):
    """Der Freitext des Moderators bleibt so stehen, wie er geschrieben wurde -
    uebersetzt wird der feste Rahmen darum (Art. 17 Abs. 3 DSA)."""
    headers = register_user(client, "gesperrt-en@example.com", language="en")
    user_id = client.get("/api/profiles/me", headers=headers).json()["id"]
    mails = _gefangene_mails(monkeypatch)

    resp = client.post(
        f"/api/admin/users/{user_id}/ban",
        json={"reason": "Wiederholte Zahlungsaufforderungen im Chat."},
        headers=admin_headers,
    )
    assert resp.status_code == 200, resp.text

    assert mails, "keine Moderationsmitteilung verschickt"
    mail = mails[-1]
    assert mail["subject"] == TEXTE["moderation.subject"]["en"]
    assert "Restriction: your account is blocked." in mail["text"]
    assert "object to the decision" in mail["text"]
    # Die Begruendung des Moderators unveraendert.
    assert "Wiederholte Zahlungsaufforderungen" in mail["text"]


def test_deutsche_profile_bekommen_weiter_deutsche_mails(
    client, admin_headers, monkeypatch
):
    """Die Gegenprobe: Ohne Sprachwahl aendert sich nichts."""
    headers = register_user(client, "gesperrt-de@example.com")
    user_id = client.get("/api/profiles/me", headers=headers).json()["id"]
    mails = _gefangene_mails(monkeypatch)

    client.post(
        f"/api/admin/users/{user_id}/ban",
        json={"reason": "Wiederholte Zahlungsaufforderungen im Chat."},
        headers=admin_headers,
    )

    mail = mails[-1]
    assert mail["subject"] == TEXTE["moderation.subject"]["de"]
    assert "Beschränkung: Dein Konto ist gesperrt." in mail["text"]


# ---------------------------------------------------------------------------
# Mails an Leute ohne Konto: die Sprache kommt von der Formularseite
# ---------------------------------------------------------------------------


def test_meldung_ohne_konto_antwortet_in_der_formularsprache(client, monkeypatch):
    mails = _gefangene_mails(monkeypatch)

    resp = client.post(
        "/api/notices",
        json={
            "category": "fraud",
            "explanation": (
                "The profile repeatedly asks for Paysafecard codes in the chat "
                "and claims an emergency. This is an attempted scam."
            ),
            "content_reference": "Profile 'Alex_Lifts', chat of 14 August 2026",
            "reporter_name": "Jane Doe",
            "reporter_email": "jane@example.com",
            "good_faith": True,
            "language": "en",
        },
    )
    assert resp.status_code == 201, resp.text

    # Die Antwort im Bestaetigungskasten des Formulars.
    assert "Your report has been received" in resp.json()["message"]
    # Und die Empfangsbestaetigung nach Art. 16 Abs. 4.
    assert mails[-1]["subject"] == TEXTE["notice.subject"]["en"].format(
        reference=resp.json()["reference"]
    )
    assert "Fraud, extortion, scam" in mails[-1]["text"]


def test_ruecktritt_wird_in_der_erklaerungssprache_aufgezeichnet(client, monkeypatch):
    """Wer auf der englischen Seite erklaert, erklaert auf Englisch - und genau
    das wird gespeichert und nach § 13a Abs. 4 FAGG bestaetigt. Eine deutsche
    Aufzeichnung waere nicht der Inhalt der Erklaerung, sondern eine
    Uebersetzung davon."""
    mails = _gefangene_mails(monkeypatch)

    resp = client.post(
        "/api/withdrawal",
        json={
            "name": "Jane Doe",
            "email": "jane@example.com",
            "confirmed": True,
            "language": "en",
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()

    assert "I hereby give notice that I withdraw" in body["declaration_text"]
    assert "Section 13a(4) FAGG" in body["message"]
    assert mails[-1]["subject"].startswith("Confirmation of your withdrawal")


def test_ruecktritt_eines_angemeldeten_folgt_dem_profil(client, monkeypatch):
    """Die Profilsprache geht vor: Wer angemeldet ist, bekommt FLEXR ohnehin in
    dieser Sprache - auch wenn er zufaellig auf der anderen Seite landet."""
    headers = register_user(client, "abo-en@example.com", language="en")
    _gefangene_mails(monkeypatch)

    resp = client.post(
        "/api/withdrawal",
        # Die deutsche Seite, aber ein englisches Profil.
        json={
            "name": "Alex",
            "email": "abo-en@example.com",
            "confirmed": True,
            "language": "de",
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    assert "I hereby give notice that I withdraw" in resp.json()["declaration_text"]


# ---------------------------------------------------------------------------
# Das Woerterbuch selbst
# ---------------------------------------------------------------------------


def test_jeder_text_gibt_es_in_beiden_sprachen():
    fehlend = [
        key for key, eintrag in TEXTE.items()
        if "de" not in eintrag or "en" not in eintrag
    ]
    assert fehlend == [], fehlend


def test_platzhalter_stimmen_zwischen_den_sprachen_ueberein():
    """Ein Platzhalter, den nur eine Sprache kennt, wirft im Betrieb einen
    KeyError oder bleibt als ``{name}`` in der Mail stehen."""
    import re

    abweichend = {}
    for key, eintrag in TEXTE.items():
        felder = {
            sprache: set(re.findall(r"\{(\w+)\}", eintrag[sprache]))
            for sprache in ("de", "en")
        }
        if felder["de"] != felder["en"]:
            abweichend[key] = felder
    assert abweichend == {}, abweichend


@pytest.mark.parametrize(
    "eingabe,erwartet",
    [("de", "de"), ("en", "en"), ("de-AT", "de"), ("EN", "en"),
     (None, "de"), ("", "de"), ("fr", "de")],
)
def test_normalise_faellt_auf_die_ausgangssprache_zurueck(eingabe, erwartet):
    assert normalise(eingabe) == erwartet


def test_fehlende_uebersetzung_faellt_auf_deutsch_zurueck(monkeypatch):
    """Dieselbe Regel wie in frontend/i18n.js: eine vergessene Uebersetzung
    sieht nach deutschem Text aus und nicht nach einem Fehler."""
    monkeypatch.setitem(TEXTE, "test.nurdeutsch", {"de": "Nur auf Deutsch"})
    assert t("test.nurdeutsch", "en") == "Nur auf Deutsch"
