"""Abholfach für App-Benachrichtigungen und Anmeldung der Geräte.

**Zwei Wege, und der zweite ist seit 17.09.2026 der schnelle.**

Das Abholfach hier ist der ältere: Die Apps fragen es im Hintergrund ab
(WorkManager bzw. BGTaskScheduler) und zeigen das Ergebnis als lokale
Systembenachrichtigung an. Das reicht für alles, was ein paar Stunden Zeit hat,
und es reicht für eine Chatnachricht nicht - WorkManager lässt frühestens 15
Minuten zu, und Android schiebt den Lauf im Doze-Modus in die nächste
Wartungsphase. Gemeldet wurde genau das: Die Nachricht kam erst an, als die App
von Hand gestartet wurde.

Deshalb gibt es daneben jetzt echte Zustellung über FCM. Die Apps melden ihren
Gerätetoken über ``/token`` an, der Server schickt selbst, und das Gerät wacht
dafür auch aus dem Doze auf (siehe ``app/push.py``). Das Abholfach bleibt als
Fallback bestehen - ohne FCM-Zugangsdaten läuft alles unverändert weiter, nur
eben langsam.

Die Abfrage schickt X-Flexr-Background: 1 mit, damit sie nicht als
Vordergrund-Nutzung zählt (siehe security.get_current_user) - sonst würde
ausgerechnet der Abgleich, der die Inaktivitäts-Erinnerung ausliefern soll,
diese Erinnerung dauerhaft verhindern.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import notifications, push
from ..database import get_db
from ..models import User
from ..schemas import MarkDeliveredRequest, PushTokenRequest, PushNotificationOut
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


@router.post("/token")
def register_push_token(
    payload: PushTokenRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Gerätetoken für echte Push-Zustellung hinterlegen.

    Die Apps rufen das nach dem Anmelden auf und erneut, sooft Firebase den
    Token erneuert (das passiert von selbst, etwa nach einer Neuinstallation).
    Mehrfaches Anmelden desselben Tokens ist deshalb der Normalfall und
    schreibt nur dieselbe Zeile fort.
    """
    push.register(db, current_user, payload.platform, payload.token)
    return {"registered": True}


@router.delete("/token")
def unregister_push_token(
    payload: PushTokenRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Gerätetoken abmelden - beim Abmelden und beim Abschalten der
    Benachrichtigungen in der App.

    Der Token **ist** der Schalter: Ohne ihn hat der Server niemanden, dem er
    zustellen könnte. Bewusst kein zusätzliches Flag am Konto - zwei Quellen
    für dieselbe Frage laufen früher oder später auseinander.
    """
    push.unregister(db, payload.token)
    return {"registered": False}
