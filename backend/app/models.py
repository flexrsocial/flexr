import enum
import uuid
from datetime import datetime, timedelta

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .config import settings
from .database import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


class Gender(str, enum.Enum):
    mann = "mann"
    frau = "frau"


class PhotoStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


# Wien-Gyms aus dem Prototyp — bei Bedarf um weitere österreichische Städte/Gyms erweitern
GYM_CHOICES = [
    "John Harris Fitness",
    "Holmes Place",
    "FitInn",
    "Clever Fit",
    "McFit",
    "Fitness First",
    "Kraftwerk Gym",
    "Iron Gym Wien",
    "USI Wien",
    "Anderes Studio",
]

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_uuid)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)

    name = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    # Adresse: plz/city stammen aus einer echten PLZ-Lookup (OpenPLZ API, siehe
    # Frontend), keine feste Städteliste mehr - ganz Österreich ist abgedeckt.
    plz = Column(String(4), nullable=False)
    city = Column(String, nullable=False)  # aus PLZ abgeleiteter Ort/Gemeinde-Name
    street = Column(String, nullable=False)
    gender = Column(Enum(Gender), nullable=False)
    interest = Column(Enum(Gender), nullable=False)  # sucht Mann oder Frau
    gym = Column(String, nullable=False)  # muss einer der GYM_CHOICES sein
    height_cm = Column(Integer, nullable=True)
    weight_kg = Column(Integer, nullable=True)
    bio = Column(String(280), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    trial_ends_at = Column(
        DateTime,
        default=lambda: datetime.utcnow() + timedelta(days=settings.stripe_trial_days),
    )
    is_subscribed = Column(Boolean, default=False)
    stripe_customer_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)

    # Nachweis-Zeitstempel für zwei gesetzlich getrennt einzuholende Einwilligungen
    # (siehe Hinweise in frontend/datenschutz.html und frontend/agb.html):
    # Art. 9 Abs. 2 lit. a DSGVO - explizite Einwilligung zur Verarbeitung der
    # sexuellen Orientierung (aus gender/interest ableitbar), und § 18 Abs. 1 Z 11
    # FAGG - Verzicht auf das Rücktrittsrecht durch sofortigen Leistungsbeginn.
    sensitive_data_consent_at = Column(DateTime, nullable=False)
    withdrawal_waiver_consent_at = Column(DateTime, nullable=False)

    is_banned = Column(Boolean, default=False, nullable=False)

    photos = relationship("Photo", back_populates="user", cascade="all, delete-orphan")

    def is_active_member(self) -> bool:
        return self.is_subscribed or datetime.utcnow() < self.trial_ends_at


class Photo(Base):
    __tablename__ = "photos"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    url = Column(Text, nullable=False)  # Objekt-Storage-URL, nicht Base64
    position = Column(Integer, default=0)  # 0-4, Reihenfolge
    status = Column(Enum(PhotoStatus), nullable=False, default=PhotoStatus.pending)

    user = relationship("User", back_populates="photos")


class Swipe(Base):
    __tablename__ = "swipes"
    __table_args__ = (UniqueConstraint("from_user_id", "to_user_id", name="uq_swipe_pair"),)

    id = Column(String, primary_key=True, default=gen_uuid)
    from_user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    to_user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    action = Column(String, nullable=False)  # "like" | "pass"
    created_at = Column(DateTime, default=datetime.utcnow)


class Match(Base):
    __tablename__ = "matches"
    __table_args__ = (UniqueConstraint("user_a_id", "user_b_id", name="uq_match_pair"),)

    id = Column(String, primary_key=True, default=gen_uuid)
    user_a_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user_b_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Block(Base):
    __tablename__ = "blocks"
    __table_args__ = (UniqueConstraint("blocker_id", "blocked_id", name="uq_block_pair"),)

    id = Column(String, primary_key=True, default=gen_uuid)
    blocker_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    blocked_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Report(Base):
    __tablename__ = "reports"

    id = Column(String, primary_key=True, default=gen_uuid)
    reporter_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    reported_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    reason = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class AdminUser(Base):
    """Getrenntes Login-System für das Admin-Tool - unabhängig vom Dating-User-Modell,
    damit Admin-Zugänge kein vollständiges Dating-Profil (Alter/Gym/Consent etc.)
    durchlaufen müssen."""

    __tablename__ = "admin_users"

    id = Column(String, primary_key=True, default=gen_uuid)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
