package flexr.social.app.core.diagnostics

import android.content.ContentValues
import android.content.Context
import android.os.Build
import android.os.Environment
import android.provider.MediaStore
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
 * **Nachtrag vom 18.09.2026:** "Mit jedem Dateimanager zugaenglich" stimmt so
 * nicht mehr. Seit Android 11 sperrt das System den Zugriff auf `Android/data`
 * fremder Apps fuer jeden Dateimanager - auch fuer Samsungs "Eigene Dateien"
 * und selbst fuer X-plore mitsamt seinem SAF-Grant-Trick, der bei `media/` noch
 * funktioniert, bei `data/` und `obb/` aber schlicht "Zugriff verweigert"
 * zeigt. Ohne Rechner (USB oder gleiches WLAN fuer kabelloses ADB) war der
 * Bericht dieser Sitzung dadurch faktisch unerreichbar - genau die Lage, die
 * dieser Mechanismus eigentlich verhindern sollte.
 *
 * Deshalb zusaetzlich eine Kopie in `Downloads/`: ueber die MediaStore-Downloads-
 * Sammlung angelegt, braucht das seit Android 10 keine Berechtigung (eine App
 * darf dort eigene Dateien anlegen, ohne WRITE_EXTERNAL_STORAGE), und der
 * Ordner ist ganz normal sichtbar - in "Eigene Dateien", in jedem
 * Download-Manager, beim Dateianhang in einer Mail. Die Kopie unter
 * `Android/data/.../files/` bleibt bestehen, falls doch einmal ein Rechner
 * zur Hand ist.
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
        val dateiname = "$PREFIX$zeitpunkt.txt"
        val inhalt = buildString {
            appendLine("FLEXR-Absturzbericht")
            appendLine("Zeitpunkt:  $zeitpunkt")
            appendLine("App:        ${BuildConfig.VERSION_NAME} (${BuildConfig.VERSION_CODE})")
            appendLine("Variante:   ${BuildConfig.FLAVOR}/${BuildConfig.BUILD_TYPE}")
            appendLine("Android:    ${Build.VERSION.RELEASE} (API ${Build.VERSION.SDK_INT})")
            appendLine("Geraet:     ${Build.MANUFACTURER} ${Build.MODEL}")
            appendLine("Thread:     ${thread.name}")
            appendLine()
            appendLine(fehler.stackTraceToString())
        }

        val datei = File(ordner, dateiname)
        datei.writeText(inhalt)
        // Zusaetzlich ins Log: Wer doch einen Rechner zur Hand hat, findet es
        // dort sofort, ohne die Datei suchen zu muessen.
        Log.e(TAG, "Absturz in ${datei.absolutePath}", fehler)
        aufraeumen(ordner)

        // Zweite Kopie dort, wo sie ohne Rechner tatsaechlich abzuholen ist -
        // siehe Klassenkommentar. Eigener runCatching-Block: Scheitert das
        // (kein MediaStore auf uralten ROMs o.ae.), soll wenigstens die erste
        // Kopie oben stehen bleiben.
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            runCatching { kopiereNachDownloads(context, dateiname, inhalt) }
                .onFailure { Log.e(TAG, "Kopie nach Downloads/ fehlgeschlagen", it) }
        }
    }

    private fun kopiereNachDownloads(context: Context, dateiname: String, inhalt: String) {
        val werte = ContentValues().apply {
            put(MediaStore.MediaColumns.DISPLAY_NAME, dateiname)
            put(MediaStore.MediaColumns.MIME_TYPE, "text/plain")
            put(MediaStore.MediaColumns.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS)
        }
        val uri = context.contentResolver.insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, werte)
            ?: return
        context.contentResolver.openOutputStream(uri)?.use { it.write(inhalt.toByteArray()) }
        aufraeumenDownloads(context)
    }

    /** Nur die juengsten Berichte behalten - der Ordner soll nicht volllaufen. */
    private fun aufraeumen(ordner: File) {
        val berichte = ordner.listFiles { f -> f.name.startsWith(PREFIX) } ?: return
        berichte.sortedByDescending { it.lastModified() }
            .drop(MAX_DATEIEN)
            .forEach { it.delete() }
    }

    /** Dasselbe fuer die Downloads-Kopien - per MediaStore-Abfrage statt File-Listing. */
    private fun aufraeumenDownloads(context: Context) {
        val projektion = arrayOf(MediaStore.MediaColumns._ID, MediaStore.MediaColumns.DATE_ADDED)
        val auswahl = "${MediaStore.MediaColumns.DISPLAY_NAME} LIKE ?"
        context.contentResolver.query(
            MediaStore.Downloads.EXTERNAL_CONTENT_URI,
            projektion,
            auswahl,
            arrayOf("$PREFIX%"),
            "${MediaStore.MediaColumns.DATE_ADDED} DESC",
        )?.use { cursor ->
            val idSpalte = cursor.getColumnIndexOrThrow(MediaStore.MediaColumns._ID)
            var uebersprungen = 0
            while (cursor.moveToNext()) {
                uebersprungen++
                if (uebersprungen <= MAX_DATEIEN) continue
                val id = cursor.getLong(idSpalte)
                val uri = MediaStore.Downloads.EXTERNAL_CONTENT_URI.buildUpon()
                    .appendPath(id.toString())
                    .build()
                context.contentResolver.delete(uri, null, null)
            }
        }
    }
}
