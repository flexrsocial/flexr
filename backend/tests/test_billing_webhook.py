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


def _event(event_type, obj):
    return {"type": event_type, "data": {"object": obj}}


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
