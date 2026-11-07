"""Restore Key der Android-App: Anmeldung nach dem Geraetewechsel.

Die Tests spielen den Credential Manager mit einem echten P-256-Schluessel
nach (``FakeAuthenticator``): Registrierungs- und Anmeldeantwort entstehen
genau so, wie Android sie baut (clientDataJSON, authenticatorData,
Attestation "none", DER-Signatur) - gepruefte Kryptografie, keine Attrappe.
"""

import base64
import hashlib
import json
import os
import struct
from datetime import timedelta

import pytest
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec

from app import restore_keys
from app.config import settings
from app.models import RestoreChallenge, RestoreCredential, User
from app.timeutil import utcnow
from tests.conftest import DEFAULT_USER, TestingSessionLocal, register_raw, register_user

ORIGIN = sorted(restore_keys.allowed_origins())[0]
DEVICE_A = "geraet-alt-0001"
DEVICE_B = "geraet-neu-0002"


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _cbor(value) -> bytes:
    """Kleiner CBOR-Schreiber fuer die Testdaten."""

    def head(major, n):
        if n < 24:
            return bytes([major << 5 | n])
        if n < 256:
            return bytes([major << 5 | 24, n])
        if n < 65536:
            return bytes([major << 5 | 25]) + struct.pack(">H", n)
        return bytes([major << 5 | 26]) + struct.pack(">I", n)

    if isinstance(value, bool) or value is None:
        return bytes([0xF5 if value is True else 0xF4 if value is False else 0xF6])
    if isinstance(value, int):
        return head(0, value) if value >= 0 else head(1, -1 - value)
    if isinstance(value, bytes):
        return head(2, len(value)) + value
    if isinstance(value, str):
        raw = value.encode()
        return head(3, len(raw)) + raw
    if isinstance(value, list):
        return head(4, len(value)) + b"".join(_cbor(v) for v in value)
    if isinstance(value, dict):
        return head(5, len(value)) + b"".join(_cbor(k) + _cbor(v) for k, v in value.items())
    raise TypeError(value)


class FakeAuthenticator:
    """Ein Restore Key, wie ihn der Credential Manager anlegt."""

    def __init__(self, origin=ORIGIN, rp_id=None):
        self.key = ec.generate_private_key(ec.SECP256R1())
        self.credential_id = os.urandom(32)
        self.origin = origin
        self.rp_id = rp_id or settings.webauthn_rp_id
        self.user_handle = None

    def _rp_hash(self):
        return hashlib.sha256(self.rp_id.encode()).digest()

    def _client_data(self, typ, challenge):
        return json.dumps(
            {"type": typ, "challenge": challenge, "origin": self.origin,
             "androidPackageName": "flexr.social.app"}
        ).encode()

    def create(self, options_json: str) -> str:
        options = json.loads(options_json)
        self.user_handle = options["user"]["id"]
        numbers = self.key.public_key().public_numbers()
        cose = {1: 2, 3: -7, -1: 1, -2: numbers.x.to_bytes(32, "big"),
                -3: numbers.y.to_bytes(32, "big")}
        auth_data = (
            self._rp_hash() + bytes([0x41]) + struct.pack(">I", 0)
            + bytes(16) + struct.pack(">H", len(self.credential_id)) + self.credential_id
            + _cbor(cose)
        )
        attestation = _cbor({"fmt": "none", "attStmt": {}, "authData": auth_data})
        return json.dumps({
            "id": _b64(self.credential_id),
            "rawId": _b64(self.credential_id),
            "type": "public-key",
            "response": {
                "clientDataJSON": _b64(self._client_data("webauthn.create", options["challenge"])),
                "attestationObject": _b64(attestation),
                "transports": ["internal"],
            },
            "clientExtensionResults": {},
        })

    def get(self, options_json: str, sign_count=1, tamper=False) -> str:
        options = json.loads(options_json)
        assert options["allowCredentials"] == []
        client_data = self._client_data("webauthn.get", options["challenge"])
        # Restore Keys werden still eingeloest: weder UP noch UV gesetzt.
        auth_data = self._rp_hash() + bytes([0x00]) + struct.pack(">I", sign_count)
        signature = self.key.sign(
            auth_data + hashlib.sha256(client_data).digest(), ec.ECDSA(hashes.SHA256())
        )
        if tamper:
            client_data = client_data.replace(b"webauthn.get", b"webauthn.get ")
        return json.dumps({
            "id": _b64(self.credential_id),
            "rawId": _b64(self.credential_id),
            "type": "public-key",
            "response": {
                "clientDataJSON": _b64(client_data),
                "authenticatorData": _b64(auth_data),
                "signature": _b64(signature),
                "userHandle": self.user_handle,
            },
        })


def _with_device(headers, device):
    return {**headers, "X-Device-Id": device}


def _anlegen(client, headers, auth=None, device=DEVICE_A):
    auth = auth or FakeAuthenticator()
    h = _with_device(headers, device)
    opts = client.post("/api/auth/restore-key/options", headers=h)
    assert opts.status_code == 200, opts.text
    resp = client.post(
        "/api/auth/restore-key", headers=h,
        json={"registration_response_json": auth.create(opts.json()["request_json"])},
    )
    return auth, resp


def _einloesen(client, auth, device=DEVICE_B, **kwargs):
    opts = client.post("/api/auth/restore-key/login/options")
    assert opts.status_code == 200, opts.text
    return client.post(
        "/api/auth/restore-key/login", headers={"X-Device-Id": device},
        json={"authentication_response_json": auth.get(opts.json()["request_json"], **kwargs)},
    )


def _keys(user_id=None):
    db = TestingSessionLocal()
    try:
        q = db.query(RestoreCredential)
        if user_id:
            q = q.filter(RestoreCredential.user_id == user_id)
        return q.all()
    finally:
        db.close()


def _me(client, headers):
    return client.get("/api/profiles/me", headers=headers).json()


# ---------------------------------------------------------------------------
# Der Normalfall
# ---------------------------------------------------------------------------


def test_anlegen_und_auf_dem_neuen_geraet_einloesen(client):
    headers = register_user(client, "restore.normal@example.com")
    auth, resp = _anlegen(client, headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["credential_id"] == _b64(auth.credential_id)

    keys = _keys()
    assert len(keys) == 1 and keys[0].device_id == DEVICE_A

    login = _einloesen(client, auth)
    assert login.status_code == 200, login.text
    neu = {"Authorization": f"Bearer {login.json()['access_token']}"}
    assert _me(client, neu)["id"] == _me(client, headers)["id"]
    assert _keys()[0].last_used_at is not None


def test_optionen_entsprechen_den_vorgaben_von_google(client):
    headers = register_raw(client, "restore.optionen@example.com")
    opts = json.loads(
        client.post("/api/auth/restore-key/options", headers=headers).json()["request_json"]
    )
    assert opts["rp"]["id"] == "flexr.social"
    assert opts["attestation"] == "none"
    assert {"type": "public-key", "alg": -7} in opts["pubKeyCredParams"]
    assert {"type": "public-key", "alg": -257} in opts["pubKeyCredParams"]
    assert opts["authenticatorSelection"]["residentKey"] == "required"
    # base64url ohne Auffuellung, sonst wirft der Credential Manager
    assert "=" not in opts["challenge"] and "=" not in opts["user"]["id"]
    # keine Klardaten im Schluessel, der ins Google-Backup wandert
    assert "restore.optionen" not in json.dumps(opts)

    login_opts = json.loads(
        client.post("/api/auth/restore-key/login/options").json()["request_json"]
    )
    assert login_opts["rpId"] == "flexr.social"
    assert login_opts["allowCredentials"] == []


def test_auch_ein_konto_in_der_pruefung_kommt_hinein(client):
    """Wie beim Passwort-Login: Die Pruefung entscheidet ueber das Deck,
    nicht ueber die Anmeldung."""
    headers = register_raw(client, "restore.pruefung@example.com")
    auth, resp = _anlegen(client, headers)
    assert resp.status_code == 200
    assert _einloesen(client, auth).status_code == 200


def test_anlegen_nur_angemeldet(client):
    assert client.post("/api/auth/restore-key/options").status_code == 401
    assert client.post(
        "/api/auth/restore-key", json={"registration_response_json": "{}"}
    ).status_code == 401


# ---------------------------------------------------------------------------
# Was abgewiesen werden muss
# ---------------------------------------------------------------------------


def test_challenge_gilt_nur_einmal(client):
    headers = register_user(client, "restore.einmal@example.com")
    auth, _ = _anlegen(client, headers)
    opts = client.post("/api/auth/restore-key/login/options").json()["request_json"]
    antwort = auth.get(opts)
    erst = client.post("/api/auth/restore-key/login", json={"authentication_response_json": antwort})
    assert erst.status_code == 200
    noch_mal = client.post("/api/auth/restore-key/login", json={"authentication_response_json": antwort})
    assert noch_mal.status_code == 401
    assert noch_mal.json()["detail"]["code"] == "restore_key_invalid"


def test_abgelaufene_challenge(client):
    headers = register_user(client, "restore.alt@example.com")
    auth, _ = _anlegen(client, headers)
    opts = client.post("/api/auth/restore-key/login/options").json()["request_json"]
    db = TestingSessionLocal()
    try:
        for c in db.query(RestoreChallenge).all():
            c.expires_at = utcnow() - timedelta(seconds=1)
        db.commit()
    finally:
        db.close()
    resp = client.post(
        "/api/auth/restore-key/login", json={"authentication_response_json": auth.get(opts)}
    )
    assert resp.status_code == 401


def test_falsche_signatur(client):
    headers = register_user(client, "restore.signatur@example.com")
    auth, _ = _anlegen(client, headers)
    assert _einloesen(client, auth, tamper=True).status_code == 401


def test_fremder_schluessel_mit_gestohlener_id(client):
    headers = register_user(client, "restore.fremd@example.com")
    echt, _ = _anlegen(client, headers)
    faelscher = FakeAuthenticator()
    faelscher.credential_id = echt.credential_id
    faelscher.user_handle = echt.user_handle
    assert _einloesen(client, faelscher).status_code == 401


def test_unbekannter_schluessel(client):
    auth = FakeAuthenticator()
    auth.user_handle = _b64(b"irgendwer")
    assert _einloesen(client, auth).status_code == 401


def test_fremde_app_beim_anlegen(client):
    headers = register_user(client, "restore.herkunft@example.com")
    _, resp = _anlegen(client, headers, auth=FakeAuthenticator(origin="https://evil.example"))
    assert resp.status_code == 400
    assert _keys() == []


def test_falsche_rp_id_beim_anlegen(client):
    headers = register_user(client, "restore.rpid@example.com")
    _, resp = _anlegen(client, headers, auth=FakeAuthenticator(rp_id="evil.example"))
    assert resp.status_code == 400


def test_challenge_eines_anderen_kontos(client):
    a = register_user(client, "restore.konto.a@example.com")
    b = register_user(client, "restore.konto.b@example.com")
    opts = client.post("/api/auth/restore-key/options", headers=a).json()["request_json"]
    resp = client.post(
        "/api/auth/restore-key", headers=b,
        json={"registration_response_json": FakeAuthenticator().create(opts)},
    )
    assert resp.status_code == 400


def test_login_challenge_taugt_nicht_zum_anlegen(client):
    headers = register_user(client, "restore.zweck@example.com")
    opts = json.loads(client.post("/api/auth/restore-key/login/options").json()["request_json"])
    opts["user"] = {"id": _b64(b"x")}
    resp = client.post(
        "/api/auth/restore-key", headers=headers,
        json={"registration_response_json": FakeAuthenticator().create(json.dumps(opts))},
    )
    assert resp.status_code == 400


@pytest.mark.parametrize("muell", [
    "kein json",
    "[]",
    json.dumps({"response": {"clientDataJSON": "!!!", "attestationObject": "AA"}}),
    json.dumps({"response": {"clientDataJSON": _b64(b"{}"), "attestationObject": _b64(b"\xff")}}),
])
def test_kaputte_antworten_sind_400_und_kein_absturz(client, muell):
    headers = register_user(client, f"restore.muell{abs(hash(muell))}@example.com")
    resp = client.post(
        "/api/auth/restore-key", headers=headers, json={"registration_response_json": muell}
    )
    assert resp.status_code == 400
    login = client.post("/api/auth/restore-key/login", json={"authentication_response_json": muell})
    assert login.status_code == 401


def test_cbor_leser_weist_unsinn_ab():
    for data in (b"", b"\x5f", b"\xa1", b"\x9f\xff", b"\x01\x02", b"\x81" * 20 + b"\x01"):
        with pytest.raises(restore_keys.RestoreKeyError):
            restore_keys.cbor_decode(data)
    assert restore_keys.cbor_decode(_cbor({1: 2, -2: b"ab", "x": [True, None]})) == {
        1: 2, -2: b"ab", "x": [True, None]
    }


# ---------------------------------------------------------------------------
# Dieselben Kontoregeln wie beim Passwort-Login
# ---------------------------------------------------------------------------


def test_gesperrtes_konto(client):
    headers = register_user(client, "restore.gesperrt@example.com")
    auth, _ = _anlegen(client, headers)
    user_id = _me(client, headers)["id"]
    db = TestingSessionLocal()
    try:
        db.query(User).filter(User.id == user_id).first().is_banned = True
        db.commit()
    finally:
        db.close()
    resp = _einloesen(client, auth)
    assert resp.status_code == 403
    assert "access_token" not in resp.text


def test_kontoloeschung_verwirft_die_schluessel(client):
    headers = register_user(client, "restore.geloescht@example.com")
    auth, _ = _anlegen(client, headers)
    resp = client.request(
        "DELETE", "/api/profiles/me", headers=headers,
        json={"password": DEFAULT_USER["password"]},
    )
    assert resp.status_code == 200, resp.text
    assert _keys() == []
    assert _einloesen(client, auth).status_code == 401


def test_geloeschtes_konto_mit_restschluessel(client):
    """Auch ein Schluessel, der die Loeschung irgendwie ueberlebt hat, fuehrt
    nicht hinein - reaktivieren geht nur mit Passwort."""
    headers = register_user(client, "restore.rest@example.com")
    auth, _ = _anlegen(client, headers)
    user_id = _me(client, headers)["id"]
    db = TestingSessionLocal()
    try:
        db.query(User).filter(User.id == user_id).first().deleted_at = utcnow()
        db.commit()
    finally:
        db.close()
    assert _einloesen(client, auth).status_code == 401
    assert _keys() == []


def test_passwortwechsel_verwirft_die_schluessel(client):
    headers = register_user(client, "restore.passwort@example.com")
    auth, _ = _anlegen(client, headers)
    resp = client.post(
        "/api/profiles/me/password", headers=headers,
        json={"current_password": DEFAULT_USER["password"], "new_password": "ganzneues123"},
    )
    assert resp.status_code == 200, resp.text
    assert _keys() == []
    assert _einloesen(client, auth).status_code == 401


def test_schluessel_von_vor_dem_passwortwechsel(client):
    """password_changed_at-Regel wie bei security.token_predates_password_change."""
    headers = register_user(client, "restore.vorher@example.com")
    auth, _ = _anlegen(client, headers)
    user_id = _me(client, headers)["id"]
    db = TestingSessionLocal()
    try:
        db.query(User).filter(User.id == user_id).first().password_changed_at = (
            utcnow() + timedelta(seconds=1)
        )
        db.commit()
    finally:
        db.close()
    assert _einloesen(client, auth).status_code == 401
    assert _keys() == []


# ---------------------------------------------------------------------------
# Abmelden, Ersetzen, Fristen
# ---------------------------------------------------------------------------


def test_abmelden_verwirft_nur_den_schluessel_dieses_geraets(client):
    headers = register_user(client, "restore.abmelden@example.com")
    alt, _ = _anlegen(client, headers, device=DEVICE_A)
    neu, _ = _anlegen(client, headers, device=DEVICE_B)
    assert len(_keys()) == 2

    resp = client.post(
        "/api/auth/restore-key/delete", headers=_with_device(headers, DEVICE_A), json={}
    )
    assert resp.status_code == 200
    assert [k.device_id for k in _keys()] == [DEVICE_B]
    assert _einloesen(client, alt).status_code == 401
    assert _einloesen(client, neu).status_code == 200


def test_abmelden_ueber_die_credential_id(client):
    headers = register_user(client, "restore.credid@example.com")
    auth, resp = _anlegen(client, headers)
    client.post(
        "/api/auth/restore-key/delete", headers=headers,
        json={"credential_id": resp.json()["credential_id"]},
    )
    assert _keys() == []


def test_abmelden_trifft_kein_fremdes_konto(client):
    a = register_user(client, "restore.fremd.a@example.com")
    b = register_user(client, "restore.fremd.b@example.com")
    _, resp = _anlegen(client, a)
    client.post(
        "/api/auth/restore-key/delete", headers=_with_device(b, DEVICE_A),
        json={"credential_id": resp.json()["credential_id"]},
    )
    assert len(_keys()) == 1


def test_neuer_schluessel_ersetzt_den_alten_desselben_geraets(client):
    headers = register_user(client, "restore.ersetzen@example.com")
    alt, _ = _anlegen(client, headers)
    neu, _ = _anlegen(client, headers)
    keys = _keys()
    assert len(keys) == 1 and keys[0].credential_id == _b64(neu.credential_id)
    assert _einloesen(client, alt).status_code == 401


def test_hoechstens_fuenf_schluessel_je_konto(client):
    headers = register_user(client, "restore.fuenf@example.com")
    for i in range(restore_keys.MAX_KEYS_PER_USER + 2):
        _, resp = _anlegen(client, headers, device=f"geraet-{i:04d}-xx")
        assert resp.status_code == 200
    assert len(_keys()) == restore_keys.MAX_KEYS_PER_USER


def test_loeschlauf_entfernt_alte_schluessel_und_challenges(client):
    from app import cleanup

    headers = register_user(client, "restore.frist@example.com")
    _anlegen(client, headers, device=DEVICE_A)
    _anlegen(client, headers, device=DEVICE_B)
    client.post("/api/auth/restore-key/login/options")
    db = TestingSessionLocal()
    try:
        alt = db.query(RestoreCredential).filter_by(device_id=DEVICE_A).one()
        alt.created_at = utcnow() - timedelta(days=restore_keys.RESTORE_KEY_MAX_AGE_DAYS + 1)
        for c in db.query(RestoreChallenge).all():
            c.expires_at = utcnow() - timedelta(seconds=1)
        db.commit()
        assert cleanup.purge_restore_keys(db) == 1
        assert db.query(RestoreChallenge).count() == 0
    finally:
        db.close()
    assert [k.device_id for k in _keys()] == [DEVICE_B]


def test_herkunft_aus_den_fingerprints():
    # Upload-Key BC:64:...:80, wie in assetlinks.json
    erwartet = "android:apk-key-hash:" + _b64(bytes.fromhex(
        "BC64AD3F273EB22D381ED7CB46DE676E6A1CC63B18C964FAABA3DDA5140E7980"
    ))
    assert erwartet in restore_keys.allowed_origins()
    assert len(restore_keys.allowed_origins()) == 2
