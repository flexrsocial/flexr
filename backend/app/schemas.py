from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from .age import is_plausible_birthdate


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

    # Zwei getrennt einzuholende, aktive Einwilligungen (siehe models.py User) -
    # müssen explizit angehakt werden, ein Default von True wäre unwirksam.
    consent_sensitive_data: bool = Field(
        description="Einwilligung zur Verarbeitung der sexuellen Orientierung (Art. 9 Abs. 2 lit. a DSGVO)"
    )
    consent_withdrawal_waiver: bool = Field(
        description="Kenntnisnahme, dass das Rücktrittsrecht durch sofortigen Leistungsbeginn erlischt (§ 18 Abs. 1 Z 11 FAGG)"
    )

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

    @field_validator("consent_withdrawal_waiver")
    @classmethod
    def _require_withdrawal_waiver_consent(cls, v: bool) -> bool:
        if not v:
            raise ValueError("Kenntnisnahme zum Rücktrittsrecht ist erforderlich.")
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
    search_radius_km: int = 20
    # Alters-/Identitätsprüfung: Muss dieses Konto sie durchlaufen, und ist es
    # bereits freigeschaltet? Nur lesbar - gesetzt wird ausschließlich
    # serverseitig nach der Admin-Entscheidung.
    verification_required: bool = False
    is_account_activated: bool = True
    age_verified: bool = False
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
