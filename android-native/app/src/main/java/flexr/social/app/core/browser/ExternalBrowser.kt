package flexr.social.app.core.browser

import android.content.ActivityNotFoundException
import android.content.Context
import android.content.Intent
import android.net.Uri
import androidx.browser.customtabs.CustomTabsIntent
import androidx.core.net.toUri
import flexr.social.app.core.designsystem.theme.FlexrPalette

/**
 * Öffnet eine externe Seite (Stripe-Checkout, Billing-Portal) in einem
 * Custom Tab.
 *
 * Bewusst kein WebView: Zahlungsvorgänge gehören in den echten Browser des
 * Geräts — dort sind Adressleiste, Zertifikatsprüfung und gespeicherte
 * Zahlungsmittel des Nutzers verfügbar, und die App bekommt zu keinem
 * Zeitpunkt Zahlungsdaten zu sehen.
 */
fun Context.openExternalPage(url: String) {
    val uri: Uri = url.toUri()
    try {
        CustomTabsIntent.Builder()
            .setShowTitle(true)
            .setUrlBarHidingEnabled(false)
            .setDefaultColorSchemeParams(
                androidx.browser.customtabs.CustomTabColorSchemeParams.Builder()
                    .setToolbarColor(FlexrPalette.Ink.value.toInt())
                    .build(),
            )
            .build()
            .launchUrl(this, uri)
    } catch (_: ActivityNotFoundException) {
        // Kein Browser mit Custom-Tab-Unterstützung: normaler Browser-Intent.
        runCatching { startActivity(Intent(Intent.ACTION_VIEW, uri)) }
    }
}
