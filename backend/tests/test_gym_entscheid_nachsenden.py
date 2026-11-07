"""scripts/gym_entscheid_nachsenden.py: zeigt ohne Schalter nur an, sendet mit
--senden jede Mail hoechstens einmal und laesst offene Vorschlaege aus."""

import importlib.util
import sys
from pathlib import Path

from app import mailer
from tests.conftest import create_admin, register_user

SKRIPT = Path(__file__).resolve().parents[1] / "scripts" / "gym_entscheid_nachsenden.py"


def _lauf(monkeypatch, *argv):
    spec = importlib.util.spec_from_file_location("nachsenden", SKRIPT)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    monkeypatch.setattr(sys, "argv", ["x", *argv])
    modul.main()


def test_nachsenden(client, monkeypatch, capsys):
    gesendet = []
    monkeypatch.setattr(mailer, "send_gym_decision",
                        lambda *a: gesendet.append(a) or True)
    for name, plz in (("Altgym Frei", "4600"), ("Altgym Weg", "4601"), ("Altgym Offen", "4602")):
        client.post("/api/gyms/suggest", json={"name": name, "street": "Gasse",
                                               "house_number": "1", "plz": plz, "city": "Wels"})
    register_user(client, "frei@example.com", gym="Altgym Frei")
    register_user(client, "weg@example.com", gym="Altgym Weg")
    register_user(client, "offen@example.com", gym="Altgym Offen")
    admin, _ = create_admin(client, email="admin-nach@example.com")
    ids = {g["name"]: g["id"] for g in client.get("/api/admin/gyms?status=pending", headers=admin).json()}
    # Entscheidung "wie vor dem 07.11.": Status direkt setzen, ohne Mail
    from app.models import Gym, GymStatus
    from tests.conftest import TestingSessionLocal
    db = TestingSessionLocal()
    db.get(Gym, ids["Altgym Frei"]).status = GymStatus.approved
    db.get(Gym, ids["Altgym Weg"]).status = GymStatus.rejected
    db.commit(); db.close()

    _lauf(monkeypatch)
    assert gesendet == []
    assert "Nur angezeigt" in capsys.readouterr().out

    _lauf(monkeypatch, "--senden")
    assert sorted((a[0], a[3]) for a in gesendet) == [("frei@example.com", True), ("weg@example.com", False)]

    _lauf(monkeypatch, "--senden")
    assert len(gesendet) == 2
