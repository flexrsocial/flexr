package flexr.social.app.data.billing

import org.junit.Assert.assertEquals
import org.junit.Test

/**
 * Die Kennung muss Zeichen fuer Zeichen der von store_billing.google_account_id
 * im Backend entsprechen - sonst lehnt der Server jeden neuen Play-Kauf ab.
 */
class KontoKennungTest {
    @Test
    fun `entspricht dem Backend-Hash`() {
        assertEquals(
            "8a3b0255097fa9bc7b7d1340161b952182383f69d5fd6a014cc64e683e15522a",
            kontoKennung("0b7c1f7e-2c7e-4a58-9b43-7d7f8e2b1a11"),
        )
    }
}
