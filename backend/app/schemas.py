from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from .age import is_plausible_birthdate


def _strip(v):
    """Umgebende Leerzeichen entfernen, bevor die Längengrenzen greifen.

    Sonst kommt " " an min_length=1 vorbei: Der Name landet leer im Profil und
    eine Chatnachricht als leere Blase im Verlauf, die auch noch als ungelesen
    zählt. Beide Clients schneiden zwar selbst zu, aber die Grenze gehört an
    den Server - er ist die einzige Stelle, die jeder Client passieren muss.
    """
    return v.strip() if isinstance(v, str) else v


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str = Field(min_length=1, max_length=100)
    # Geburtsdatum statt Alter - das Alter wird serverseitig laufend berechnet.
    birthdate: date
    # Adresse: city ist der amtliche Ortsname zur PLZ. Der Client holt ihn über
    # GET /api/geo/plz/{plz}; maßgeblich ist ohnehin, was der Server daraus
    # macht (siehe routers/auth.py) - keine feste Städteliste, ganz Österreich.
    plz: str = Field(pattern=r"^\d{4}$", description="4-stellige österreichische Postleitzahl")
    city: str = Field(min_length=1)
    gender: Literal["mann", "frau"]
    gym: str
    bio: Optional[str] = Field(default=None, max_length=280)

    # Ausdrückliche Einwilligung nach Art. 9 Abs. 2 lit. a DSGVO - muss aktiv
    # angehakt werden, ein Default von True wäre unwirksam.
    consent_sensitive_data: bool = Field(
        description="Einwilligung zur Verarbeitung der sexuellen Orientierung (Art. 9 Abs. 2 lit. a DSGVO)"
    )
    # Früher Pflichtfeld ("ich verliere mein Rücktrittsrecht"), seit 15.08.2026
    # gegenstandslos: Die Registrierung begründet keinen entgeltlichen Vertrag,
    # es gibt also kein Rücktrittsrecht, auf das verzichtet werden könnte.
    #
    # Das Feld bleibt entgegennahmefähig, damit die ausgelieferten Android- und
    # iOS-Fassungen weiter registrieren können - sie schicken es noch mit. Der
    # Wert wird ignoriert und nirgends gespeichert.
    consent_withdrawal_waiver: Optional[bool] = Field(
        default=None,
        deprecated=True,
        description=(
            "Wird nicht mehr ausgewertet. Bleibt nur, damit ältere App-Fassungen "
            "weiter registrieren können."
        ),
    )

    _trim = field_validator("name", "bio", mode="before")(_strip)

    @field_validator("birthdate")
    @classmethod
    def _plausible_birthdate(cls, v: date) -> date:
        """Nur die formale Plausibilität (kein Datum in der Zukunft, kein
        unrealistisches Alter). Die 18-Jahres-Grenze prüft der Router - sie
        muss den Versuch protokollieren und mit einer eigenen Antwort
        beantworten können (siehe routers/auth.py)."""
        if not is_plausible_birthdate(v):
            raise ValueError("Bitte ein gültiges Geburtsdatum angeben.")
        return v

    @field_validator("consent_sensitive_data")
    @classmethod
    def _require_sensitive_data_consent(cls, v: bool) -> bool:
        if not v:
            raise ValueError("Einwilligung zur Verarbeitung sensibler Daten ist erforderlich.")
        return v



class AgeCheckRequest(BaseModel):
    """Vorabprüfung des Geburtsdatums im Registrierungsformular. Verbindlich
    ist trotzdem die Prüfung in POST /api/auth/register - dieser Endpunkt
    verbessert nur die Führung durch das Formular."""

    birthdate: date


class AgeCheckResponse(BaseModel):
    eligible: bool
    age: Optional[int] = None
    message: Optional[str] = None
    # Was danach ansteht - der Client zeigt daraufhin den Hinweis auf die
    # Alters-/Identitätsprüfung an, bevor irgendein Bild aufgenommen wird.
    verification_required: bool = True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PhotoOut(BaseModel):
    id: str
    url: str
    thumb_url: Optional[str] = None
    position: int
    status: str

    class Config:
        from_attributes = True


class PresignPhotoRequest(BaseModel):
    content_type: Literal["image/jpeg", "image/png", "image/webp"]


class PresignPhotoResponse(BaseModel):
    upload_url: str
    object_key: str


class AddPhotoRequest(BaseModel):
    object_key: str
    thumb_object_key: Optional[str] = None


class ProfileOut(BaseModel):
    id: str
    name: str
    age: int
    city: str
    gender: str
    gym: str
    bio: Optional[str]
    is_online: bool = False
    is_verified: bool = False
    # Entfernung zum anfragenden Nutzer in km (nur im Swipe-Deck gesetzt)
    distance_km: Optional[int] = None
    photos: list[PhotoOut] = []

    class Config:
        from_attributes = True


class MyProfileOut(ProfileOut):
    """Eigene Profilansicht (/me) - enthält zusätzlich die PLZ, die anderen
    Nutzern nicht angezeigt wird (dort nur der Ort)."""

    plz: str
    birthdate: date
    # Nur in der eigenen Ansicht: Der Nutzer muss sehen, an welche Adresse die
    # Bestätigungsmail ging - sonst bemerkt er einen Tippfehler nie. In
    # ProfileOut (Fremdansicht) hat sie nichts verloren.
    email: EmailStr
    search_radius_km: int = 20
    # Alters-/Identitätsprüfung: Muss dieses Konto sie durchlaufen, und ist es
    # bereits freigeschaltet? Nur lesbar - gesetzt wird ausschließlich
    # serverseitig nach der Admin-Entscheidung.
    verification_required: bool = False
    is_account_activated: bool = True
    age_verified: bool = False
    # E-Mail-Bestätigung. Steht vor der Alters- und Identitätsprüfung, siehe
    # app/email_verification.py.
    email_verified: bool = False
    phone: Optional[str] = None
    phone_verified: bool = False
    # Befristete Chat-Sperre: bis wann darf der Nutzer keine Nachrichten senden
    # (None oder Vergangenheit = keine aktive Sperre)
    messaging_muted_until: Optional[datetime] = None


class UpdateProfileRequest(BaseModel):
    """Editierbare Profilfelder. PLZ und Ort müssen gemeinsam kommen; welcher
    Ort gespeichert wird, entscheidet aber die PLZ (siehe routers/profiles.py).
    Das Geburtsdatum ist bewusst nicht änderbar."""

    plz: Optional[str] = Field(default=None, pattern=r"^\d{4}$")
    city: Optional[str] = Field(default=None, min_length=1)
    gym: Optional[str] = None
    bio: Optional[str] = Field(default=None, max_length=280)
    search_radius_km: Optional[int] = Field(default=None, ge=2, le=250)

    # Eine Bio aus lauter Leerzeichen ist eine leere Bio - und die bedeutet
    # serverseitig "Bio entfernen" (siehe routers/profiles.py).
    _trim = field_validator("bio", mode="before")(_strip)


class DeleteAccountRequest(BaseModel):
    """Selbstlöschung: erneute Passworteingabe als Bestätigung."""

    password: str


class MembershipStatus(BaseModel):
    is_subscribed: bool
    trial_ends_at: datetime
    is_active: bool


class SwipeRequest(BaseModel):
    to_user_id: str
    action: Literal["like", "pass"]


class SwipeResult(BaseModel):
    matched: bool


class MessageOut(BaseModel):
    id: str
    match_id: str
    sender_id: str
    content: str
    created_at: datetime
    read_at: Optional[datetime]
    # True wenn in dieser Nachricht Links/Kontaktdaten zensiert wurden. Für den
    # Empfänger ist content bereits die zensierte Fassung; der Absender sieht sein
    # Original und dazu diesen Hinweis.
    was_censored: bool = False

    class Config:
        from_attributes = True


class SendMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=2000)

    _trim = field_validator("content", mode="before")(_strip)


class MatchOut(BaseModel):
    match_id: str
    profile: ProfileOut
    last_message: Optional[MessageOut] = None
    unread_count: int = 0
    is_online: bool = False


# ---------- Gyms ----------

class GymOut(BaseModel):
    id: str
    name: str
    street: str
    house_number: str
    plz: str
    city: str
    label: str


class GymSuggestRequest(BaseModel):
    """Nutzer-Vorschlag für ein fehlendes Gym."""

    name: str = Field(min_length=2, max_length=120)
    street: str = Field(min_length=2, max_length=120)
    house_number: str = Field(min_length=1, max_length=20)
    plz: str = Field(pattern=r"^\d{4}$")
    city: Optional[str] = Field(default=None, max_length=100)


# ---------- Geo ----------

class PlzLookupOut(BaseModel):
    plz: str
    city: str


# ---------- Telefonprüfung ----------

class PhoneRequestRequest(BaseModel):
    # E.164-Format, z. B. +436761234567
    phone: str = Field(pattern=r"^\+[1-9]\d{6,14}$")


class PhoneConfirmRequest(BaseModel):
    code: str = Field(pattern=r"^\d{6}$")


# ---------- E-Mail-Bestätigung ----------

class EmailConfirmRequest(BaseModel):
    token: str = Field(min_length=16, max_length=200)

    _trim = field_validator("token", mode="before")(_strip)


class EmailConfirmResponse(BaseModel):
    """Bestätigte Adresse und Name - die Seite begrüßt den Nutzer damit."""

    email: EmailStr
    name: str
    confirmed: bool = True


class EmailResendResponse(BaseModel):
    email: EmailStr
    valid_hours: int


# ---------- Alters- und Identitätsprüfung ----------

class VerificationSelfieIn(BaseModel):
    prompt: str
    object_key: str


class VerificationSubmitRequest(BaseModel):
    # Der Server verlangt genau ein Selfie (siehe routers/verification.py). Die
    # Obergrenze bleibt bei 3, damit eine ältere App-Version die verständliche
    # Fehlermeldung aus dem Router bekommt statt eines nackten 422.
    selfies: list[VerificationSelfieIn] = Field(min_length=1, max_length=3)


class VerificationStatusOut(BaseModel):
    """Statusantwort für den Nutzer.

    ``status`` behält die bisherigen Werte bei (ältere App-Versionen kennen sie
    bereits); ``id_required`` und ``reupload_required`` sind neu. ``next_step``
    sagt dem Client, was als Nächstes zu tun ist, ohne dass er die Statuswerte
    interpretieren muss.
    """

    status: Literal[
        "none", "in_progress", "id_required", "reupload_required",
        "submitted", "approved", "rejected",
    ]
    prompts: Optional[list[str]] = None
    next_step: Optional[Literal["selfie", "document", "wait", "none"]] = None
    # Sachlicher Grund, wenn eine neue Aufnahme nötig ist oder abgelehnt wurde.
    # Fester Katalogtext, kein Freitext des Prüfers.
    reason: Optional[str] = None
    # Muss dieses Konto die Prüfung bestehen, bevor es nutzbar wird?
    verification_required: bool = False
    account_activated: bool = True
    # Steht vor allem anderen: Ohne bestätigte Adresse lehnt /start ab. Bewusst
    # ein eigenes Feld statt eines neuen next_step-Wertes - ausgelieferte
    # App-Versionen kennen den Wert nicht und würden ihn als "none" lesen.
    email_verified: bool = True
    # Zugelassene Dokumenttypen und ob eine Rückseite gebraucht wird -
    # damit der Client keine eigene Liste pflegen muss.
    document_types: Optional[list[dict]] = None


class VerificationDocumentPresignRequest(BaseModel):
    content_type: Literal["image/jpeg", "image/png", "image/webp"]
    # Vom Client gemeldete Dateigröße. Die verbindliche Prüfung passiert nach
    # dem Upload gegen das tatsächliche Objekt (storage.inspect_uploaded_image).
    byte_size: int = Field(gt=0)


class VerificationDocumentSubmitRequest(BaseModel):
    document_type: Literal["id_card", "passport", "drivers_license"]
    front_object_key: str
    back_object_key: Optional[str] = None


class AdminVerificationOut(BaseModel):
    id: str
    user_id: str
    user_name: str
    user_email: str
    # Für den Abgleich mit dem Ausweis: angegebenes Geburtsdatum und das daraus
    # errechnete Alter.
    user_birthdate: date
    user_age: int
    user_registered_at: datetime
    prompts: list[str]
    selfie_urls: list[dict]  # [{"prompt": ..., "url": ...}] - kurzlebige Signed URLs
    profile_photo_urls: list[str]
    document_type: Optional[str] = None
    # [{"side": "front"|"back", "url": ...}] - kurzlebige Signed URLs, nie öffentlich
    document_urls: list[dict] = []
    created_at: datetime
    submitted_at: Optional[datetime] = None


class AdminVerificationApproveRequest(BaseModel):
    """Prüfcheckliste. Freigabe ist erst möglich, wenn der Prüfer jeden Punkt
    ausdrücklich bestätigt hat - der Server verlässt sich dabei nicht auf die
    Oberfläche, sondern lehnt unvollständige Bestätigungen ab."""

    selfie_matches_profile_photos: bool
    selfie_matches_document: bool
    document_shows_min_age: bool
    document_dob_matches_registration: bool
    document_legible: bool
    document_plausible: bool

    @model_validator(mode="after")
    def _all_confirmed(self):
        missing = [name for name, value in self.model_dump().items() if not value]
        if missing:
            raise ValueError(
                "Alle Punkte der Prüfcheckliste müssen bestätigt sein: "
                + ", ".join(missing)
            )
        return self


REVIEW_REASONS = Literal[
    "document_unreadable",
    "details_not_visible",
    "person_mismatch",
    "dob_mismatch",
    "underage",
    "document_unsuitable",
    "selfie_unusable",
    "other",
]


class AdminVerificationRejectRequest(BaseModel):
    reason_code: REVIEW_REASONS


class AdminVerificationReuploadRequest(BaseModel):
    reason_code: REVIEW_REASONS
    # True, wenn auch die Selfies neu aufgenommen werden müssen. Die alten
    # Aufnahmen werden dann gelöscht und der Selfie-Schritt beginnt von vorn.
    redo_selfie: bool = False


class AdminVerificationDecisionOut(BaseModel):
    status: str
    # False, wenn nach der Entscheidung noch Aufnahmen im Storage liegen. Der
    # Vorgang gilt dann als nicht abgeschlossen und wird erneut aufgeräumt.
    documents_deleted: bool = True
    cleanup_pending: bool = False


class ReportRequest(BaseModel):
    reported_user_id: str
    reason: str = Field(min_length=3, max_length=500)


class ReportAck(BaseModel):
    """Empfangsbestätigung nach Art. 16 Abs. 4 DSA: Der Melder bekommt ein
    Aktenzeichen und weiß, wann und wie er von der Entscheidung erfährt."""

    reported: bool = True
    reference: str
    created_at: datetime
    message: str


class ModerationNotice(BaseModel):
    """Begründete Mitteilung zu einer Maßnahme gegen das eigene Konto
    (Art. 17 DSA) - inklusive Hinweis auf den Rechtsbehelf."""

    action: str                     # ModerationAction
    reason: str
    action_at: datetime
    muted_until: Optional[datetime] = None
    appeal_hint: str


class BlockRequest(BaseModel):
    user_id: str


# ---------- Admin ----------

class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str


class AdminTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AdminUserListItem(BaseModel):
    id: str
    email: str
    name: str
    age: int
    city: str
    is_subscribed: bool
    is_banned: bool
    is_verified: bool = False
    is_active: bool
    # Alters-/Identitätsprüfung
    verification_required: bool = False
    is_account_activated: bool = True
    age_verified: bool = False
    created_at: datetime
    photo_count: int


class AdminUserDetailOut(BaseModel):
    id: str
    email: str
    name: str
    age: int
    plz: str
    city: str
    gender: str
    interest: str
    gym: str
    bio: Optional[str]
    is_subscribed: bool
    is_banned: bool
    is_verified: bool = False
    is_active: bool
    # Alters-/Identitätsprüfung
    verification_required: bool = False
    is_account_activated: bool = True
    age_verified: bool = False
    age_verified_at: Optional[datetime] = None
    verification_method: Optional[str] = None
    activated_at: Optional[datetime] = None
    messaging_muted_until: Optional[datetime] = None
    # Begründung der laufenden Maßnahme (Art. 17 DSA)
    moderation_action: Optional[str] = None
    moderation_reason: Optional[str] = None
    moderation_action_at: Optional[datetime] = None
    created_at: datetime
    trial_ends_at: datetime
    stripe_customer_id: Optional[str]
    phone: Optional[str] = None
    phone_verified: bool = False
    photos: list[PhotoOut] = []
    # Geräteprüfung: [{device_id, user_agent, last_seen, shared_with: [Namen]}]
    devices: list[dict] = []

    class Config:
        from_attributes = True


class AdminMuteRequest(BaseModel):
    """Befristete Chat-Sperre setzen: Dauer in Tagen und/oder Stunden.
    Die Begründung sieht der Betroffene im Chat (Art. 17 DSA)."""

    days: int = Field(default=0, ge=0, le=365)
    hours: int = Field(default=0, ge=0, le=8760)
    reason: str = Field(min_length=3, max_length=500)

    @model_validator(mode="after")
    def _at_least_one(self):
        if self.days == 0 and self.hours == 0:
            raise ValueError("Sperrdauer muss größer als 0 sein.")
        return self


class AdminGymOut(BaseModel):
    id: str
    name: str
    street: str
    house_number: str
    plz: str
    city: str
    status: str
    created_at: Optional[datetime] = None


class AdminGymUpdate(BaseModel):
    """Korrektur eines Gym-Eintrags durch den Admin (z. B. Rechtschreibung),
    bevor er freigegeben wird. Alle Felder optional - nur Angegebenes wird
    geändert."""

    name: Optional[str] = Field(default=None, min_length=2, max_length=120)
    street: Optional[str] = Field(default=None, max_length=120)
    house_number: Optional[str] = Field(default=None, max_length=20)
    plz: Optional[str] = Field(default=None, pattern=r"^\d{4}$")
    city: Optional[str] = Field(default=None, max_length=100)


class AdminFlaggedMessageOut(BaseModel):
    id: str
    sender_id: str
    sender_name: str
    content: str               # Original des Absenders
    display_content: str       # das, was der Empfänger tatsächlich gesehen hat
    was_censored: bool         # wurde ein Link/Kontakt für den Empfänger entfernt?
    delivered: bool = True     # Nachrichten werden zugestellt (kein Auto-Block)
    read_at: Optional[datetime] = None  # vom Empfänger gelesen (None = ungelesen)
    flag_reason: Optional[str]
    created_at: datetime


class AdminStats(BaseModel):
    total_users: int
    active_subscriptions: int
    trial_users: int
    banned_users: int
    # Offene Aufgaben (Aufgaben-Panel im Dashboard)
    pending_photos: int
    open_reports: int
    pending_verifications: int = 0
    # Entschiedene Prüfungen, bei denen das Löschen der Aufnahmen noch aussteht
    pending_verification_cleanups: int = 0
    flagged_messages: int = 0
    pending_gyms: int = 0
    # Zugriffe
    active_today: int = 0
    new_today: int = 0


class AdminAccessPoint(BaseModel):
    day: str
    count: int


class AdminCountryStat(BaseModel):
    country: str
    count: int


class AdminAccessStats(BaseModel):
    daily: list[AdminAccessPoint]        # tagesaktive Nutzer je Tag (letzte N Tage)
    countries: list[AdminCountryStat]    # Länderverteilung (heute aktive Nutzer)


class AdminReportOut(BaseModel):
    id: str
    reference: str
    reporter_id: str
    reporter_name: str
    reported_id: str
    reported_name: str
    reason: str
    created_at: datetime


class AdminReportDecisionRequest(BaseModel):
    """Entscheidung über eine Meldung. Der Text geht wörtlich an den Melder,
    deshalb ist er Pflicht (Art. 16 Abs. 5 DSA)."""

    outcome: Literal["no_action", "action_taken"]
    decision_note: str = Field(min_length=3, max_length=500)


class AdminModerationRequest(BaseModel):
    """Begründung einer Maßnahme (Art. 17 DSA). Ohne Begründung keine Sperre."""

    reason: str = Field(min_length=3, max_length=500)


class PhotoModerationOut(BaseModel):
    id: str
    url: str
    status: str
    position: int
    user_id: str
    user_name: str
    user_email: str


# ---------------------------------------------------------------------------
# Online-Rücktrittsfunktion (§ 13a FAGG)
# ---------------------------------------------------------------------------


class WithdrawalRequest(BaseModel):
    """Rücktrittserklärung über die öffentliche Funktion.

    Bewusst niedrigschwellig: § 13a FAGG verlangt, dass der Rücktritt ohne
    unnötige Hürden erklärt werden kann. Pflicht sind deshalb nur Name und eine
    elektronische Adresse für die Bestätigung - die Bezeichnung des Vertrags
    darf auch ungenau sein, solange sich der Vorgang zuordnen lässt.
    """

    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    contract_reference: Optional[str] = Field(default=None, max_length=200)
    message: Optional[str] = Field(default=None, max_length=1000)
    # Der zweite, getrennte Schritt: erst nach dem Bestätigungsknopf wird
    # erklärt. Ein Formular allein ist noch keine Erklärung.
    confirmed: bool

    _trim = field_validator("name", "contract_reference", "message", mode="before")(_strip)

    @field_validator("confirmed")
    @classmethod
    def _require_confirmation(cls, v: bool) -> bool:
        if not v:
            raise ValueError("Bitte den Rücktritt im zweiten Schritt bestätigen.")
        return v


class WithdrawalAck(BaseModel):
    reference: str
    received_at: datetime
    declaration_text: str
    confirmation_sent: bool
    message: str


# ---------------------------------------------------------------------------
# Meldeverfahren nach Art. 16 DSA
# ---------------------------------------------------------------------------

#: Kategorien, bei denen Art. 16 Abs. 3 DSA die Angabe von Name und E-Mail
#: nicht verlangt (Straftaten nach Art. 3-7 der Richtlinie 2011/93/EU).
ANONYMOUS_NOTICE_CATEGORIES = {"csam"}


class NoticeRequest(BaseModel):
    """Meldung über das öffentliche Formular - auch ohne Konto möglich."""

    category: Literal[
        "csam", "minor", "trafficking", "threat", "sexual_content",
        "impersonation", "fraud", "hate", "ip_infringement",
        "data_protection", "other_illegal",
    ]
    # Art. 16 Abs. 2 lit. a - eine Begründung, die eine Prüfung erlaubt.
    # 30 Zeichen Untergrenze: "ist illegal" ist keine hinreichend präzise
    # Meldung und würde die Prüfung nur blockieren.
    explanation: str = Field(min_length=30, max_length=5000)
    # Art. 16 Abs. 2 lit. b - genaue Fundstelle.
    content_reference: str = Field(min_length=3, max_length=500)
    reporter_name: Optional[str] = Field(default=None, max_length=120)
    reporter_email: Optional[EmailStr] = None
    # Art. 16 Abs. 2 lit. d - Erklärung in gutem Glauben.
    good_faith: bool

    _trim = field_validator(
        "explanation", "content_reference", "reporter_name", mode="before"
    )(_strip)

    @field_validator("good_faith")
    @classmethod
    def _require_good_faith(cls, v: bool) -> bool:
        if not v:
            raise ValueError(
                "Ohne die Erklärung, dass die Angaben nach bestem Wissen richtig "
                "und vollständig sind, können wir die Meldung nicht bearbeiten."
            )
        return v

    @model_validator(mode="after")
    def _require_contact_unless_exempt(self):
        """Kontaktangaben sind Pflicht - außer in den Fällen des Art. 16 Abs. 3.

        Ohne Adresse gibt es weder Empfangsbestätigung noch Entscheidung; der
        Melder soll das nicht versehentlich wählen. Bei Darstellungen sexuellen
        Kindesmissbrauchs verlangt der DSA die Identifizierung ausdrücklich
        nicht, dort bleibt das Feld frei.
        """
        if self.category in ANONYMOUS_NOTICE_CATEGORIES:
            return self
        if not self.reporter_name or not self.reporter_email:
            raise ValueError(
                "Für diese Kategorie brauchen wir Name und E-Mail-Adresse, damit "
                "wir dir den Eingang und die Entscheidung mitteilen können."
            )
        return self


class NoticeAck(BaseModel):
    reference: str
    created_at: datetime
    acknowledgement_sent: bool
    message: str


class AdminNoticeOut(BaseModel):
    id: str
    reference: str
    category: str
    explanation: str
    content_reference: str
    reporter_name: Optional[str] = None
    reporter_email: Optional[str] = None
    created_at: datetime
    decided_at: Optional[datetime] = None
    outcome: Optional[str] = None


class AdminNoticeDecisionRequest(BaseModel):
    """Entscheidung über eine Meldung samt Begründung (Art. 16 Abs. 5 DSA)."""

    outcome: Literal["action_taken", "no_action", "forwarded", "insufficient"]
    decision_reason: str = Field(min_length=10, max_length=5000)
    decision_automated: bool = False


# ---------------------------------------------------------------------------
# Meldungen aus Nutzersicht (Art. 16 Abs. 5 DSA)
# ---------------------------------------------------------------------------


class MyReportOut(BaseModel):
    """Eine eigene Meldung mit ihrem Stand.

    Bis 15.08.2026 versprach frontend/sicherheit.html eine Ansicht "Meine
    Meldungen" im Konto-Bereich, die es nicht gab: Der Melder erfuhr das
    Ergebnis nirgends. Dieses Schema ist die Grundlage dafür.
    """

    reference: str
    created_at: datetime
    reason: str
    status: Literal["open", "decided"]
    outcome: Optional[str] = None
    decision_note: Optional[str] = None
    decided_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Einwilligungen (Art. 7 DSGVO)
# ---------------------------------------------------------------------------


class ConsentOut(BaseModel):
    consent_type: str
    version: str
    granted_at: datetime
    revoked_at: Optional[datetime] = None
    active: bool


class ConsentRevokeRequest(BaseModel):
    consent_type: Literal["sensitive_data", "verification_media", "immediate_start"]


class AdminPhotoRejectRequest(BaseModel):
    """Ablehnung eines Profilfotos mit Grund (Art. 17 DSA).

    Feste Gründe statt Freitext: Die Begründung soll konkret sein, ohne dass
    lose Notizen zu Personen entstehen. ``note`` ergänzt nur den Fall "other".
    """

    reason: Literal[
        "no_person", "not_account_holder", "multiple_people", "nudity",
        "violence", "minor", "contact_details", "third_party_rights",
        "unusable", "other",
    ]
    note: Optional[str] = Field(default=None, max_length=300)

    _trim = field_validator("note", mode="before")(_strip)
