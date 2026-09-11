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

from .. import telegram
from ..database import get_db
from ..mailer import email_configured, send_notice_acknowledgement
from ..models import Notice, NoticeCategory
from ..rate_limit import limiter
from ..message_texts import normalise, t
from ..schemas import NoticeAck, NoticeRequest

logger = logging.getLogger("flexr.notices")

router = APIRouter(prefix="/api/notices", tags=["dsa"])

#: Anzeigenamen der Kategorien - erscheinen in der Empfangsbestätigung und in
#: der Entscheidung. Beide gehen an den Melder und folgen der Sprache, in der
#: er das Formular ausgefüllt hat (Notice.language); die Beschriftungen im
#: Formular selbst stehen in frontend/meldung.html und /en/meldung.html.
CATEGORY_LABELS = {
    NoticeCategory.csam: {
        "de": "Darstellung sexuellen Kindesmissbrauchs",
        "en": "Child sexual abuse material",
    },
    NoticeCategory.minor: {
        "de": "Mutmaßlich minderjährige Person",
        "en": "Person suspected of being a minor",
    },
    NoticeCategory.trafficking: {
        "de": "Menschenhandel oder sexuelle Ausbeutung",
        "en": "Human trafficking or sexual exploitation",
    },
    NoticeCategory.threat: {
        "de": "Drohung oder Gefahr für Leib und Leben",
        "en": "Threat or danger to life and limb",
    },
    NoticeCategory.sexual_content: {
        "de": "Nicht einvernehmliche intime Aufnahmen",
        "en": "Non-consensual intimate images",
    },
    NoticeCategory.impersonation: {
        "de": "Identitätsmissbrauch, fremde Fotos",
        "en": "Impersonation, someone else’s photos",
    },
    NoticeCategory.fraud: {
        "de": "Betrug, Erpressung, Scam",
        "en": "Fraud, extortion, scam",
    },
    NoticeCategory.hate: {
        "de": "Hass, Verhetzung, Diskriminierung",
        "en": "Hate, incitement, discrimination",
    },
    NoticeCategory.ip_infringement: {
        "de": "Urheber- oder Kennzeichenrecht",
        "en": "Copyright or trade mark infringement",
    },
    NoticeCategory.data_protection: {
        "de": "Verstoß gegen Datenschutzrecht",
        "en": "Breach of data protection law",
    },
    NoticeCategory.other_illegal: {
        "de": "Sonstiger mutmaßlich rechtswidriger Inhalt",
        "en": "Other allegedly illegal content",
    },
}

#: Kategorien, die vorrangig behandelt werden. Der Melder erfährt das sofort,
#: damit er weiß, dass er nicht auf 72 Stunden wartet.
URGENT_CATEGORIES = {
    NoticeCategory.csam,
    NoticeCategory.minor,
    NoticeCategory.trafficking,
    NoticeCategory.threat,
}


def category_label(value: str, lang: str = "de") -> str:
    try:
        return CATEGORY_LABELS[NoticeCategory(value)][normalise(lang)]
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
    # Die Sprache kommt von der Formularseite (/meldung.html oder
    # /en/meldung.html). Aeltere Clients schicken sie nicht - dann Deutsch.
    lang = normalise(payload.language)

    notice = Notice(
        category=payload.category,
        language=lang,
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

    telegram.notify_admin_task(
        f"🆕 Neue DSA-Meldung ({notice.reference}) im FLEXR-Admin-Dashboard: "
        f"{category_label(payload.category)}"  # Admin-Hinweis bleibt deutsch
    )

    # Ohne konfiguriertes SMTP kann keine Empfangsbestätigung rausgehen. Das
    # dem Melder zu verschweigen wäre der schlimmere Fehler: Er soll sich das
    # Aktenzeichen notieren, statt auf eine Mail zu warten, die nie kommt.
    ack_sent = bool(payload.reporter_email) and email_configured()
    if ack_sent:
        background_tasks.add_task(
            send_notice_acknowledgement,
            payload.reporter_email,
            notice.reference,
            now.strftime("%d.%m.%Y %H:%M:%S UTC"),
            category_label(payload.category, lang),
            lang,
        )
    elif payload.reporter_email:
        logger.error(
            "Meldung %s ohne Empfangsbestaetigung: SMTP ist nicht konfiguriert "
            "(siehe LEGAL_REVIEW.md, T-06)",
            notice.reference,
        )

    logger.info(
        "DSA-Meldung %s eingegangen (Kategorie %s, dringend: %s)",
        notice.reference,
        payload.category,
        category in URGENT_CATEGORIES,
    )

    frist = t(
        "api.notice.urgent" if category in URGENT_CATEGORIES else "api.notice.normal",
        lang,
    )

    if payload.reporter_email and ack_sent:
        zustellung = t("api.notice.delivery", lang, email=payload.reporter_email)
    elif payload.reporter_email:
        zustellung = t(
            "api.notice.noMail", lang,
            reference=notice.reference, email=payload.reporter_email,
        )
    else:
        zustellung = t("api.notice.anonymous", lang)

    return NoticeAck(
        reference=notice.reference,
        created_at=now,
        acknowledgement_sent=ack_sent,
        message=t(
            "api.notice.received", lang,
            reference=notice.reference, deadline=frist, delivery=zustellung,
        ),
    )
