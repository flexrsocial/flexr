package flexr.social.app.testing

import flexr.social.app.core.locale.AppStrings

/**
 * [AppStrings] fuer JVM-Tests: gibt statt des uebersetzten Texts eine stabile
 * Kennung zurueck. Die Tests pruefen Zustandsuebergaenge, nicht Wortlaute —
 * echte Ressourcen brauechten einen Android-Context und damit Robolectric.
 */
class FakeAppStrings : AppStrings {

    override fun get(id: Int): String = "res:$id"

    override fun get(id: Int, vararg args: Any): String =
        "res:$id(${args.joinToString(",")})"
}
