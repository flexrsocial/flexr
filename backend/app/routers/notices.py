"""Melde- und Abhilfeverfahren nach Art. 16 DSA.

Bisher gab es nur POST /api/reports: eine Ein-Klick-Meldung aus der App
heraus, die eine Anmeldung voraussetzt und ein Nutzerkonto als Ziel braucht.
Art. 16 DSA verlangt darüber hinaus ein Verfahren, das

  * jeder Person und Einrichtung offensteht - auch ohne Konto,
  * eine hinreichend präzise und begründete Meldung ermöglicht,
  * die genaue elektronische Fundstelle aufnimmt,
  * die Kontaktangaben des Melders erfasst (mit der Ausnahme des Abs. 3),
  * eine Erklärung in gutem Glauben verlangt,
  * den Eingang unverzüglich bestätigt und
  * die Entscheidung samt Begründung und Rechtsbehelf mitteilt.

Die App-Meldung bleibt daneben bestehen - sie ist der schnelle Weg für
angemeldete Nutzer, dieses Formular der förmliche.
"""

import logging
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, Request
from sqlalchemy.orm import Session

from ..database import get_db
from ..mailer import send_notice_acknowledgement
from ..models import Notice, NoticeCategory
from ..rate_limit import limiter
from ..schemas import NoticeAck, NoticeRequest

logger = logging.getLogger("flexr.notices")

router = APIRouter(prefix="/api/notices", tags=["dsa"])

#: Anzeigenamen der Kategorien - erscheinen in der Empfangsbestätigung.
CATEGORY_LABELS = {
    NoticeCategory.csam: "Darstellung sexuellen Kindesmissbrauchs",
    NoticeCategory.minor: "Mutmaßlich minderjährige Person",
    NoticeCategory.trafficking: "Menschenhandel oder sexuelle Ausbeutung",
    NoticeCategory.threat: "Drohung oder Gefahr für Leib und Leben",
    NoticeCategory.sexual_content: "Nicht einvernehmliche intime Aufnahmen",
    NoticeCategory.impersonation: "Identitätsmissbrauch, fremde Fotos",
    NoticeCategory.fraud: "Betrug, Erpressung, Scam",
    NoticeCategory.hate: "Hass, Verhetzung, Diskriminierung",
    NoticeCategory.ip_infringement: "Urheber- oder Kennzeichenrecht",
    NoticeCategory.data_protection: "Verstoß gegen Datenschutzrecht",
    NoticeCategory.other_illegal: "Sonstiger mutmaßlich rechtswidriger Inhalt",
}

#: Kategorien, die vorrangig behandelt werden. Der Melder erfährt das sofort,
#: damit er weiß, dass er nicht auf 72 Stunden wartet.
URGENT_CATEGORIES = {
    NoticeCategory.csam,
    NoticeCategory.minor,
    NoticeCategory.trafficking,
    NoticeCategory.threat,
}


def category_label(value: str) -> str:
    try:
        return CATEGORY_LABELS[NoticeCategory(value)]
    except ValueError:
        return value


@router.post("", response_model=NoticeAck, status_code=201)
@router.post("/", response_model=NoticeAck, status_code=201, include_in_schema=False)
@limiter.limit("10/hour")
def submit_notice(
    request: Request,
    payload: NoticeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Nimmt eine Meldung entgegen und bestätigt den Eingang.

    Kein Login: Art. 16 Abs. 1 DSA spricht von "Personen oder Einrichtungen" -
    ein Konto zu verlangen wäre eine Hürde, die die Vorschrift nicht kennt.
    Missbrauch wird über das Rate Limit begrenzt, nicht über eine Anmeldung.
    """
    now = datetime.utcnow()
    category = NoticeCategory(payload.category)

    notice = Notice(
        category=payload.category,
        explanation=payload.explanation,
        content_reference=payload.content_reference,
        reporter_name=payload.reporter_name,
        reporter_email=payload.reporter_email,
        good_faith=payload.good_faith,
        created_at=now,
        # Die Bestätigung geht mit dieser Antwort raus - der Zeitstempel gehört
        # deshalb hierher und nicht hinter den Mailversand.
        acknowledged_at=now,
    )
    db.add(notice)
    db.commit()
    db.refresh(notice)

    ack_sent = False
    if payload.reporter_email:
        background_tasks.add_task(
            send_notice_acknowledgement,
            payload.reporter_email,
            notice.reference,
            now.strftime("%d.%m.%Y %H:%M:%S UTC"),
            category_label(payload.category),
        )
        ack_sent = True

    logger.info(
        "DSA-Meldung %s eingegangen (Kategorie %s, dringend: %s)",
        notice.reference,
        payload.category,
        category in URGENT_CATEGORIES,
    )

    if category in URGENT_CATEGORIES:
        frist = (
            "Meldungen dieser Kategorie behandeln wir vorrangig — spätestens "
            "binnen 24 Stunden."
        )
    else:
        frist = "Ein Mensch prüft die Meldung, in der Regel binnen 72 Stunden."

    if payload.reporter_email:
        zustellung = (
            f"Die Empfangsbestätigung und später die begründete Entscheidung "
            f"gehen an {payload.reporter_email}."
        )
    else:
        zustellung = (
            "Du hast keine Kontaktadresse angegeben — das ist bei dieser "
            "Kategorie zulässig (Art. 16 Abs. 3 DSA). Wir können dir dann aber "
            "keine Entscheidung zusenden. Notiere dir das Aktenzeichen."
        )

    return NoticeAck(
        reference=notice.reference,
        created_at=now,
        acknowledgement_sent=ack_sent,
        message=(
            f"Deine Meldung ist eingegangen (Aktenzeichen {notice.reference}). "
            f"{frist} {zustellung}"
        ),
    )
