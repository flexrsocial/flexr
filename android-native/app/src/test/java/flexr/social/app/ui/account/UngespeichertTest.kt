package flexr.social.app.ui.account

import flexr.social.app.domain.model.Gender
import flexr.social.app.domain.model.MyProfile
import flexr.social.app.domain.model.Profile
import flexr.social.app.ui.components.GymPickerState
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class UngespeichertTest {

    private val gymLabel = "Bikram Yoga — Maria-Theresien-Straße 32-34, 1010 Wien"

    private val gespeichert = MyProfile(
        profile = Profile(
            id = "lukas",
            name = "Lukas",
            age = 33,
            city = "Wien",
            gender = Gender.MANN,
            gym = gymLabel,
            bio = "Hi, ich trainiere gern.",
            isOnline = false,
            isVerified = false,
            isPremium = false,
            distanceKm = null,
            photos = emptyList(),
        ),
        plz = "1010",
        birthdate = null,
        searchRadiusKm = 580,
        messagingMutedUntil = null,
    )

    private val unveraendert = AccountUiState(
        postalCode = "1010",
        gymPicker = GymPickerState(query = "Bikram Yoga", selectedLabel = gymLabel),
        bio = "Hi, ich trainiere gern.",
        searchRadiusKm = 580,
    )

    @Test
    fun `frisch gefuelltes formular hat nichts zu speichern`() {
        assertFalse(unveraendert.hatUngespeicherteAenderungen(gespeichert))
        // Leerzeichen am Ende schickt "Profil speichern" ohnehin nicht mit.
        assertFalse(unveraendert.copy(bio = "Hi, ich trainiere gern.  ").hatUngespeicherteAenderungen(gespeichert))
    }

    @Test
    fun `jede gespeicherte angabe zaehlt als aenderung`() {
        assertTrue(unveraendert.copy(bio = "Morgens Kraft.").hatUngespeicherteAenderungen(gespeichert))
        assertTrue(unveraendert.copy(postalCode = "8010").hatUngespeicherteAenderungen(gespeichert))
        assertTrue(unveraendert.copy(searchRadiusKm = 50).hatUngespeicherteAenderungen(gespeichert))
        // Neues Suchwort ohne Auswahl: das Gym ist nicht mehr das gespeicherte.
        assertTrue(
            unveraendert.copy(gymPicker = GymPickerState(query = "John Harris"))
                .hatUngespeicherteAenderungen(gespeichert),
        )
    }

    @Test
    fun `gekappter umkreis ist keine aenderung`() {
        // Ohne Premium kappt der Regler auf die erlaubte Grenze - das Formular
        // zeigt dann 50 km, gespeichert sind noch 580.
        val gekappt = unveraendert.copy(searchRadiusKm = 50, maxSelectableRadiusKm = 50)
        assertFalse(gekappt.hatUngespeicherteAenderungen(gespeichert))
    }

    @Test
    fun `ohne geladenes profil gibt es nichts zu speichern`() {
        assertFalse(unveraendert.copy(bio = "anders").hatUngespeicherteAenderungen(null))
    }
}
