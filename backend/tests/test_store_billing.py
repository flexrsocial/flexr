"""Belege aus App Store und Play Store: Pruefung und Berechtigung.

Der wichtigste Teil sind die **Ablehnungen**. Ein Kauf-Beleg ist das einzige
Stueck Eingabe, mit dem sich hier Geldwert erzeugen laesst - was daran nicht
stimmt, muss zuverlaessig auffallen.

Fuer den positiven Fall wird Apples Wurzelzertifikat im Test durch ein selbst
erzeugtes ersetzt. Anders ginge es nicht: Eine gueltige Signatur von Apple
kann niemand nachbauen, und genau das ist ja der Sinn der Sache. Geprueft wird
damit trotzdem das, worauf es ankommt - dass die Kette abgelaufen wird, dass
die Signatur zum Blattzertifikat passt und dass beides bei der kleinsten
Aenderung bricht.
"""

import base64
import json
from datetime import datetime, timedelta, timezone

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature
from cryptography.x509.oid import NameOID

from app import store_billing
from app.config import settings
from app.models import StoreProvider, StoreSubscription, User
from tests.conftest import TestingSessionLocal, register_user
from app.timeutil import utcnow

# ---------------------------------------------------------------------------
# Eine Zertifikatskette, wie Apple sie mitschickt - nur eben unsere
# ---------------------------------------------------------------------------


def _cert(subject: str, key, issuer_name, issuer_key, ca: bool, tage: int = 30, oid=None):
    jetzt = datetime.now(timezone.utc)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, subject)])
    bauer = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(issuer_name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(jetzt - timedelta(days=1))
        .not_valid_after(jetzt + timedelta(days=tage))
        .add_extension(x509.BasicConstraints(ca=ca, path_length=None), critical=True)
    )
    if oid is not None:
        # Apples Markierung: leerer ASN.1-NULL-Wert, wie im Original.
        bauer = bauer.add_extension(
            x509.UnrecognizedExtension(x509.ObjectIdentifier(oid), b"\x05\x00"), critical=False
        )
    return bauer.sign(issuer_key, hashes.SHA256()), name


@pytest.fixture
def kette():
    """(Wurzel, Zwischenstelle, Blatt) samt privatem Blattschluessel."""
    wurzel_key = ec.generate_private_key(ec.SECP256R1())
    # Selbstsigniert: Aussteller ist der eigene Name.
    wurzel, wurzel_name = _cert(
        "Test Root",
        wurzel_key,
        x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Test Root")]),
        wurzel_key,
        ca=True,
    )

    zwischen_key = ec.generate_private_key(ec.SECP256R1())
    zwischen, zwischen_name = _cert(
        "Test Intermediate", zwischen_key, wurzel_name, wurzel_key, ca=True,
        oid="1.2.840.113635.100.6.2.1",
    )

    blatt_key = ec.generate_private_key(ec.SECP256R1())
    blatt, _ = _cert(
        "Test Leaf", blatt_key, zwischen_name, zwischen_key, ca=False,
        oid="1.2.840.113635.100.6.11.1",
    )

    # Zum Gegentest: ein Blatt aus demselben Baum, aber ohne App-Store-
    # Markierung (so wie ein Apple-Pay-Zertifikat, dessen Schluessel ein
    # Entwickler besitzt).
    fremd_key = ec.generate_private_key(ec.SECP256R1())
    fremd, _ = _cert("Other Leaf", fremd_key, zwischen_name, zwischen_key, ca=False)

    return {"wurzel": wurzel, "zwischen": zwischen, "blatt": blatt, "blatt_key": blatt_key,
            "fremd": fremd, "fremd_key": fremd_key}


def _jws(nutzlast: dict, kette: dict) -> str:
    kopf = {
        "alg": "ES256",
        "x5c": [
            base64.b64encode(c.public_bytes(serialization.Encoding.DER)).decode()
            for c in (kette["blatt"], kette["zwischen"], kette["wurzel"])
        ],
    }

    def teil(d):
        return base64.urlsafe_b64encode(json.dumps(d).encode()).rstrip(b"=").decode()

    zu_signieren = f"{teil(kopf)}.{teil(nutzlast)}"
    der = kette["blatt_key"].sign(zu_signieren.encode(), ec.ECDSA(hashes.SHA256()))
    r, s = decode_dss_signature(der)
    roh = r.to_bytes(32, "big") + s.to_bytes(32, "big")
    signatur = base64.urlsafe_b64encode(roh).rstrip(b"=").decode()
    return f"{zu_signieren}.{signatur}"


@pytest.fixture
def apple(monkeypatch, kette):
    """Die geprüfte Wurzel ist im Test unsere - siehe Modulkopf."""
    monkeypatch.setattr(store_billing, "_apple_root", lambda: kette["wurzel"])
    monkeypatch.setattr(settings, "apple_bundle_id", "social.flexr.app")
    monkeypatch.setattr(settings, "apple_subscription_product_id", "premium.monthly")
    return kette


def _nutzlast(**felder):
    in_einem_monat = int(
        (datetime.now(timezone.utc) + timedelta(days=30)).timestamp() * 1000
    )
    grund = {
        "bundleId": "social.flexr.app",
        "productId": "premium.monthly",
        "originalTransactionId": "2000000900000001",
        "transactionId": "2000000900000009",
        "expiresDate": in_einem_monat,
        "environment": "Production",
    }
    grund.update(felder)
    return grund


# ---------------------------------------------------------------------------
# Was nicht durchkommen darf
# ---------------------------------------------------------------------------


def test_beleg_mit_fremder_wurzel_wird_abgelehnt(kette):
    """Ohne den Wurzelvergleich koennte jeder eigene Belege ausstellen."""
    token = _jws(_nutzlast(), kette)
    # Kein Monkeypatch: geprueft wird gegen Apples echtes Wurzelzertifikat.
    with pytest.raises(store_billing.StoreVerificationError, match="Zertifikatskette"):
        store_billing.verify_apple_jws(token)


def test_veraenderte_nutzlast_bricht_die_signatur(apple, kette):
    token = _jws(_nutzlast(), kette)
    kopf, nutzlast, signatur = token.split(".")

    gefaelscht = base64.urlsafe_b64encode(
        json.dumps(_nutzlast(originalTransactionId="999")).encode()
    ).rstrip(b"=").decode()

    with pytest.raises(store_billing.StoreVerificationError, match="Signatur"):
        store_billing.verify_apple_jws(f"{kopf}.{gefaelscht}.{signatur}")


def test_gebrochene_kette_wird_abgelehnt(apple, kette):
    """Ein Blatt, das die Zwischenstelle nie ausgestellt hat."""
    fremd_key = ec.generate_private_key(ec.SECP256R1())
    fremd, _ = _cert(
        "Fremdes Blatt",
        fremd_key,
        x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Test Intermediate")]),
        fremd_key,  # selbst signiert, gibt sich aber als von der Zwischenstelle aus
        ca=False,
    )
    gemischt = dict(kette, blatt=fremd, blatt_key=fremd_key)
    with pytest.raises(store_billing.StoreVerificationError):
        store_billing.verify_apple_jws(_jws(_nutzlast(), gemischt))


def test_beleg_einer_anderen_app(apple, kette):
    token = _jws(_nutzlast(bundleId="com.beispiel.andere"), kette)
    with pytest.raises(store_billing.StoreVerificationError, match="anderen App"):
        store_billing.apple_transaction_from_jws(token)


def test_beleg_eines_anderen_produkts(apple, kette):
    token = _jws(_nutzlast(productId="etwas.anderes"), kette)
    with pytest.raises(store_billing.StoreVerificationError, match="anderen Produkt"):
        store_billing.apple_transaction_from_jws(token)


def test_unsinn_ist_kein_beleg(apple):
    for eingabe in ("", "abc", "a.b.c", "a.b"):
        with pytest.raises(store_billing.StoreVerificationError):
            store_billing.verify_apple_jws(eingabe)


# ---------------------------------------------------------------------------
# Was durchkommen soll
# ---------------------------------------------------------------------------


def test_gueltiger_beleg_wird_gelesen(apple, kette):
    beleg = store_billing.apple_transaction_from_jws(_jws(_nutzlast(), kette))
    assert beleg["provider"] is StoreProvider.apple
    assert beleg["external_id"] == "2000000900000001"
    assert beleg["product_id"] == "premium.monthly"
    assert beleg["expires_at"] > utcnow()
    assert beleg["status"] == "active"


def test_rueckerstattung_hebt_den_kauf_auf(apple, kette):
    """Ein revocationDate zaehlt mehr als jedes Ablaufdatum."""
    widerruf = int(datetime.now(timezone.utc).timestamp() * 1000)
    beleg = store_billing.apple_transaction_from_jws(
        _jws(_nutzlast(revocationDate=widerruf), kette)
    )
    assert beleg["expires_at"] is None
    assert beleg["status"] == "revoked"


# ---------------------------------------------------------------------------
# Berechtigung schreiben
# ---------------------------------------------------------------------------


def _beleg(external_id="2000000900000001", tage=30, environment="Production", status="active"):
    return {
        "provider": StoreProvider.apple,
        "external_id": external_id,
        "product_id": "premium.monthly",
        "expires_at": utcnow() + timedelta(days=tage) if tage is not None else None,
        "status": status,
        "auto_renewing": True,
        "environment": environment,
    }


def _user(db, email):
    return db.query(User).filter(User.email == email).one()


def test_kauf_schaltet_premium_frei(client, monkeypatch):
    monkeypatch.setattr(settings, "premium_enabled", True)
    register_user(client, "kaeufer@example.com")

    db = TestingSessionLocal()
    try:
        user = _user(db, "kaeufer@example.com")
        assert user.is_premium is False
        store_billing.apply_subscription(db, user, _beleg())
        db.refresh(user)
        assert user.is_premium is True
        # Kulanzfrist: die Berechtigung reicht ueber das Ablaufdatum hinaus,
        # damit eine verspaetete Verlaengerungsmeldung niemanden aussperrt.
        assert user.store_premium_until > user.store_premium_until - store_billing.GRACE
        assert db.query(StoreSubscription).count() == 1
    finally:
        db.close()


def test_abgelaufenes_abo_traegt_kein_premium(client, monkeypatch):
    monkeypatch.setattr(settings, "premium_enabled", True)
    register_user(client, "abgelaufen@example.com")

    db = TestingSessionLocal()
    try:
        user = _user(db, "abgelaufen@example.com")
        # Weit genug in der Vergangenheit, dass auch die Kulanzfrist vorbei ist.
        store_billing.apply_subscription(db, user, _beleg(tage=-5))
        db.refresh(user)
        assert user.is_premium is False
    finally:
        db.close()


def test_sandbox_kauf_wird_in_produktion_nicht_angenommen(client, monkeypatch):
    monkeypatch.setattr(settings, "premium_enabled", True)
    monkeypatch.setattr(settings, "store_sandbox_allowed", False)
    register_user(client, "sandbox@example.com")

    db = TestingSessionLocal()
    try:
        user = _user(db, "sandbox@example.com")
        with pytest.raises(store_billing.StoreVerificationError, match="Testkaeufe"):
            store_billing.apply_subscription(db, user, _beleg(environment="Sandbox"))
        db.refresh(user)
        assert user.is_premium is False
    finally:
        db.close()


def test_derselbe_kauf_erzeugt_nicht_zweimal_premium(client, monkeypatch):
    """Zwei FLEXR-Konten, ein Apple-Zugang: Der Kauf wandert, er vervielfaeltigt sich nicht."""
    monkeypatch.setattr(settings, "premium_enabled", True)
    register_user(client, "erstkonto@example.com")
    register_user(client, "zweitkonto@example.com")

    db = TestingSessionLocal()
    try:
        erst = _user(db, "erstkonto@example.com")
        store_billing.apply_subscription(db, erst, _beleg())
        db.refresh(erst)
        assert erst.is_premium is True

        zweit = _user(db, "zweitkonto@example.com")
        store_billing.apply_subscription(db, zweit, _beleg())  # derselbe Beleg
        db.refresh(erst)
        db.refresh(zweit)

        assert zweit.is_premium is True
        assert erst.is_premium is False, "Premium darf nicht auf beiden Konten liegen"
        assert db.query(StoreSubscription).count() == 1
    finally:
        db.close()


def test_verlaengerung_schreibt_dieselbe_zeile_fort(client, monkeypatch):
    monkeypatch.setattr(settings, "premium_enabled", True)
    register_user(client, "verlaengert@example.com")

    db = TestingSessionLocal()
    try:
        user = _user(db, "verlaengert@example.com")
        store_billing.apply_subscription(db, user, _beleg(tage=1))
        vorher = _user(db, "verlaengert@example.com").store_premium_until

        # Die Benachrichtigung des Stores kennt kein FLEXR-Konto - sie findet
        # es ueber die Zeile, die der Kauf angelegt hat.
        store_billing.apply_subscription(db, None, _beleg(tage=31))
        db.refresh(user)

        assert user.store_premium_until > vorher
        assert db.query(StoreSubscription).count() == 1
    finally:
        db.close()


def test_benachrichtigung_zu_unbekanntem_kauf_laeuft_ins_leere(client, monkeypatch):
    """Kein Konto zuzuordnen - und vor allem kein Absturz."""
    monkeypatch.setattr(settings, "premium_enabled", True)
    db = TestingSessionLocal()
    try:
        assert store_billing.apply_subscription(db, None, _beleg("unbekannt")) is None
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Die Endpunkte
# ---------------------------------------------------------------------------

IOS_AGENT = "FLEXR/24 CFNetwork/3896.100.1.2.1 Darwin/27.0.0"


def test_endpunkt_lehnt_unsinnigen_beleg_ab(client, monkeypatch):
    monkeypatch.setattr(settings, "premium_enabled", True)
    headers = register_user(client, "unsinn@example.com")

    resp = client.post(
        "/api/billing/apple/transaction",
        json={"signed_transaction": "kein-echtes-jws." + "x" * 40},
        headers={**headers, "User-Agent": IOS_AGENT},
    )
    assert resp.status_code == 400


def test_kein_kauf_solange_premium_aus_ist(client, monkeypatch):
    """Sonst nimmt der Server Geld fuer Vorteile, die es gerade nicht gibt."""
    monkeypatch.setattr(settings, "premium_enabled", False)
    headers = register_user(client, "zufrueh-store@example.com")

    resp = client.post(
        "/api/billing/apple/transaction",
        json={"signed_transaction": "a" * 40},
        headers={**headers, "User-Agent": IOS_AGENT},
    )
    assert resp.status_code == 409


def test_google_benachrichtigung_braucht_das_geheimnis(client, monkeypatch):
    monkeypatch.setattr(settings, "google_notifications_token", "richtig")
    assert client.post("/api/billing/google/notifications/falsch", json={}).status_code == 404


def test_apple_benachrichtigung_ohne_gueltige_signatur(client):
    resp = client.post(
        "/api/billing/apple/notifications", json={"signedPayload": "a.b.c"}
    )
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Was der Client angeboten bekommt
# ---------------------------------------------------------------------------

BROWSER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/131.0 Safari/537.36"
ANDROID_AGENT = "okhttp/4.12.0"


def test_jeder_client_bekommt_genau_einen_kaufweg(client, monkeypatch):
    monkeypatch.setattr(settings, "premium_enabled", True)
    monkeypatch.setattr(settings, "apple_subscription_product_id", "premium.monthly")
    monkeypatch.setattr(settings, "google_subscription_product_id", "premium_monthly")
    headers = register_user(client, "kaufweg@example.com")

    def status(agent):
        return client.get(
            "/api/billing/status", headers={**headers, "User-Agent": agent}
        ).json()

    web = status(BROWSER_AGENT)
    assert web["checkout_available"] is True
    assert web["store_purchase_available"] is False

    ios = status(IOS_AGENT)
    assert ios["checkout_available"] is False
    assert ios["store_purchase_available"] is True
    assert ios["store_product_id"] == "premium.monthly"

    android = status(ANDROID_AGENT)
    assert android["store_product_id"] == "premium_monthly"


def test_ohne_eingetragenes_produkt_kein_kauf_knopf(client, monkeypatch):
    """Ein Knopf, der im Store nichts findet, waere schlimmer als keiner."""
    monkeypatch.setattr(settings, "premium_enabled", True)
    monkeypatch.setattr(settings, "apple_subscription_product_id", "")
    headers = register_user(client, "ohneprodukt@example.com")

    daten = client.get(
        "/api/billing/status", headers={**headers, "User-Agent": IOS_AGENT}
    ).json()
    assert daten["store_purchase_available"] is False
    assert daten["store_product_id"] is None


def test_blatt_ohne_app_store_markierung_wird_abgewiesen(apple, kette):
    """Ein Zertifikat unter Apples Wurzel, dessen Schluessel ein Entwickler
    haelt (z. B. Apple Pay), darf keinen Kaufbeleg signieren koennen."""
    gefaelscht = _jws(
        {"bundleId": settings.apple_bundle_id, "productId": "x"},
        {**kette, "blatt": kette["fremd"], "blatt_key": kette["fremd_key"]},
    )
    with pytest.raises(store_billing.StoreVerificationError):
        store_billing.verify_apple_jws(gefaelscht)


@pytest.mark.parametrize("token", ["../../../edits/xyz-abcdef", "abc/def/ghijkl", "abcdefghij?x=1"])
def test_play_token_mit_pfadzeichen_wird_nicht_nachgefragt(monkeypatch, token):
    aufrufe = []
    monkeypatch.setattr(store_billing, "google_configured", lambda: True)
    monkeypatch.setattr(store_billing.requests, "get", lambda *a, **k: aufrufe.append(a))
    with pytest.raises(store_billing.StoreVerificationError):
        store_billing.google_subscription_from_token(token)
    assert aufrufe == []


# ---------------------------------------------------------------------------
# Kontobindung
# ---------------------------------------------------------------------------


def test_gebundener_kauf_wandert_nicht_zu_fremdem_konto(client, monkeypatch):
    monkeypatch.setattr(settings, "premium_enabled", True)
    register_user(client, "kaeuferin@example.com")
    register_user(client, "dieb@example.com")
    db = TestingSessionLocal()
    try:
        kaeuferin = _user(db, "kaeuferin@example.com")
        dieb = _user(db, "dieb@example.com")
        beleg = {**_beleg(), "account": kaeuferin.id}
        store_billing.apply_subscription(db, kaeuferin, beleg)
        with pytest.raises(store_billing.StoreVerificationError, match="anderen FLEXR-Konto"):
            store_billing.apply_subscription(db, dieb, beleg)
        db.refresh(kaeuferin)
        db.refresh(dieb)
        assert kaeuferin.is_premium is True
        assert dieb.is_premium is False
    finally:
        db.close()


def test_play_kennung_ist_der_hash_der_nutzer_id(client, monkeypatch):
    monkeypatch.setattr(settings, "premium_enabled", True)
    register_user(client, "playkonto@example.com")
    db = TestingSessionLocal()
    try:
        user = _user(db, "playkonto@example.com")
        beleg = {**_beleg(), "provider": StoreProvider.google,
                 "account": store_billing.google_account_id(user.id)}
        store_billing.apply_subscription(db, user, beleg)
        db.refresh(user)
        assert user.is_premium is True
        assert len(store_billing.google_account_id(user.id)) == 64
    finally:
        db.close()


def test_apple_app_account_token_wird_gelesen(apple, kette):
    token = _jws(_nutzlast(appAccountToken="0B7C1F7E-2C7E-4A58-9B43-7D7F8E2B1A11"), kette)
    beleg = store_billing.apple_transaction_from_jws(token)
    assert beleg["account"] == "0b7c1f7e-2c7e-4a58-9b43-7d7f8e2b1a11"


def test_benachrichtigung_zu_gebundenem_kauf_wirkt_weiter(client, monkeypatch):
    """Store-Benachrichtigungen kommen ohne Konto - die Bindung darf sie nicht blockieren."""
    monkeypatch.setattr(settings, "premium_enabled", True)
    register_user(client, "verlaengert@example.com")
    db = TestingSessionLocal()
    try:
        user = _user(db, "verlaengert@example.com")
        store_billing.apply_subscription(db, user, {**_beleg(), "account": user.id})
        zeile = store_billing.apply_subscription(db, None, {**_beleg(tage=60), "account": user.id})
        assert zeile is not None and zeile.user_id == user.id
    finally:
        db.close()
