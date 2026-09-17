"""Endpunkte fuer Kaeufe in den Apps.

Zwei Arten von Aufrufen, mit zwei ganz verschiedenen Vertrauensverhaeltnissen:

* **Von der App** (mit Anmeldung): "Hier ist mein Beleg, schreib ihn meinem
  Konto gut." Nur hier ist bekannt, um welches FLEXR-Konto es geht - Apple und
  Google kennen es nicht.
* **Vom Store** (ohne Anmeldung): Verlaengerung, Kuendigung, Rueckerstattung.
  Diese Aufrufe tragen keine Sitzung und duerfen sich auch nicht auf eine
  berufen; sie weisen sich anders aus - Apple durch die Signatur der
  Nachricht, Google durch ein Geheimnis im Pfad.

Die Pruefung selbst steht in ``app/store_billing.py``; hier steht nur, wer
was einreichen darf und was der Client als Antwort braucht.
"""

import base64
import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from .. import store_billing
from ..config import settings
from ..database import get_db
from ..models import User
from ..schemas import AppleTransactionRequest, GooglePurchaseRequest, StorePurchaseResult
from ..security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/billing", tags=["billing"])


def _ergebnis(user: User) -> StorePurchaseResult:
    return StorePurchaseResult(
        is_premium=user.is_premium,
        premium_until=user.store_premium_until,
    )


def _premium_muss_scharf_sein() -> None:
    """Kein Kauf, solange Premium serverseitig aus ist.

    Sonst nimmt der Server Geld fuer Vorteile entgegen, die es gerade gar
    nicht gibt (ohne Grenzen ist Premium wirkungslos) - und muesste sie
    erstatten.
    """
    if not settings.premium_enabled:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "FLEXR Premium ist derzeit nicht bestellbar.",
        )


@router.post("/apple/transaction", response_model=StorePurchaseResult)
def apple_transaction(
    payload: AppleTransactionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Signierte StoreKit-Transaktion einreichen.

    Die iOS-App ruft das nach jedem Kauf auf und ausserdem bei jedem Start fuer
    alle laufenden Berechtigungen (``Transaction.currentEntitlements``). Das
    zweite ist kein Beiwerk, sondern der Weg zurueck aus jeder Stoerung: Wer
    beim Kauf gerade keine Verbindung hatte, das Geraet gewechselt hat oder
    seine Kaeufe wiederherstellt, bekommt sein Premium dadurch von selbst
    wieder - ohne Knopf "Kauf wiederherstellen", den er suchen muesste.

    Mehrfaches Einreichen desselben Belegs ist deshalb ausdruecklich normal
    und schreibt nur dieselbe Zeile fort.
    """
    _premium_muss_scharf_sein()
    try:
        beleg = store_billing.apple_transaction_from_jws(payload.signed_transaction)
        store_billing.apply_subscription(db, current_user, beleg)
    except store_billing.StoreVerificationError as fehler:
        logger.warning("Apple-Beleg abgelehnt (user=%s): %s", current_user.id, fehler)
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(fehler))
    return _ergebnis(current_user)


@router.post("/google/purchase", response_model=StorePurchaseResult)
def google_purchase(
    payload: GooglePurchaseRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Play-Kauf einreichen. Der Token allein sagt nichts - gefragt wird Google."""
    _premium_muss_scharf_sein()
    try:
        beleg = store_billing.google_subscription_from_token(payload.purchase_token)
        store_billing.apply_subscription(db, current_user, beleg)
        # Erst jetzt bestaetigen: Google storniert einen unbestaetigten Kauf
        # nach drei Tagen von selbst, und bestaetigen sollte man nur, was auch
        # wirklich gutgeschrieben wurde.
        if not beleg["_acknowledged"] and beleg["expires_at"]:
            store_billing.google_acknowledge(beleg["product_id"], payload.purchase_token)
    except store_billing.StoreVerificationError as fehler:
        logger.warning("Play-Kauf abgelehnt (user=%s): %s", current_user.id, fehler)
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(fehler))
    return _ergebnis(current_user)


# ---------------------------------------------------------------------------
# Benachrichtigungen der Stores
# ---------------------------------------------------------------------------


@router.post("/apple/notifications")
async def apple_notifications(request: Request, db: Session = Depends(get_db)):
    """App Store Server Notifications V2.

    Die Nachricht ist selbst ein signiertes JWS und weist sich dadurch aus -
    eine Anmeldung gibt es hier nicht und darf es nicht geben. Innen liegt
    erneut ein JWS mit der eigentlichen Transaktion.

    Antwortet bewusst auch dann mit 200, wenn die Nachricht zu einem Kauf
    gehoert, den wir nicht kennen: Apple wiederholt sonst tagelang etwas, das
    sich durch Wiederholen nicht aendert. Was nicht stimmt, wird abgelehnt.
    """
    try:
        rumpf = await request.json()
        nachricht = store_billing.verify_apple_jws(rumpf["signedPayload"])
    except store_billing.StoreVerificationError as fehler:
        logger.warning("Apple-Benachrichtigung abgelehnt: %s", fehler)
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Ungueltige Signatur.")
    except Exception:  # noqa: BLE001
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unlesbare Benachrichtigung.")

    art = nachricht.get("notificationType")
    signierte_transaktion = (
        nachricht.get("data", {}).get("signedTransactionInfo")
    )
    if not signierte_transaktion:
        # CONSUMPTION_REQUEST und Testnachrichten tragen keine Transaktion.
        logger.info("Apple-Benachrichtigung ohne Transaktion: %s", art)
        return {"received": True}

    try:
        beleg = store_billing.apple_transaction_from_jws(signierte_transaktion)
    except store_billing.StoreVerificationError as fehler:
        logger.warning("Apple-Benachrichtigung (%s) abgelehnt: %s", art, fehler)
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Ungueltiger Beleg.")

    # REFUND und REVOKE heben den Kauf auf, ganz gleich, was das Ablaufdatum
    # sagt. Apple traegt dafuer zwar ein revocationDate ein, das
    # apple_transaction_from_jws() bereits auswertet - die Art der Nachricht
    # ist hier die zweite, unabhaengige Quelle derselben Aussage.
    if art in ("REFUND", "REVOKE"):
        beleg["expires_at"] = None
        beleg["status"] = "revoked"

    try:
        store_billing.apply_subscription(db, None, beleg)
    except store_billing.StoreVerificationError as fehler:
        logger.info("Apple-Benachrichtigung (%s) ohne Wirkung: %s", art, fehler)
    return {"received": True}


@router.post("/google/notifications/{token}")
async def google_notifications(
    token: str, request: Request, db: Session = Depends(get_db)
):
    """Real-time Developer Notifications von Google, ueber Pub/Sub zugestellt.

    Googles Zustellung traegt keine Signatur, die sich ohne weitere
    Abhaengigkeit pruefen liesse - stattdessen ein nicht zu erratendes
    Geheimnis im Pfad, das nur in der Pub/Sub-Konfiguration und in der ``.env``
    steht.

    Die Nachricht selbst enthaelt bewusst **keinen Zustand**, nur den Hinweis
    "an diesem Kauf hat sich etwas geaendert". Der aktuelle Stand wird
    anschliessend bei Google geholt - so, wie Google es auch vorsieht: Die
    Reihenfolge der Zustellung ist nicht garantiert, eine aeltere Nachricht
    duerfte sonst eine neuere ueberschreiben.
    """
    erwartet = settings.google_notifications_token
    if not erwartet or token != erwartet:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Nicht gefunden.")

    try:
        rumpf = await request.json()
        roh = base64.b64decode(rumpf["message"]["data"])
        nachricht = json.loads(roh)
    except Exception:  # noqa: BLE001
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unlesbare Benachrichtigung.")

    abo = nachricht.get("subscriptionNotification")
    if not abo or not abo.get("purchaseToken"):
        # Test- und Voucher-Nachrichten. Nichts zu tun, aber bestaetigen -
        # sonst stellt Pub/Sub sie endlos erneut zu.
        logger.info("Play-Benachrichtigung ohne Abo-Teil: %s", list(nachricht))
        return {"received": True}

    try:
        beleg = store_billing.google_subscription_from_token(abo["purchaseToken"])
        store_billing.apply_subscription(db, None, beleg)
    except store_billing.StoreVerificationError as fehler:
        logger.info("Play-Benachrichtigung ohne Wirkung: %s", fehler)
    return {"received": True}
