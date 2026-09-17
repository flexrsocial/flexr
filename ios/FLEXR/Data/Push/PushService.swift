import Foundation
import UIKit
import UserNotifications

/// Echte Push-Zustellung über APNs.
///
/// **Warum es das gibt.** Bis zum 17.09.2026 holte sich die App ihre
/// Benachrichtigungen selbst ab (`BGAppRefreshTask`, siehe
/// `MessageRefreshService`). iOS entscheidet dabei selbst, wann — und wann
/// heißt in der Praxis: wenn es zur Nutzungsgewohnheit passt, gern erst
/// Stunden später. Für ein neues Match reicht das, für eine Chatnachricht
/// nicht. Auf Android war derselbe Entwurf der Grund dafür, dass eine
/// Nachricht erst beim manuellen Start der App ankam.
///
/// **Warum direkt an Apple und nicht über Firebase.** Für FCM müsste diese App
/// das Firebase-SDK einbinden. Ein Swift-Package lässt sich nicht so nebenbei
/// ins Xcode-Projekt hängen wie eine Gradle-Zeile, und für den direkten Weg
/// braucht die App kein einziges fremdes Paket — nur die Push-Berechtigung.
/// Dazu kommt, dass so nichts an Google geht, was nicht muss.
///
/// Der Hintergrundabgleich bleibt **zusätzlich** bestehen: als Fallback, wenn
/// jemand die Erlaubnis verweigert oder eine Zustellung verlorengeht.
@MainActor
final class PushService {

    private let api: FlexrAPI
    private let session: SessionStore

    /// Der zuletzt beim Server angemeldete Token. Lokal gemerkt, weil der
    /// Server ihn zum Abmelden braucht — beim Ausloggen ist er von iOS nicht
    /// mehr zuverlässig zu bekommen.
    private var angemeldeterToken: String? {
        get { UserDefaults.standard.string(forKey: Self.speicherSchluessel) }
        set {
            if let newValue {
                UserDefaults.standard.set(newValue, forKey: Self.speicherSchluessel)
            } else {
                UserDefaults.standard.removeObject(forKey: Self.speicherSchluessel)
            }
        }
    }

    init(api: FlexrAPI, session: SessionStore) {
        self.api = api
        self.session = session
    }

    /// Erlaubnis einholen und beim System registrieren.
    ///
    /// Bewusst erst **nach** dem Anmelden und nicht beim ersten Start: Wer die
    /// App gerade zum ersten Mal öffnet, weiß noch gar nicht, wofür er die
    /// Erlaubnis geben soll — und ein abgelehnter Dialog kommt auf iOS kein
    /// zweites Mal.
    func anfordern() async {
        let zentrale = UNUserNotificationCenter.current()
        let erlaubt = (try? await zentrale.requestAuthorization(options: [.alert, .sound, .badge])) ?? false
        guard erlaubt else { return }
        // Muss auf dem Hauptthread laufen; die Klasse ist ohnehin @MainActor.
        UIApplication.shared.registerForRemoteNotifications()
    }

    /// Den von APNs vergebenen Token beim Server anmelden.
    ///
    /// Aufgerufen aus `AppDelegate.didRegisterForRemoteNotifications`. iOS
    /// vergibt den Token neu, wenn die App neu installiert oder wiederher-
    /// gestellt wird — deshalb wird bei **jedem** Start registriert und nicht
    /// nur einmal.
    func anmelden(deviceToken: Data) async {
        let hex = deviceToken.map { String(format: "%02x", $0) }.joined()
        guard session.token != nil else { return }
        do {
            _ = try await api.registerPushToken(platform: "ios", token: hex)
            angemeldeterToken = hex
        } catch {
            // Still: Ohne Push bleibt der Hintergrundabgleich.
        }
    }

    /// Abmelden — beim Ausloggen. Ohne das schickte der Server weiter an ein
    /// Gerät, auf dem dieses Konto niemand mehr benutzt.
    func abmelden() async {
        guard let hex = angemeldeterToken else { return }
        _ = try? await api.unregisterPushToken(platform: "ios", token: hex)
        angemeldeterToken = nil
    }

    private static let speicherSchluessel = "flexr_push_token"
}
