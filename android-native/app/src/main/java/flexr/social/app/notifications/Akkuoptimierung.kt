package flexr.social.app.notifications

import android.content.ActivityNotFoundException
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.PowerManager
import android.provider.Settings

/**
 * Ob Android diese App schlafen legen darf, sobald sie niemand mehr im
 * Vordergrund hat — und der Weg zu der Einstellung, die das abstellt.
 *
 * **Warum das hier steht.** Gemeldet am 18.09.2026: Solange die App im
 * Hintergrund geöffnet blieb, kamen Chat-Benachrichtigungen sofort an; war sie
 * aus der Übersicht gewischt, kam gar keine. Am Server liegt das nicht — der
 * schickt in beiden Fällen dieselbe Nachricht mit `priority: high`
 * (`backend/app/push.py`), und Firebase nimmt sie in beiden Fällen an.
 *
 * Der Unterschied entsteht auf dem Gerät: Ist der Prozess weg, muss Android ihn
 * für die Zustellung **neu starten**. Genau das verweigern die
 * Akku-Optimierung und, deutlich schärfer, die Herstellerzusätze darüber
 * (Samsungs „Apps im Ruhemodus", Xiaomis Autostart-Sperre): Die App bleibt im
 * Ruhezustand, und ihre Benachrichtigungen kommen erst, wenn sie jemand von
 * Hand öffnet. Kein Code in der App kann das umgehen — es ist eine
 * Entscheidung des Systems über die App, nicht in ihr.
 *
 * Was die App tun kann, ist genau zweierlei: nachsehen, ob die Ausnahme
 * gesetzt ist, und den Nutzer an die Stelle führen, an der er sie setzen kann.
 * Beides steht hier.
 *
 * Bewusst **nicht** über [Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS]
 * (der Einzeldialog „Zulassen?"): Der verlangt die Berechtigung
 * `REQUEST_IGNORE_BATTERY_OPTIMIZATIONS`, und Google lässt die nur für einen
 * kurzen Katalog von Anwendungsfällen zu (Alarme, Anrufe, Gerätesteuerung) —
 * eine Dating-App gehört nicht dazu, und die Play-Prüfung wirft sie zurück.
 * Der Weg über die Einstellungsliste braucht keine Berechtigung.
 */
object Akkuoptimierung {

    /**
     * Ist FLEXR von der Akku-Optimierung ausgenommen?
     *
     * Im Zweifel `true`: Die Antwort steuert nur einen Hinweis. Lieber keinen
     * Hinweis als einen, der auf einem Gerät ohne [PowerManager] dauerhaft
     * etwas behauptet, das sich dort gar nicht prüfen lässt.
     */
    fun istAusgenommen(context: Context): Boolean {
        val manager = context.getSystemService(PowerManager::class.java) ?: return true
        return runCatching { manager.isIgnoringBatteryOptimizations(context.packageName) }
            .getOrDefault(true)
    }

    /**
     * Der Weg zur Einstellung, als Liste von Versuchen.
     *
     * Erste Wahl ist die Systemliste „Akku-Optimierung" — dort steht die App
     * mit genau dem einen Schalter, um den es geht. Fehlt diese Ansicht auf
     * einem Gerät (Hersteller dürfen sie ersetzen), bleibt die Detailseite der
     * App: von dort sind es zwei Tipper mehr, aber sie gibt es überall.
     *
     * Geprüft wird durch Ausprobieren und nicht mit `resolveActivity`: Seit
     * Android 11 filtert die Paketsichtbarkeit auch die Auflösung von Intents,
     * eine Absage von dort hiesse also nicht zwingend, dass es die Ansicht
     * nicht gibt.
     */
    fun oeffneEinstellungen(context: Context) {
        val versuche = listOf(
            Intent(Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS),
            Intent(
                Settings.ACTION_APPLICATION_DETAILS_SETTINGS,
                Uri.fromParts("package", context.packageName, null),
            ),
        )
        for (intent in versuche) {
            try {
                context.startActivity(intent)
                return
            } catch (_: ActivityNotFoundException) {
                // nächster Versuch
            }
        }
    }
}
