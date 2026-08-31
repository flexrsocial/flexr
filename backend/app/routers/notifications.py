"""Abholfach für App-Benachrichtigungen.

FLEXR verschickt keine echten Push-Nachrichten über FCM/APNs. Die nativen Apps
fragen dieses Fach im Hintergrund ab (WorkManager bzw. BGTaskScheduler) und
zeigen das Ergebnis als lokale Systembenachrichtigung an - dasselbe Muster, mit
dem NewMessageWorker schon neue Chatnachrichten meldet.

Die Abfrage schickt X-Flexr-Background: 1 mit, damit sie nicht als
Vordergrund-Nutzung zählt (siehe security.get_current_user) - sonst würde
ausgerechnet der Abgleich, der die Inaktivitäts-Erinnerung ausliefern soll,
diese Erinnerung dauerhaft verhindern.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import notifications
from ..database import get_db
from ..models import User
from ..schemas import MarkDeliveredRequest, PushNotificationOut
from ..security import get_current_user

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("/pending", response_model=list[PushNotificationOut])
def pending_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Noch nicht angezeigte Benachrichtigungen dieses Nutzers."""
    return notifications.pending_for(db, current_user.id)


@router.post("/delivered")
def mark_delivered(
    payload: MarkDeliveredRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Bestätigt, dass die App die Benachrichtigungen angezeigt hat.

    Quittiert wird erst nach dem Anzeigen, nicht beim Abholen: bricht der
    Hintergrundlauf dazwischen ab, kommt die Nachricht beim nächsten Durchgang
    erneut - besser doppelt als verschluckt.
    """
    changed = notifications.mark_delivered(db, current_user.id, payload.ids)
    return {"delivered": changed}
