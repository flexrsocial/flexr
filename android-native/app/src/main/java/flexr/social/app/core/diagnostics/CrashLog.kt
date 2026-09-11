package flexr.social.app.core.diagnostics

import android.content.Context
import android.os.Build
import android.util.Log
import flexr.social.app.BuildConfig
import java.io.File
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/**
 * Schreibt den Stapelabzug eines unbehandelten Fehlers in eine Datei, die sich
 * ohne Rechner vom Geraet holen laesst.
 *
 * Warum es das gibt: Am 11.09.2026 startete Fassung 2.6.0 auf einem echten
 * Geraet nicht mehr - die App schloss sich sofort wieder. Ohne angeschlossenen
 * Rechner gibt es kein `adb logcat`, und die Play Console zeigt Abstuerze erst
 * mit Verzoegerung und nur, wenn der Nutzer der Uebermittlung zugestimmt hat.
 * Damit war der einzige Hinweis auf die Ursache nicht erreichbar.
 *
 * Ablageort ist bewusst `getExternalFilesDir` und nicht `filesDir`: Der Ordner
 * liegt unter `Android/data/flexr.social.app/files/` und ist mit jedem
 * Dateimanager und ueber USB zugaenglich, ohne Root und ohne Entwickleroptionen.
 * Er gehoert trotzdem der App und verschwindet mit ihrer Deinstallation.
 *
 * Der Bericht enthaelt ausschliesslich Technisches: Zeitpunkt, App- und
 * Android-Fassung, Geraetemodell und den Stapelabzug. Keine Profildaten, keine
 * Adresse, kein Token - er wird auch nirgendwohin verschickt, sondern liegt nur
 * auf dem Geraet.
 */
object CrashLog {

    private const val TAG = "FlexrCrash"
    private const val PREFIX = "absturz-"
    private const val MAX_DATEIEN = 5

    /**
     * Haengt sich vor den bestehenden Handler.
     *
     * Der vorherige Handler wird danach trotzdem aufgerufen: Er ist es, der den
     * Prozess beendet und den Absturz an die Play Console meldet. Wuerde er
     * uebergangen, bliebe die App in einem toten Zustand stehen, statt sich zu
     * schliessen - und der Play-Bericht fiele weg.
     */
    fun install(context: Context) {
        val vorheriger = Thread.getDefaultUncaughtExceptionHandler()
        Thread.setDefaultUncaughtExceptionHandler { thread, fehler ->
            // Ein Fehler beim Schreiben des Berichts darf den Absturz nicht
            // verschlucken - sonst stuende die App still, statt sich zu beenden.
            runCatching { schreibe(context, thread, fehler) }
                .onFailure { Log.e(TAG, "Absturzbericht konnte nicht geschrieben werden", it) }
            vorheriger?.uncaughtException(thread, fehler)
        }
    }

    private fun schreibe(context: Context, thread: Thread, fehler: Throwable) {
        val ordner = context.getExternalFilesDir(null) ?: context.filesDir
        val zeitpunkt = SimpleDateFormat("yyyy-MM-dd_HH-mm-ss", Locale.US).format(Date())
        val datei = File(ordner, "$PREFIX$zeitpunkt.txt")

        datei.writeText(
            buildString {
                appendLine("FLEXR-Absturzbericht")
                appendLine("Zeitpunkt:  $zeitpunkt")
                appendLine("App:        ${BuildConfig.VERSION_NAME} (${BuildConfig.VERSION_CODE})")
                appendLine("Variante:   ${BuildConfig.FLAVOR}/${BuildConfig.BUILD_TYPE}")
                appendLine("Android:    ${Build.VERSION.RELEASE} (API ${Build.VERSION.SDK_INT})")
                appendLine("Geraet:     ${Build.MANUFACTURER} ${Build.MODEL}")
                appendLine("Thread:     ${thread.name}")
                appendLine()
                appendLine(fehler.stackTraceToString())
            },
        )
        // Zusaetzlich ins Log: Wer doch einen Rechner zur Hand hat, findet es
        // dort sofort, ohne die Datei suchen zu muessen.
        Log.e(TAG, "Absturz in ${datei.absolutePath}", fehler)
        aufraeumen(ordner)
    }

    /** Nur die juengsten Berichte behalten - der Ordner soll nicht volllaufen. */
    private fun aufraeumen(ordner: File) {
        val berichte = ordner.listFiles { f -> f.name.startsWith(PREFIX) } ?: return
        berichte.sortedByDescending { it.lastModified() }
            .drop(MAX_DATEIEN)
            .forEach { it.delete() }
    }
}
