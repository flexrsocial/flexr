import enum
import uuid
from datetime import datetime, timedelta

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .age import age_on
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


class GymStatus(str, enum.Enum):
    approved = "approved"
    pending = "pending"    # von Nutzern vorgeschlagen, wartet auf Admin-Freigabe
    rejected = "rejected"


class ReportOutcome(str, enum.Enum):
    """Ergebnis einer Meldung, das dem Melder mitgeteilt wird (Art. 16 DSA)."""

    no_action = "no_action"      # geprüft, kein Verstoß festgestellt
    action_taken = "action_taken"  # Inhalt entfernt bzw. Konto gesperrt


class ModerationAction(str, enum.Enum):
    """Maßnahme gegen ein Konto - Grundlage der Begründung nach Art. 17 DSA."""

    mute = "mute"  # befristete Chat-Sperre
    ban = "ban"    # Kontosperre


class ModerationSource(str, enum.Enum):
    """Woher die Maßnahme kommt - Art. 17 Abs. 3 lit. b und c DSA verlangen die
    Angabe, ob eine Meldung zugrunde lag und ob dabei automatisiert erkannt
    wurde."""

    user_notice = "user_notice"        # Meldung eines Nutzers bzw. über das Formular
    own_initiative = "own_initiative"  # eigene Moderation ohne Meldung
    authority = "authority"            # behördliche Anordnung


class ModerationBasis(str, enum.Enum):
    """Rechtsgrund der Maßnahme - Art. 17 Abs. 3 lit. d und e DSA unterscheiden
    zwischen rechtswidrigem Inhalt (Gesetzesstelle) und Vertragsverstoß
    (konkrete Regel der Nutzungsrichtlinien)."""

    illegal_content = "illegal_content"  # Verstoß gegen geltendes Recht
    terms = "terms"                      # Verstoß gegen die Nutzungsrichtlinien


class PhotoRejectionReason(str, enum.Enum):
    """Feste Ablehnungsgründe für Profilfotos.

    Vorher wurde ein Foto kommentarlos abgelehnt - der Nutzer sah nur, dass es
    verschwunden war. Art. 17 DSA verlangt für jede Beschränkung
    nutzergenerierter Inhalte eine Begründung, die die tatsächlichen Umstände
    benennt. Eine feste Liste statt Freitext, damit die Begründung immer
    konkret ist und keine losen Notizen zu Personen entstehen.
    """

    no_person = "no_person"                  # keine Person erkennbar
    not_account_holder = "not_account_holder"  # zeigt offenkundig eine andere Person
    multiple_people = "multiple_people"      # mehrere Personen, Zuordnung unklar
    nudity = "nudity"                        # sexuell explizite Darstellung
    violence = "violence"                    # Gewalt- oder Hassdarstellung
    minor = "minor"                          # zeigt offenkundig eine minderjährige Person
    contact_details = "contact_details"      # Kontaktdaten/Links im Bild
    third_party_rights = "third_party_rights"  # fremdes Bildmaterial, Werbung
    unusable = "unusable"                    # unscharf, zu dunkel, Bildschirmfoto
    other = "other"                          # sonstiger Grund


class ConsentType(str, enum.Enum):
    """Einwilligungsarten, die getrennt nachgewiesen werden müssen.

    Ausdrücklich KEINE Einwilligung ist die Annahme der AGB - sie ist
    Vertragsschluss. Sie steht hier trotzdem, weil auch die akzeptierte
    Vertragsfassung nachweisbar sein muss (siehe legal.TERMS_VERSION).
    """

    sensitive_data = "sensitive_data"          # Art. 9 Abs. 2 lit. a DSGVO
    verification_media = "verification_media"  # Selfie + Ausweisaufnahme
    immediate_start = "immediate_start"        # § 10 FAGG, ausdrückliches Verlangen
    terms = "terms"                            # angenommene AGB-Fassung (kein Consent i.S.d. DSGVO)


class NoticeCategory(str, enum.Enum):
    """Meldekategorien des öffentlichen Verfahrens nach Art. 16 DSA."""

    csam = "csam"                          # Darstellung sexuellen Kindesmissbrauchs
    minor = "minor"                        # mutmaßlich minderjährige Person
    trafficking = "trafficking"            # Menschenhandel, sexuelle Ausbeutung
    threat = "threat"                      # Drohung, Gefahr für Leib und Leben
    sexual_content = "sexual_content"      # nicht einvernehmliche intime Aufnahmen
    impersonation = "impersonation"        # Identitätsmissbrauch, fremde Fotos
    fraud = "fraud"                        # Betrug, Erpressung, Scam
    hate = "hate"                          # Hass, Verhetzung, Diskriminierung
    ip_infringement = "ip_infringement"    # Urheber-/Kennzeichenrecht
    data_protection = "data_protection"    # Verstoß gegen Datenschutzrecht
    other_illegal = "other_illegal"        # sonstiger mutmaßlich rechtswidriger Inhalt


class NoticeOutcome(str, enum.Enum):
    """Ergebnis einer Meldung, das dem Melder mitgeteilt wird."""

    action_taken = "action_taken"    # Inhalt entfernt bzw. Konto beschränkt
    no_action = "no_action"          # geprüft, kein Verstoß festgestellt
    forwarded = "forwarded"          # an eine Behörde weitergegeben
    insufficient = "insufficient"    # Angaben reichen zur Prüfung nicht aus


class VerificationStatus(str, enum.Enum):
    """Zustände der Alters- und Identitätsprüfung (eine Prüfung, mehrere Schritte).

    Die Namen der Bestandswerte bleiben unverändert - sie stehen so im
    Postgres-Enum und in den ausgelieferten Apps. ``submitted`` ist der
    "pending_review"-Zustand, ``in_progress`` der Selfie-Schritt.
    """

    in_progress = "in_progress"            # Anweisung ausgegeben, Selfie noch nicht eingereicht
    id_required = "id_required"            # Selfies da, Lichtbildausweis fehlt noch
    reupload_required = "reupload_required"  # Admin fordert eine neue Aufnahme an
    submitted = "submitted"                # alles eingereicht, wartet auf manuelle Prüfung
    approved = "approved"
    rejected = "rejected"


# Schritte, in denen der Nutzer noch etwas beitragen muss
VERIFICATION_OPEN_STATES = (
    VerificationStatus.in_progress,
    VerificationStatus.id_required,
    VerificationStatus.reupload_required,
    VerificationStatus.submitted,
)


class VerificationDocumentType(str, enum.Enum):
    """Zugelassene amtliche Lichtbildausweise."""

    id_card = "id_card"            # Personalausweis
    passport = "passport"          # Reisepass
    drivers_license = "drivers_license"  # Führerschein


# Ausweise, bei denen die Rückseite für die Prüfung gebraucht wird.
#
# Seit 9.8.2026 ist die Liste leer: Foto, Geburtsdatum und Gültigkeit stehen bei
# allen drei zugelassenen Dokumenten auf der Vorder- bzw. Datenseite, und der
# Prüfer braucht für die Altersprüfung nichts von der Rückseite. Eine Aufnahme
# anzufordern, die niemand ansieht, wäre überschüssige Datenerhebung.
#
# Der Mechanismus bleibt: needs_back kommt weiter vom Server, Web und App
# richten sich danach - ein Dokumenttyp mit Rückseite ließe sich also ohne
# Client-Änderung wieder aufnehmen.
DOCUMENT_TYPES_WITH_BACK: tuple[VerificationDocumentType, ...] = ()


class VerificationReviewReason(str, enum.Enum):
    """Feste Prüfgründe für Ablehnung/Neu-Upload - bewusst eine kurze Liste
    statt Freitext, damit keine sensiblen Notizen zum Ausweis entstehen."""

    document_unreadable = "document_unreadable"        # Dokument unleserlich
    details_not_visible = "details_not_visible"        # notwendige Angaben nicht sichtbar
    person_mismatch = "person_mismatch"                # Person stimmt nicht überein
    dob_mismatch = "dob_mismatch"                      # DOB stimmt nicht überein
    underage = "underage"                              # unter 18
    document_unsuitable = "document_unsuitable"        # Dokument ungeeignet
    selfie_unusable = "selfie_unusable"                # Selfies nicht verwertbar
    other = "other"                                    # sonstiger Prüfgrund


# Legacy-Liste aus dem Prototyp - dient nur noch als Seed für die gyms-Tabelle
# (bestehende Profile referenzieren diese Namen). Die eigentliche Gym-Liste
# lebt in der Tabelle Gym (OSM-Import + freigegebene Nutzer-Vorschläge).
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


class Gym(Base):
    """Fitnessstudios in Österreich: Basisdaten aus OpenStreetMap (Name,
    Straße, Hausnummer, PLZ), ergänzt um Nutzer-Vorschläge, die nach
    Admin-Freigabe in die Auswahlliste aufgenommen werden."""

    __tablename__ = "gyms"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String, nullable=False, index=True)
    street = Column(String, nullable=False, default="")
    house_number = Column(String, nullable=False, default="")
    plz = Column(String(4), nullable=False, default="", index=True)
    city = Column(String, nullable=False, default="")
    status = Column(Enum(GymStatus), nullable=False, default=GymStatus.pending)
    suggested_by = Column(
        String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at = Column(DateTime, default=datetime.utcnow)

    @property
    def label(self) -> str:
        """Anzeigename inkl. Adresse, z. B. "FITINN — Johnstraße 65, 1150 Wien"."""
        addr = f"{self.street} {self.house_number}".strip()
        place = f"{self.plz} {self.city}".strip()
        parts = [p for p in (addr, place) if p]
        return f"{self.name} — {', '.join(parts)}" if parts else self.name

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_uuid)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)

    name = Column(String, nullable=False)
    # Geburtsdatum statt festem Alter - das Alter wird daraus laufend berechnet
    # und bleibt so in allen Profilen automatisch aktuell.
    birthdate = Column(Date, nullable=False)
    # Adresse: city ist der amtliche Ortsname zur PLZ (app/data/plz_cities.json,
    # siehe geo.py) - keine feste Städteliste, ganz Österreich ist abgedeckt.
    plz = Column(String(4), nullable=False)
    city = Column(String, nullable=False)  # aus der PLZ abgeleiteter Ortsname
    gender = Column(Enum(Gender), nullable=False)
    interest = Column(Enum(Gender), nullable=False)  # sucht Mann oder Frau
    gym = Column(String, nullable=False)  # muss einer der GYM_CHOICES sein
    bio = Column(String(280), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    trial_ends_at = Column(
        DateTime,
        default=lambda: datetime.utcnow() + timedelta(days=settings.stripe_trial_days),
    )
    is_subscribed = Column(Boolean, default=False)
    stripe_customer_id = Column(String, nullable=True)
    stripe_subscription_id = Column(String, nullable=True)

    # Nachweis-Zeitstempel der ausdrücklichen Einwilligung nach Art. 9 Abs. 2
    # lit. a DSGVO zur Verarbeitung der aus gender/interest ableitbaren sexuellen
    # Orientierung. Die versionierte Fassung steht zusätzlich in ``consents``;
    # dieses Feld bleibt als schneller Zugriff und für Bestandskonten.
    sensitive_data_consent_at = Column(DateTime, nullable=False)

    # Frühere "Verzicht auf das Rücktrittsrecht"-Erklärung (§ 18 Abs. 1 Z 11
    # FAGG), die bei jeder Registrierung erzwungen wurde.
    #
    # Am 15.08.2026 aufgegeben: Bei der Registrierung entsteht überhaupt kein
    # entgeltlicher Vertrag - es wird kein Zahlungsmittel erhoben, und der
    # Probemonat wandelt sich nicht von selbst in ein Abo um (siehe
    # routers/billing.py). Ohne entgeltlichen Vertrag gibt es kein
    # Rücktrittsrecht, auf das man verzichten könnte; die Erklärung war
    # gegenstandslos und in ihrer Formulierung irreführend.
    #
    # Die Spalte bleibt für Bestandskonten erhalten, ist aber nullable und wird
    # bei neuen Registrierungen nicht mehr gesetzt.
    withdrawal_waiver_consent_at = Column(DateTime, nullable=True)

    is_banned = Column(Boolean, default=False, nullable=False)

    # Befristete Chat-Sperre ("Abmahnung"): der Nutzer kann sich weiter einloggen
    # und Chats lesen, aber bis zu diesem Zeitpunkt keine Nachrichten senden.
    # NULL = keine Sperre.
    messaging_muted_until = Column(DateTime, nullable=True)

    # Art. 17 DSA: Jede Beschränkung braucht eine Begründung für den Betroffenen.
    # Gilt für die letzte verhängte Maßnahme; wird beim Aufheben geleert.
    #
    # Bis 15.08.2026 bestand die Begründung aus einem einzigen Freitextfeld.
    # Art. 17 Abs. 3 DSA verlangt aber mehr als einen Satz: Umfang der Maßnahme,
    # die zugrunde liegenden Tatsachen, ob eine Meldung Anlass war, ob dabei
    # automatisiert erkannt wurde, und die konkrete Rechts- bzw. AGB-Grundlage.
    # Deshalb die zusätzlichen Felder - moderation_reason bleibt die
    # Zusammenfassung in einem Satz.
    moderation_action = Column(String(20), nullable=True)  # ModerationAction
    moderation_reason = Column(String(500), nullable=True)
    moderation_action_at = Column(DateTime, nullable=True)
    # Was genau beschränkt wurde ("Senden von Nachrichten", "gesamtes Konto").
    moderation_scope = Column(String(200), nullable=True)
    # Die tatsächlichen Umstände, auf die sich die Entscheidung stützt.
    moderation_facts = Column(String(1000), nullable=True)
    moderation_source = Column(String(20), nullable=True)   # ModerationSource
    # Ob bei der Erkennung ein automatisiertes Mittel beteiligt war. Bei FLEXR
    # sind das die Filter aus safety_checks.py - die Entscheidung selbst trifft
    # immer ein Mensch.
    moderation_automated = Column(Boolean, default=False, nullable=False)
    moderation_basis = Column(String(20), nullable=True)    # ModerationBasis
    # Fundstelle: Gesetzesstelle bei rechtswidrigem Inhalt, sonst der Abschnitt
    # der Nutzungsrichtlinien.
    moderation_basis_detail = Column(String(300), nullable=True)

    # Selbstlöschung: Konto wird sofort deaktiviert (Login gesperrt, unsichtbar),
    # nach 30 Tagen Karenz endgültig gelöscht (siehe Datenschutzerklärung Punkt 5).
    deleted_at = Column(DateTime, nullable=True)

    # Foto-Verifizierung (blauer Haken) - wird nach manueller Prüfung der
    # Verifizierungs-Selfies gegen die Profilfotos gesetzt.
    is_verified = Column(Boolean, default=False, nullable=False)

    # E-Mail-Bestätigung per Aktivierungslink. Steht vor der Alters- und
    # Identitätsprüfung: Ein Mensch soll keine Ausweisaufnahme begutachten,
    # solange nicht feststeht, dass die Adresse überhaupt dem Nutzer gehört -
    # und ein Tippfehler soll auffallen, solange der Nutzer noch weiß, was er
    # eingegeben hat (es gibt kein "Passwort vergessen"). Bestandskonten setzt
    # die Migration auf den Zeitpunkt der Umstellung.
    email_verified_at = Column(DateTime, nullable=True)

    # ---- Alters- und Identitätsprüfung (manuell, siehe VerificationRequest) ----
    # Muss dieses Konto die Prüfung durchlaufen, bevor es nutzbar wird? Neue
    # Registrierungen: ja. Bestandskonten werden von der Migration auf False
    # gesetzt und können vom Admin gezielt nachgefordert werden (siehe
    # POST /api/admin/users/{id}/require-verification).
    verification_required = Column(Boolean, default=True, nullable=False)
    # Wann die Prüfung (zuletzt) verlangt wurde. Bei neuen Registrierungen der
    # Zeitpunkt der Anmeldung, bei Bestandskonten der Zeitpunkt der Nachforderung
    # durch den Admin. Entscheidungen, die davor gefallen sind, blockieren einen
    # neu angeforderten Durchlauf nicht (siehe routers/verification.py).
    verification_required_at = Column(DateTime, nullable=True)
    # Zeitpunkt der Freischaltung. Solange NULL und verification_required True,
    # ist das Konto angelegt, aber nicht benutzbar (kein Deck, kein Chat, für
    # andere unsichtbar).
    activated_at = Column(DateTime, nullable=True)
    # Ergebnis der Altersprüfung. Wird ausschließlich serverseitig nach
    # Admin-Freigabe gesetzt - nie aus einem Client-Feld übernommen.
    age_verified = Column(Boolean, default=False, nullable=False)
    age_verified_at = Column(DateTime, nullable=True)
    # Wie geprüft wurde. Aktuell nur "manual_id": manuelle Sichtprüfung eines
    # vorgelegten Lichtbildausweises - ausdrücklich kein KYC-Verfahren.
    verification_method = Column(String(20), nullable=True)

    # Telefonprüfung (SMS-OTP): Nummer wird erst nach bestätigtem Code gesetzt.
    phone = Column(String, nullable=True)
    phone_verified_at = Column(DateTime, nullable=True)

    # Wird bei authentifizierten Requests (gedrosselt) aktualisiert - Basis für
    # die Online-Anzeige bei Matches.
    last_seen_at = Column(DateTime, nullable=True)

    # Radius der Umkreissuche. Mittelpunkt ist die Adresse des eingetragenen
    # Gyms (siehe gym_geo.py) - so tauchen auch Leute aus nahegelegenen
    # Studios auf, nicht nur die aus dem eigenen.
    search_radius_km = Column(Integer, nullable=False, default=20)

    # order_by ist Pflicht, nicht Kosmetik: Web und App nehmen photos[0] als
    # Hauptfoto (Karte, Avatar, Chat-Kopf). Ohne feste Sortierung liefert die
    # DB die Zeilen in beliebiger Reihenfolge - das Hauptfoto würde nach jedem
    # Schreibzugriff springen.
    photos = relationship(
        "Photo",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="(Photo.position, Photo.id)",
    )

    @property
    def age(self) -> int:
        return age_on(self.birthdate)

    @property
    def is_account_activated(self) -> bool:
        """Konto freigeschaltet? Bestandskonten (verification_required False)
        sind es unverändert; neue Konten erst nach bestandener Prüfung."""
        return not self.verification_required or self.activated_at is not None

    def is_active_member(self) -> bool:
        return self.is_subscribed or datetime.utcnow() < self.trial_ends_at

    @property
    def is_messaging_muted(self) -> bool:
        return (
            self.messaging_muted_until is not None
            and self.messaging_muted_until > datetime.utcnow()
        )

    @property
    def phone_verified(self) -> bool:
        return self.phone_verified_at is not None

    @property
    def email_verified(self) -> bool:
        return self.email_verified_at is not None

    @property
    def is_online(self) -> bool:
        """Online = in den letzten 5 Minuten aktiv gewesen. Property statt
        Methode, damit Pydantic das Feld direkt in ProfileOut übernehmen kann."""
        return (
            self.last_seen_at is not None
            and datetime.utcnow() - self.last_seen_at < timedelta(minutes=5)
        )


class Photo(Base):
    __tablename__ = "photos"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    url = Column(Text, nullable=False)  # Objekt-Storage-URL, nicht Base64
    # Quadratisches Thumbnail (256px, clientseitig beim Upload erzeugt) für
    # kleine Avatare (Match-Liste, Chat-Header) - Fallback auf url wenn NULL.
    thumb_url = Column(Text, nullable=True)
    position = Column(Integer, default=0)  # 0-4, Reihenfolge
    status = Column(Enum(PhotoStatus), nullable=False, default=PhotoStatus.pending)

    # Art. 17 DSA: Auch die Ablehnung eines einzelnen Fotos ist eine
    # Beschränkung nutzergenerierten Inhalts und braucht eine Begründung.
    # Vorher verschwand ein abgelehntes Foto kommentarlos.
    rejection_reason = Column(String(40), nullable=True)  # PhotoRejectionReason
    rejection_note = Column(String(300), nullable=True)   # Ergänzung bei "other"
    rejected_at = Column(DateTime, nullable=True)

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

    # "Chatverlauf leeren" wirkt nur für die leerende Seite: Nachrichten vor
    # diesem Zeitpunkt werden für den jeweiligen Nutzer ausgeblendet, für die
    # andere Seite bleibt der Verlauf erhalten.
    user_a_cleared_at = Column(DateTime, nullable=True)
    user_b_cleared_at = Column(DateTime, nullable=True)

    def cleared_at_for(self, user_id: str):
        return self.user_a_cleared_at if user_id == self.user_a_id else self.user_b_cleared_at

    def set_cleared_at(self, user_id: str, ts) -> None:
        if user_id == self.user_a_id:
            self.user_a_cleared_at = ts
        else:
            self.user_b_cleared_at = ts


class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=gen_uuid)
    match_id = Column(String, ForeignKey("matches.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content = Column(String(2000), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    read_at = Column(DateTime, nullable=True)

    # Automatische Sicherheitsprüfung: auffällige Nachrichten werden zugestellt,
    # aber fürs Admin-Review markiert (kein Auto-Block wegen False Positives).
    is_flagged = Column(Boolean, default=False, nullable=False)
    flag_reason = Column(String, nullable=True)

    # Chat-Schutzfunktion: content ist das Original (Absender + Admin sehen es),
    # display_content ist die für den Empfänger zensierte Fassung (Links/Kontakt-
    # daten ersetzt). was_censored = ob überhaupt etwas ersetzt wurde.
    display_content = Column(String(2000), nullable=True)
    was_censored = Column(Boolean, default=False, nullable=False)


class PhoneVerification(Base):
    """Laufende Telefonprüfung: 6-stelliger Code (nur als Hash gespeichert),
    10 Minuten gültig, max. 5 Fehlversuche."""

    __tablename__ = "phone_verifications"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    phone = Column(String, nullable=False)
    code_hash = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    attempts = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class EmailVerification(Base):
    """Offene E-Mail-Bestätigung: Zufallstoken, nur als Hash gespeichert.

    Der Token steht im Aktivierungslink und ist damit nichts anderes als ein
    Passwort auf Zeit - er wird deshalb wie der SMS-Code behandelt und nie im
    Klartext abgelegt. Pro Konto gibt es höchstens einen offenen Vorgang; ein
    neuer Versand ersetzt den alten, damit ein abgefangener älterer Link nicht
    parallel gültig bleibt.
    """

    __tablename__ = "email_verifications"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    # Die Adresse wird mitgeführt: Ändert sie sich später, ist ein noch offener
    # Link für die alte Adresse wertlos und darf nicht mehr greifen.
    email = Column(String, nullable=False)
    token_hash = Column(String, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class UserDevice(Base):
    """Geräteprüfung: Client erzeugt eine zufällige Geräte-ID (localStorage) und
    sendet sie bei Registrierung/Login mit. Dient der Erkennung von
    Mehrfachkonten und blockiert Neuregistrierungen von Geräten gesperrter
    Nutzer (Ban-Evasion-Schutz, wie bei Tinder)."""

    __tablename__ = "user_devices"
    __table_args__ = (UniqueConstraint("user_id", "device_id", name="uq_user_device"),)

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    device_id = Column(String, nullable=False, index=True)
    user_agent = Column(String, nullable=True)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)


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
    # Vom Admin abgeschlossen - bleibt als Nachweis erhalten, verschwindet aber
    # aus der offenen Meldungsliste.
    dismissed_at = Column(DateTime, nullable=True)

    # Art. 16 Abs. 5 DSA: Der Melder muss die Entscheidung über seine Meldung
    # erfahren. outcome sagt, ob eingeschritten wurde, decision_note ist der
    # Text, den der Melder zu sehen bekommt.
    outcome = Column(String(20), nullable=True)  # None = offen, sonst ReportOutcome
    decision_note = Column(String(500), nullable=True)

    @property
    def reference(self) -> str:
        """Kurzes Aktenzeichen für die Empfangsbestätigung (Art. 16 Abs. 4)."""
        return self.id.replace("-", "")[:8].upper()


class VerificationRequest(Base):
    """Alters- und Identitätsprüfung in einem Vorgang.

    Schritt 1: Der Server gibt die Anweisung vor ("Schau direkt in die Kamera"),
    der Nutzer nimmt das Selfie live über die Kamera auf. Schritt 2: ein amtlicher
    Lichtbildausweis wird temporär hochgeladen. Ein Mensch vergleicht danach
    Profilfotos, Selfie und Ausweisfoto und prüft das Geburtsdatum - es findet
    keine automatisierte biometrische Auswertung statt.

    prompts/selfies/documents sind JSON-serialisiert. selfies und documents
    werden nach der Entscheidung geleert; die Objekte im Storage werden dabei
    gelöscht (siehe cleanup_pending).
    """

    __tablename__ = "verification_requests"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(Enum(VerificationStatus), nullable=False, default=VerificationStatus.in_progress)
    prompts = Column(Text, nullable=False)   # JSON: ["Schau direkt in die Kamera"]
    selfies = Column(Text, nullable=True)    # JSON: [{"prompt": ..., "object_key": ...}]
    created_at = Column(DateTime, default=datetime.utcnow)
    decided_at = Column(DateTime, nullable=True)

    # ---- Ausweisschritt ----
    document_type = Column(String(20), nullable=True)  # VerificationDocumentType
    # JSON: [{"side": "front"|"back", "object_key": ...}] - Keys liegen im
    # privaten Prefix verification-documents/, nie unter der öffentlichen
    # Foto-Basis-URL.
    documents = Column(Text, nullable=True)
    submitted_at = Column(DateTime, nullable=True)  # vollständig eingereicht

    # ---- Prüfung ----
    reviewed_by = Column(
        String, ForeignKey("admin_users.id", ondelete="SET NULL"), nullable=True
    )
    review_reason = Column(String(40), nullable=True)  # VerificationReviewReason

    # True, wenn nach der Entscheidung noch Objekte im Storage liegen, weil das
    # Löschen fehlgeschlagen ist. Der Vorgang gilt dann NICHT als abgearbeitet;
    # app/cleanup.py wiederholt die Löschung.
    cleanup_pending = Column(Boolean, default=False, nullable=False)


class UnderageSignupAttempt(Base):
    """Registrierungsversuch mit einem Geburtsdatum unter 18.

    Bewusst datensparsam: nur die Geräte-ID (dieselbe zufällige ID wie bei der
    Geräteprüfung) und der Zeitpunkt. Kein Name, keine E-Mail, kein
    Geburtsdatum - für die Schutzwirkung reicht das Zählen der Versuche.

    Zweck: Ein einzelner Tippfehler soll sofort korrigierbar bleiben, das
    Durchprobieren des Altersfilters aber nicht. Ab dem zweiten Versuch
    innerhalb des Zeitfensters wird die Registrierung von diesem Gerät
    befristet gesperrt (siehe routers/auth.py).
    """

    __tablename__ = "underage_signup_attempts"

    id = Column(String, primary_key=True, default=gen_uuid)
    device_id = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class DailyAccess(Base):
    """Ein Eintrag pro Nutzer, Tag und Ländercode - Basis für die
    Zugriffsstatistik im Admin-Dashboard (tagesaktive Nutzer, Länderverteilung).
    Es wird bewusst KEINE IP-Adresse gespeichert, nur der grobe Ländercode aus
    der Geo-Zuordnung (bzw. der aus der PLZ abgeleitete Länderbezug "AT")."""

    __tablename__ = "daily_access"
    __table_args__ = (
        UniqueConstraint("user_id", "day", "country", name="uq_daily_access"),
    )

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    day = Column(Date, nullable=False, index=True)
    country = Column(String(2), nullable=False, default="AT")


class Consent(Base):
    """Versionierter Einwilligungsnachweis (Art. 7 Abs. 1 DSGVO).

    Bisher gab es nur zwei Zeitstempel am Nutzer - ohne Fassung des Textes, zu
    dem eingewilligt wurde, und ohne Möglichkeit, einen Widerruf festzuhalten.
    Art. 7 Abs. 1 verlangt aber den Nachweis, *wozu* eingewilligt wurde, und
    Art. 7 Abs. 3, dass der Widerruf so einfach ist wie die Erteilung.

    Bewusst OHNE IP-Adresse: Für den Nachweis reicht, wer wann zu welcher
    Fassung eingewilligt hat. Eine IP wäre zusätzliche personenbezogene Daten
    ohne eigenen Zweck.
    """

    __tablename__ = "consents"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    consent_type = Column(String(30), nullable=False)  # ConsentType
    # Fassung des Textes, zu dem eingewilligt wurde (siehe app/legal.py).
    version = Column(String(20), nullable=False)
    granted_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    # Gesetzt, sobald widerrufen wurde. Der Datensatz bleibt als Nachweis
    # bestehen - gelöscht wird er erst mit dem Konto.
    revoked_at = Column(DateTime, nullable=True)

    @property
    def is_active(self) -> bool:
        return self.revoked_at is None


class CheckoutConsent(Base):
    """Die zwei getrennten Erklärungen beim kostenpflichtigen Checkout.

    Bewusst eine eigene Tabelle, nicht ``Consent``: ``Consent`` bildet
    widerrufbare DSGVO-Einwilligungen ab (Art. 9, Verifizierungsmedien). Die
    beiden Erklärungen hier sind etwas anderes - Wissenserklärungen zum
    Vertrag (§ 10, § 18 Abs. 1 Z 1 FAGG), die nicht "widerrufen" werden
    können, sondern rechtlich fortwirken, solange der Vertrag läuft. Deshalb
    getrennt gespeichert und direkt mit der Abo-ID verknüpfbar, sobald diese
    aus dem Stripe-Checkout zurückkommt (siehe routers/billing.py).
    """

    __tablename__ = "checkout_consents"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Checkbox 1: "Ich stimme ausdrücklich zu, dass FLEXR bereits vor Ablauf
    # der 14-tägigen Rücktrittsfrist mit der Erbringung der kostenpflichtigen
    # Dienstleistung beginnt."
    immediate_start_version = Column(String(20), nullable=False)
    immediate_start_granted_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Checkbox 2: "Ich bestätige, dass ich zur Kenntnis genommen habe, dass
    # mein Rücktrittsrecht nach vollständiger Vertragserfüllung durch FLEXR
    # erlischt, wenn die gesetzlichen Voraussetzungen dafür erfüllt sind."
    withdrawal_ack_version = Column(String(20), nullable=False)
    withdrawal_ack_granted_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Erst nach dem Bezahlvorgang bekannt - vom Stripe-Webhook nachgetragen,
    # sobald checkout.session.completed die Abo-ID liefert (nullable bis dahin).
    stripe_subscription_id = Column(String, nullable=True, index=True)
    stripe_customer_id = Column(String, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)


class EmailNotification(Base):
    """Idempotenz- und Versandnachweis fuer transaktionale E-Mails.

    Stripe stellt Webhooks mindestens einmal zu und wiederholt sie bei
    Zeitueberschreitungen. Ohne einen stabilen Schluessel bekaeme ein Nutzer
    dadurch dieselbe Zahlungs- oder Kuendigungsnachricht mehrfach. Der
    Schluessel ist ein SHA-256-Hash der fachlichen Ereignis-ID; Mailadresse,
    Nutzer-ID und Nachrichteninhalt werden nicht gespeichert.
    """

    __tablename__ = "email_notifications"

    id = Column(String, primary_key=True, default=gen_uuid)
    notification_key = Column(String(64), unique=True, nullable=False, index=True)
    kind = Column(String(50), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)


class WithdrawalDeclaration(Base):
    """Rücktrittserklärung über die Online-Rücktrittsfunktion (§ 13a FAGG).

    Ausdrücklich etwas anderes als "Abo kündigen": Die Kündigung beendet einen
    laufenden Vertrag zum Periodenende, der Rücktritt löst ihn binnen 14 Tagen
    rückwirkend auf. Beides muss getrennt erreichbar sein.

    Die Erklärung kann auch von jemandem kommen, der gerade nicht angemeldet
    ist - deshalb ist user_id optional und Name/E-Mail werden mitgeschrieben.
    Der Bestätigungstext wird vollständig gespeichert, weil § 13a Abs. 4 FAGG
    eine Bestätigung auf dauerhaftem Datenträger verlangt, die Inhalt, Datum
    und Uhrzeit der Erklärung wiedergibt.
    """

    __tablename__ = "withdrawal_declarations"

    id = Column(String, primary_key=True, default=gen_uuid)
    # Optional: Wer angemeldet erklärt, bekommt die Zuordnung geschenkt.
    # ondelete SET NULL, damit die Erklärung eine Kontolöschung überdauert -
    # sie ist der Nachweis, dass zurückgetreten wurde.
    user_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Clientseitig erzeugte UUID, eindeutig - Grundlage der Idempotenz bei
    # Doppelklick/Doppel-Submit (siehe routers/withdrawal.py).
    request_id = Column(String(64), unique=True, nullable=True, index=True)

    name = Column(String(120), nullable=False)
    email = Column(String, nullable=False, index=True)
    # Freie Bezeichnung des Vertrags/Kontos, wie der Erklärende sie angibt
    # (E-Mail des Kontos, Rechnungsnummer, Stripe-Referenz).
    contract_reference = Column(String(200), nullable=True)
    # Optionale eigene Worte des Erklärenden.
    message = Column(String(1000), nullable=True)

    # Wortlaut der Erklärung, wie er dem Erklärenden angezeigt und bestätigt
    # wurde - nicht nachträglich rekonstruiert, sondern festgehalten.
    declaration_text = Column(Text, nullable=False)

    received_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    # Dieselbe Sekunde noch einmal, nur in Europe/Vienna und als fertig
    # formatierte Zeichenkette - so, wie sie dem Erklärenden angezeigt und
    # per Mail bestätigt wird. Der maßgebliche Zeitpunkt bleibt received_at
    # (UTC); diese Spalte ist nur die menschenlesbare Lokalzeit dazu.
    received_at_vienna = Column(String(40), nullable=False)
    confirmation_sent_at = Column(DateTime, nullable=True)
    # "email" - weitere dauerhafte Datenträger sind derzeit nicht angebunden.
    confirmation_channel = Column(String(20), nullable=True)

    # Bearbeitungsstand: "eingegangen" -> "bestaetigt" (Mail raus) ->
    # "abgeschlossen" (Betreiber hat Rueckabwicklung/Storno dokumentiert).
    status = Column(String(30), nullable=False, default="eingegangen")

    # Bearbeitungsstand auf Betreiberseite (Rückabwicklung, Stripe-Storno).
    processed_at = Column(DateTime, nullable=True)
    processing_note = Column(String(500), nullable=True)
    # Gesetzt, sobald ein zugeordnetes Stripe-Abo automatisch an der
    # Verlaengerung gehindert wurde (siehe withdrawal.py).
    subscription_stopped_at = Column(DateTime, nullable=True)

    @property
    def reference(self) -> str:
        """Aktenzeichen für die Bestätigung, Form: W-XXXXXXXX."""
        return "W-" + self.id.replace("-", "")[:8].upper()


class Notice(Base):
    """Meldung nach Art. 16 DSA über das öffentliche Formular.

    Getrennt von ``Report``: Eine Meldung nach Art. 16 muss *jeder* abgeben
    können - auch wer kein Konto hat und deshalb kein Profil "melden" kann.
    Report bleibt die Ein-Klick-Meldung aus der App heraus, Notice das
    förmliche Verfahren mit Begründung, Fundstelle und
    Gutgläubigkeitserklärung.

    Zur Anonymität: Art. 16 Abs. 3 DSA nimmt Meldungen zu Straftaten nach den
    Artikeln 3 bis 7 der Richtlinie 2011/93/EU (Darstellungen sexuellen
    Kindesmissbrauchs u. a.) von der Pflicht aus, Name und E-Mail anzugeben.
    Für diese Kategorien sind die Kontaktfelder deshalb optional.
    """

    __tablename__ = "notices"

    id = Column(String, primary_key=True, default=gen_uuid)
    category = Column(String(30), nullable=False)  # NoticeCategory

    # Art. 16 Abs. 2 lit. a: Begründung, warum der Inhalt rechtswidrig sein soll.
    explanation = Column(Text, nullable=False)
    # Art. 16 Abs. 2 lit. b: genaue elektronische Fundstelle - Profilname,
    # Konto-ID, Chatverlauf, Zeitpunkt.
    content_reference = Column(String(500), nullable=False)

    # Art. 16 Abs. 2 lit. c - bei den Ausnahmekategorien leer.
    reporter_name = Column(String(120), nullable=True)
    reporter_email = Column(String, nullable=True)
    # Art. 16 Abs. 2 lit. d: Erklärung in gutem Glauben.
    good_faith = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    # Art. 16 Abs. 4: unverzügliche Empfangsbestätigung.
    acknowledged_at = Column(DateTime, nullable=True)

    # Art. 16 Abs. 5 und 6: Entscheidung, ob automatisierte Mittel beteiligt
    # waren, und Begründung.
    decided_at = Column(DateTime, nullable=True)
    outcome = Column(String(20), nullable=True)  # NoticeOutcome
    decision_reason = Column(Text, nullable=True)
    decision_automated = Column(Boolean, default=False, nullable=False)

    @property
    def reference(self) -> str:
        """Aktenzeichen für die Empfangsbestätigung, Form: M-XXXXXXXX."""
        return "M-" + self.id.replace("-", "")[:8].upper()

    @property
    def allows_anonymous(self) -> bool:
        return self.category == NoticeCategory.csam.value


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
