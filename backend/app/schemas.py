from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


def _age_from_birthdate(birthdate: date) -> int:
    today = date.today()
    return (
        today.year
        - birthdate.year
        - ((today.month, today.day) < (birthdate.month, birthdate.day))
    )


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str = Field(min_length=1, max_length=100)
    # Geburtsdatum statt Alter - das Alter wird serverseitig laufend berechnet.
    birthdate: date
    # Adresse: plz/city kommen aus einer echten PLZ-Lookup im Frontend (OpenPLZ
    # API), city ist der daraus abgeleitete Ort/Gemeinde-Name - keine feste
    # Städteliste mehr, ganz Österreich ist abgedeckt.
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
    def _require_adult(cls, v: date) -> date:
        age = _age_from_birthdate(v)
        if age < 18:
            raise ValueError("Du musst mindestens 18 Jahre alt sein.")
        if age > 99:
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
    # True wenn eine GPS-Position gespeichert ist (sonst gilt die PLZ)
    has_gps_location: bool = False
    phone: Optional[str] = None
    phone_verified: bool = False
    # Befristete Chat-Sperre: bis wann darf der Nutzer keine Nachrichten senden
    # (None oder Vergangenheit = keine aktive Sperre)
    messaging_muted_until: Optional[datetime] = None


class UpdateProfileRequest(BaseModel):
    """Editierbare Profilfelder. PLZ und Ort müssen gemeinsam kommen (der Ort
    wird im Frontend per PLZ-Lookup ermittelt). Das Geburtsdatum ist bewusst
    nicht änderbar."""

    plz: Optional[str] = Field(default=None, pattern=r"^\d{4}$")
    city: Optional[str] = Field(default=None, min_length=1)
    gym: Optional[str] = None
    bio: Optional[str] = Field(default=None, max_length=280)
    search_radius_km: Optional[int] = Field(default=None, ge=2, le=250)


class DeleteAccountRequest(BaseModel):
    """Selbstlöschung: erneute Passworteingabe als Bestätigung."""

    password: str


class LocationUpdateRequest(BaseModel):
    """GPS-Position vom Gerät (grob Österreich/Mitteleuropa plausibilisiert)."""

    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


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


# ---------- Telefonprüfung ----------

class PhoneRequestRequest(BaseModel):
    # E.164-Format, z. B. +436761234567
    phone: str = Field(pattern=r"^\+[1-9]\d{6,14}$")


class PhoneConfirmRequest(BaseModel):
    code: str = Field(pattern=r"^\d{6}$")


# ---------- Foto-Verifizierung ----------

class VerificationSelfieIn(BaseModel):
    prompt: str
    object_key: str


class VerificationSubmitRequest(BaseModel):
    selfies: list[VerificationSelfieIn] = Field(min_length=3, max_length=3)


class VerificationStatusOut(BaseModel):
    status: Literal["none", "in_progress", "submitted", "approved", "rejected"]
    prompts: Optional[list[str]] = None


class AdminVerificationOut(BaseModel):
    id: str
    user_id: str
    user_name: str
    user_email: str
    prompts: list[str]
    selfie_urls: list[dict]  # [{"prompt": ..., "url": ...}]
    profile_photo_urls: list[str]
    created_at: datetime


class ReportRequest(BaseModel):
    reported_user_id: str
    reason: str = Field(min_length=3, max_length=500)


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
    messaging_muted_until: Optional[datetime] = None
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
    """Befristete Chat-Sperre setzen: Dauer in Tagen (1-365)."""

    days: int = Field(ge=1, le=365)


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
    reporter_id: str
    reporter_name: str
    reported_id: str
    reported_name: str
    reason: str
    created_at: datetime


class PhotoModerationOut(BaseModel):
    id: str
    url: str
    status: str
    position: int
    user_id: str
    user_name: str
    user_email: str
