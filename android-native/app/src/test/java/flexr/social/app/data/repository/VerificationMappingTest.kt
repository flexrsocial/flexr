package flexr.social.app.data.repository

import flexr.social.app.data.remote.dto.MyProfileDto
import flexr.social.app.data.remote.dto.VerificationDocumentTypeDto
import flexr.social.app.data.remote.dto.VerificationStatusDto
import flexr.social.app.domain.model.VerificationStatus
import flexr.social.app.domain.model.VerificationStep
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Übersetzung des Verifizierungs-Vertrags aus backend/app/schemas.py.
 *
 * Die Statuswerte entscheiden darüber, ob ein Konto überhaupt nutzbar ist —
 * eine falsche Zuordnung würde entweder aussperren oder zu früh freigeben.
 */
class VerificationMappingTest {

    @Test
    fun `Statuswerte des Backends werden vollstaendig zugeordnet`() {
        assertEquals(VerificationStatus.IN_PROGRESS, VerificationStatus.from("in_progress"))
        assertEquals(VerificationStatus.ID_REQUIRED, VerificationStatus.from("id_required"))
        assertEquals(
            VerificationStatus.REUPLOAD_REQUIRED,
            VerificationStatus.from("reupload_required"),
        )
        assertEquals(VerificationStatus.SUBMITTED, VerificationStatus.from("submitted"))
        assertEquals(VerificationStatus.APPROVED, VerificationStatus.from("approved"))
        assertEquals(VerificationStatus.REJECTED, VerificationStatus.from("rejected"))
    }

    @Test
    fun `unbekannter Status faellt auf den sicheren Wert zurueck`() {
        // Ein neuer Serverwert darf die App nicht zum Absturz bringen; NONE
        // bedeutet "Prüfung steht noch aus" und ist die vorsichtige Annahme.
        assertEquals(VerificationStatus.NONE, VerificationStatus.from("irgendwas-neues"))
        assertEquals(VerificationStatus.NONE, VerificationStatus.from(null))
    }

    @Test
    fun `needsDocument gilt nur fuer den Ausweisschritt`() {
        assertTrue(VerificationStatus.ID_REQUIRED.needsDocument)
        assertTrue(VerificationStatus.REUPLOAD_REQUIRED.needsDocument)
        assertFalse(VerificationStatus.SUBMITTED.needsDocument)
        assertFalse(VerificationStatus.APPROVED.needsDocument)
        assertFalse(VerificationStatus.IN_PROGRESS.needsDocument)
    }

    @Test
    fun `naechster Schritt wird uebernommen`() {
        assertEquals(VerificationStep.SELFIE, VerificationStep.from("selfie"))
        assertEquals(VerificationStep.DOCUMENT, VerificationStep.from("document"))
        assertEquals(VerificationStep.WAIT, VerificationStep.from("wait"))
        assertEquals(VerificationStep.NONE, VerificationStep.from("none"))
        assertEquals(VerificationStep.NONE, VerificationStep.from(null))
    }

    @Test
    fun `Ausweisschritt liefert Dokumenttypen samt Rueckseiten-Bedarf`() {
        val state = VerificationStatusDto(
            status = "id_required",
            nextStep = "document",
            verificationRequired = true,
            accountActivated = false,
            documentTypes = listOf(
                VerificationDocumentTypeDto("id_card", "Personalausweis", needsBack = true),
                VerificationDocumentTypeDto("passport", "Reisepass", needsBack = false),
            ),
        ).toDomain()

        assertEquals(VerificationStep.DOCUMENT, state.nextStep)
        assertFalse(state.accountActivated)
        assertEquals(2, state.documentTypes.size)
        assertTrue(state.documentTypes.first { it.value == "id_card" }.needsBack)
        assertFalse(state.documentTypes.first { it.value == "passport" }.needsBack)
    }

    @Test
    fun `Prüfgrund wird an den Nutzer durchgereicht`() {
        val state = VerificationStatusDto(
            status = "reupload_required",
            nextStep = "document",
            reason = "Die Aufnahme des Ausweises war nicht gut genug lesbar.",
        ).toDomain()

        assertEquals(VerificationStatus.REUPLOAD_REQUIRED, state.status)
        assertTrue(state.reason!!.contains("lesbar"))
    }

    @Test
    fun `Profil ohne Verifizierungsfelder bleibt nutzbar`() {
        // Bestandskonten und ein Backend ohne diese Felder dürfen nicht
        // versehentlich ausgesperrt werden.
        val profil = MyProfileDto(
            id = "u1",
            name = "Test",
            age = 30,
            city = "Wien",
            gender = "mann",
            gym = "McFit",
            plz = "1010",
            birthdate = "1996-01-01",
        ).toDomain()

        assertFalse(profil.verificationRequired)
        assertTrue(profil.isAccountActivated)
        assertFalse(profil.ageVerified)
    }

    @Test
    fun `nicht freigeschaltetes Konto wird als solches erkannt`() {
        val profil = MyProfileDto(
            id = "u2",
            name = "Neu",
            age = 20,
            city = "Graz",
            gender = "frau",
            gym = "McFit",
            plz = "8010",
            birthdate = "2006-01-01",
            verificationRequired = true,
            isAccountActivated = false,
        ).toDomain()

        assertTrue(profil.verificationRequired)
        assertFalse(profil.isAccountActivated)
    }
}
