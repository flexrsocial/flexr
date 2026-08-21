"""Der Abostatus muss auch wieder erloeschen koennen.

Bis dahin setzte der Webhook ``is_subscribed`` nur auf True und nie zurueck.
Wer ueber das Stripe-Billing-Portal kuendigte, behielt den Zugang dauerhaft -
``is_active_member()`` ist das Zugangstor in security.py.

Getestet wird ``handle_stripe_event`` direkt, ohne Signaturpruefung: Die
Signatur gehoert Stripe, nicht uns, und liesse sich hier nur nachbauen.
"""

from datetime import datetime, timedelta

from app.models import User
from app.routers.billing import handle_stripe_event
from tests.conftest import TestingSessionLocal, register_user


def _user_row(user_id):
    db = TestingSessionLocal()
    try:
        return db.query(User).filter(User.id == user_id).first()
    finally:
        db.close()


def _setup_subscriber(client, email="abonnent@example.com", **felder):
    """Legt ein Konto mit laufendem Abo an und liefert seine ID."""
    headers = register_user(client, email)
    user_id = client.get("/api/profiles/me", headers=headers).json()["id"]

    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        user.is_subscribed = True
        user.stripe_customer_id = "cus_test123"
        user.stripe_subscription_id = "sub_test123"
        for name, wert in felder.items():
            setattr(user, name, wert)
        db.commit()
    finally:
        db.close()
    return user_id


def _event(event_type, obj, event_id=None, previous=None):
    data = {"object": obj}
    if previous is not None:
        data["previous_attributes"] = previous
    event = {"type": event_type, "data": data}
    if event_id is not None:
        event["id"] = event_id
    return event


def _mit_db(fn):
    db = TestingSessionLocal()
    try:
        fn(db)
        db.commit()
    finally:
        db.close()


def test_checkout_schaltet_das_abo_frei(client):
    """Regressionsschutz fuer den Weg, der vorher schon funktionierte."""
    headers = register_user(client, "neu@example.com")
    user_id = client.get("/api/profiles/me", headers=headers).json()["id"]

    _mit_db(lambda db: handle_stripe_event(
        _event("checkout.session.completed", {
            "client_reference_id": user_id,
            "customer": "cus_neu",
            "subscription": "sub_neu",
        }),
        db,
    ))

    user = _user_row(user_id)
    assert user.is_subscribed is True
    assert user.stripe_customer_id == "cus_neu"
    assert user.stripe_subscription_id == "sub_neu"


def test_checkout_webhook_traegt_die_abo_id_bei_der_checkout_erklaerung_nach(client):
    """Bei der Checkout-Anfrage selbst ist die Abo-ID noch nicht bekannt - der
    Webhook muss sie der zuvor angelegten Erklaerung nachtragen."""
    from app.models import CheckoutConsent

    headers = register_user(client, "nachtrag@example.com")
    user_id = client.get("/api/profiles/me", headers=headers).json()["id"]

    db = TestingSessionLocal()
    try:
        db.add(CheckoutConsent(
            user_id=user_id,
            immediate_start_version="2026-08-17",
            withdrawal_ack_version="2026-08-17",
        ))
        db.commit()
    finally:
        db.close()

    _mit_db(lambda db: handle_stripe_event(
        _event("checkout.session.completed", {
            "client_reference_id": user_id,
            "customer": "cus_nachtrag",
            "subscription": "sub_nachtrag",
        }),
        db,
    ))

    db = TestingSessionLocal()
    try:
        eintrag = db.query(CheckoutConsent).filter(CheckoutConsent.user_id == user_id).one()
        assert eintrag.stripe_subscription_id == "sub_nachtrag"
        assert eintrag.stripe_customer_id == "cus_nachtrag"
    finally:
        db.close()


def test_geloeschtes_abo_entzieht_den_zugang(client):
    """Der eigentliche Fehler: Kuendigung blieb folgenlos."""
    user_id = _setup_subscriber(client)

    _mit_db(lambda db: handle_stripe_event(
        _event("customer.subscription.deleted", {
            "id": "sub_test123",
            "customer": "cus_test123",
            "status": "canceled",
        }),
        db,
    ))

    assert _user_row(user_id).is_subscribed is False


def test_nach_kuendigung_und_abgelaufenem_probemonat_ist_das_konto_inaktiv(client):
    """Zusammenspiel mit dem Zugangstor: erst beides zusammen sperrt wirklich."""
    user_id = _setup_subscriber(
        client, trial_ends_at=datetime.utcnow() - timedelta(days=1)
    )
    assert _user_row(user_id).is_active_member() is True

    _mit_db(lambda db: handle_stripe_event(
        _event("customer.subscription.deleted", {
            "id": "sub_test123",
            "customer": "cus_test123",
            "status": "canceled",
        }),
        db,
    ))

    assert _user_row(user_id).is_active_member() is False


def test_laufender_probemonat_ueberlebt_die_kuendigung(client):
    """Wer im Probemonat kuendigt, behaelt ihn bis zum Ende."""
    user_id = _setup_subscriber(
        client, trial_ends_at=datetime.utcnow() + timedelta(days=10)
    )

    _mit_db(lambda db: handle_stripe_event(
        _event("customer.subscription.deleted", {
            "id": "sub_test123",
            "customer": "cus_test123",
            "status": "canceled",
        }),
        db,
    ))

    user = _user_row(user_id)
    assert user.is_subscribed is False
    assert user.is_active_member() is True


def test_status_canceled_im_update_entzieht_ebenfalls(client):
    user_id = _setup_subscriber(client)

    _mit_db(lambda db: handle_stripe_event(
        _event("customer.subscription.updated", {
            "id": "sub_test123",
            "customer": "cus_test123",
            "status": "canceled",
        }),
        db,
    ))

    assert _user_row(user_id).is_subscribed is False


def test_past_due_sperrt_nicht(client):
    """Stripe wiederholt fehlgeschlagene Abbuchungen tagelang. Waehrend dieser
    Zeit auszusperren, waere eine Sackgasse ohne eigenes Zutun."""
    user_id = _setup_subscriber(client)

    _mit_db(lambda db: handle_stripe_event(
        _event("customer.subscription.updated", {
            "id": "sub_test123",
            "customer": "cus_test123",
            "status": "past_due",
        }),
        db,
    ))

    assert _user_row(user_id).is_subscribed is True


def test_fehlgeschlagene_zahlung_sperrt_nicht(client):
    user_id = _setup_subscriber(client)

    _mit_db(lambda db: handle_stripe_event(
        _event("invoice.payment_failed", {
            "customer": "cus_test123",
            "subscription": "sub_test123",
        }),
        db,
    ))

    assert _user_row(user_id).is_subscribed is True


def test_wiederaufnahme_stellt_den_zugang_wieder_her(client):
    user_id = _setup_subscriber(client)
    _mit_db(lambda db: handle_stripe_event(
        _event("customer.subscription.deleted",
               {"id": "sub_test123", "customer": "cus_test123"}),
        db,
    ))
    assert _user_row(user_id).is_subscribed is False

    _mit_db(lambda db: handle_stripe_event(
        _event("customer.subscription.updated", {
            "id": "sub_test123",
            "customer": "cus_test123",
            "status": "active",
        }),
        db,
    ))

    assert _user_row(user_id).is_subscribed is True


def test_zuordnung_ueber_die_kunden_id_wenn_die_abo_id_fehlt(client):
    """Abo-Ereignisse tragen kein client_reference_id. Ist die Abo-ID noch
    nicht gespeichert, muss die Kunden-ID greifen - und die Abo-ID nachtragen."""
    headers = register_user(client, "ohne-abo-id@example.com")
    user_id = client.get("/api/profiles/me", headers=headers).json()["id"]
    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        user.stripe_customer_id = "cus_nur_kunde"
        user.stripe_subscription_id = None
        db.commit()
    finally:
        db.close()

    _mit_db(lambda db: handle_stripe_event(
        _event("customer.subscription.updated", {
            "id": "sub_nachgetragen",
            "customer": "cus_nur_kunde",
            "status": "active",
        }),
        db,
    ))

    user = _user_row(user_id)
    assert user.is_subscribed is True
    assert user.stripe_subscription_id == "sub_nachgetragen"


def test_checkout_ohne_erklaerung_zum_leistungsbeginn_wird_abgelehnt(client):
    """§ 10 FAGG: ohne die ausdrückliche Erklärung darf kein Checkout starten."""
    headers = register_user(client, "ohne-erklaerung@example.com")

    resp = client.post(
        "/api/billing/checkout",
        json={"immediate_start": False, "withdrawal_ack": True},
        headers=headers,
    )
    assert resp.status_code == 422

    resp_ohne_feld = client.post("/api/billing/checkout", json={}, headers=headers)
    assert resp_ohne_feld.status_code == 422


def test_checkout_ohne_kenntnisnahme_erloeschen_wird_abgelehnt(client):
    """Die zweite Erklärung (§ 18 Abs. 1 Z 1 FAGG) ist eine eigene, getrennte
    Checkbox - ohne sie darf der Checkout ebenso wenig starten wie ohne die
    erste."""
    headers = register_user(client, "ohne-kenntnisnahme@example.com")

    resp = client.post(
        "/api/billing/checkout",
        json={"immediate_start": True, "withdrawal_ack": False},
        headers=headers,
    )
    assert resp.status_code == 422


def test_checkout_mit_erklaerung_haelt_die_einwilligung_fest(client):
    import stripe
    import pytest

    from app.models import CheckoutConsent

    headers = register_user(client, "mit-erklaerung@example.com")
    user_id = client.get("/api/profiles/me", headers=headers).json()["id"]

    # Kein echter Stripe-Key im Testbetrieb - der Aufruf scheitert bei Stripe,
    # aber erst NACH der CheckoutConsent-Anlage, das reicht fuer diesen Test.
    with pytest.raises(stripe._error.AuthenticationError):
        client.post(
            "/api/billing/checkout",
            json={"immediate_start": True, "withdrawal_ack": True},
            headers=headers,
        )

    db = TestingSessionLocal()
    try:
        checkout_consent = (
            db.query(CheckoutConsent).filter(CheckoutConsent.user_id == user_id).one()
        )
    finally:
        db.close()
    # Beide Erklaerungen getrennt mit eigener Fassung, noch ohne Abo-ID -
    # die kommt erst mit dem Webhook (siehe test_stripe_webhook_erg unten).
    # Kein zusaetzlicher, "widerrufbarer" Consent-Eintrag mehr: die
    # massgebliche Erklaerung liegt allein hier und wirkt fort, solange der
    # Vertrag laeuft (siehe consents.py/billing.py).
    assert checkout_consent.immediate_start_version
    assert checkout_consent.withdrawal_ack_version
    assert checkout_consent.stripe_subscription_id is None


def test_unbekannter_kunde_und_unbekanntes_ereignis_laufen_ins_leere(client):
    """Ein Webhook fuer einen fremden Kunden darf nichts anfassen und nicht
    abstuerzen - Stripe wiederholt sonst endlos."""
    user_id = _setup_subscriber(client)

    _mit_db(lambda db: handle_stripe_event(
        _event("customer.subscription.deleted",
               {"id": "sub_fremd", "customer": "cus_fremd"}),
        db,
    ))
    _mit_db(lambda db: handle_stripe_event(
        _event("customer.discount.created", {"customer": "cus_test123"}),
        db,
    ))

    assert _user_row(user_id).is_subscribed is True


def test_trial_erinnerung_wird_trotz_webhook_wiederholung_nur_einmal_gesendet(
    client, monkeypatch
):
    _setup_subscriber(client)
    sent = []
    monkeypatch.setattr(
        "app.routers.billing.mailer.send_trial_ending",
        lambda email, name, trial_end: sent.append((email, trial_end)) or True,
    )

    event = _event(
        "customer.subscription.trial_will_end",
        {
            "id": "sub_test123",
            "customer": "cus_test123",
            "trial_end": 1790000000,
        },
        event_id="evt_trial_end",
    )
    _mit_db(lambda db: handle_stripe_event(event, db))
    _mit_db(lambda db: handle_stripe_event(event, db))

    assert sent == [("abonnent@example.com", 1790000000)]


def test_abo_verlaengerung_zahlung_und_zahlungsfehler_senden_mails(
    client, monkeypatch
):
    _setup_subscriber(client)
    sent = []
    monkeypatch.setattr(
        "app.routers.billing.mailer.send_renewal_reminder",
        lambda *args: sent.append(("upcoming", args)) or True,
    )
    monkeypatch.setattr(
        "app.routers.billing.mailer.send_payment_succeeded",
        lambda *args: sent.append(("paid", args)) or True,
    )
    monkeypatch.setattr(
        "app.routers.billing.mailer.send_payment_failed",
        lambda *args: sent.append(("failed", args)) or True,
    )

    invoice = {
        "id": "in_123",
        "customer": "cus_test123",
        "subscription": "sub_test123",
        "billing_reason": "subscription_cycle",
        "amount_due": 500,
        "amount_paid": 500,
        "currency": "eur",
        "period_end": 1790000000,
        "next_payment_attempt": 1790003600,
        "hosted_invoice_url": "https://invoice.example.test/in_123",
    }
    _mit_db(lambda db: handle_stripe_event(_event("invoice.upcoming", invoice), db))
    _mit_db(lambda db: handle_stripe_event(_event("invoice.paid", invoice), db))
    _mit_db(lambda db: handle_stripe_event(_event("invoice.payment_failed", invoice), db))

    assert [kind for kind, _args in sent] == ["upcoming", "paid", "failed"]


def test_null_euro_trial_rechnung_sendet_keine_zahlungsbestaetigung(
    client, monkeypatch
):
    _setup_subscriber(client)
    sent = []
    monkeypatch.setattr(
        "app.routers.billing.mailer.send_payment_succeeded",
        lambda *args: sent.append(args) or True,
    )

    _mit_db(lambda db: handle_stripe_event(
        _event("invoice.paid", {
            "id": "in_zero",
            "customer": "cus_test123",
            "subscription": "sub_test123",
            "amount_paid": 0,
            "currency": "eur",
        }),
        db,
    ))

    assert sent == []


def test_vorgemerkte_kuendigung_und_aboende_werden_bestaetigt(client, monkeypatch):
    _setup_subscriber(client)
    sent = []
    monkeypatch.setattr(
        "app.routers.billing.mailer.send_cancellation_scheduled",
        lambda *args: sent.append(("scheduled", args)) or True,
    )
    monkeypatch.setattr(
        "app.routers.billing.mailer.send_subscription_ended",
        lambda *args: sent.append(("ended", args)) or True,
    )

    _mit_db(lambda db: handle_stripe_event(
        _event(
            "customer.subscription.updated",
            {
                "id": "sub_test123",
                "customer": "cus_test123",
                "status": "active",
                "cancel_at_period_end": True,
                "current_period_end": 1790000000,
            },
            previous={"cancel_at_period_end": False},
        ),
        db,
    ))
    _mit_db(lambda db: handle_stripe_event(
        _event("customer.subscription.deleted", {
            "id": "sub_test123",
            "customer": "cus_test123",
            "status": "canceled",
        }),
        db,
    ))

    assert [kind for kind, _args in sent] == ["scheduled", "ended"]
