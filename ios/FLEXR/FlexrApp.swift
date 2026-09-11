import BackgroundTasks
import SwiftUI
import UserNotifications

@main
struct FlexrApp: App {

    @UIApplicationDelegateAdaptor(AppDelegate.self) private var appDelegate

    var body: some Scene {
        WindowGroup {
            RootView()
                .environment(appDelegate.container)
                .environment(appDelegate.appModel)
                // Sprachwahl umhuellt alles, was Texte zeigt: jede View liest
                // ihre Texte ueber `languageStore.strings`, ein Wechsel
                // zeichnet die Oberflaeche also von selbst neu.
                .environment(appDelegate.languageStore)
                .preferredColorScheme(.dark)
                .tint(FlexrColor.plate)
        }
    }
}

/// Startpunkt jenseits von SwiftUI.
///
/// `BGTaskScheduler.register` muss vor dem Ende von
/// `didFinishLaunchingWithOptions` laufen — dafür braucht es einen
/// App-Delegierten, ein `.task`-Modifier auf einer View wäre zu spät.
@MainActor
final class AppDelegate: NSObject, UIApplicationDelegate, UNUserNotificationCenterDelegate {

    let container = AppContainer()
    let languageStore = LanguageStore()
    lazy var appModel = AppModel(container: container, languageStore: languageStore)

    func application(
        _ application: UIApplication,
        didFinishLaunchingWithOptions options: [UIApplication.LaunchOptionsKey: Any]? = nil
    ) -> Bool {
        UNUserNotificationCenter.current().delegate = self
        // Anlegen genügt: der Speicher setzt `APIErrorParser.strings` selbst,
        // beim Start wie bei jedem späteren Sprachwechsel.
        _ = languageStore

        // Jede Wahl am Regler ans Profil melden. Der Speicher kennt weder
        // Netzwerk noch Repositories — deshalb wird der Weg hier geknüpft, wo
        // beide Seiten bekannt sind. Ohne die Meldung schriebe der Server
        // seine E-Mails weiter in der alten Sprache: Sie entstehen zum Teil
        // ohne die App (Tagesjob, Stripe-Webhook, Moderation).
        languageStore.onChange = { [weak self] language in
            guard let self else { return }
            Task { await self.container.profiles.reportLanguage(language.rawValue) }
        }

        // Bewusst auf der Hauptwarteschlange: der Abgleich läuft über die
        // MainActor-isolierten Repositories. Mit `nil` liefe der Handler auf
        // einer Hintergrundwarteschlange.
        BGTaskScheduler.shared.register(
            forTaskWithIdentifier: MessageRefreshService.taskIdentifier,
            using: .main
        ) { [weak self] task in
            guard let refreshTask = task as? BGAppRefreshTask else {
                task.setTaskCompleted(success: false)
                return
            }
            MainActor.assumeIsolated {
                self?.container.notifications.handle(refreshTask)
            }
        }
        // Zweiter Auftrag für Match, wartende Profile und Inaktivität - iOS
        // verlangt je Kennung eine eigene Registrierung.
        BGTaskScheduler.shared.register(
            forTaskWithIdentifier: ActivityRefreshService.taskIdentifier,
            using: .main
        ) { [weak self] task in
            guard let refreshTask = task as? BGAppRefreshTask else {
                task.setTaskCompleted(success: false)
                return
            }
            MainActor.assumeIsolated {
                self?.container.activityNotifications.handle(refreshTask)
            }
        }
        return true
    }

    /// Benachrichtigung bei geöffneter App: dezent anzeigen statt verschlucken.
    func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        willPresent notification: UNNotification
    ) async -> UNNotificationPresentationOptions {
        [.banner, .sound]
    }

    /// Tipp auf die Benachrichtigung führt in die Chatliste.
    func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        didReceive response: UNNotificationResponse
    ) async {
        // Jede Benachrichtigungsart bringt ihren eigenen Schlüssel mit:
        // ActivityRefreshService setzt "target" (matches/swipe),
        // MessageRefreshService "openChats". Bislang landete jeder Tipp
        // unabhängig davon in der Chatliste.
        let info = response.notification.request.content.userInfo
        if let target = info["target"] as? String, !target.isEmpty {
            appModel.open(target: target)
        } else if info["openChats"] as? Bool == true {
            appModel.openChatsTab()
        }
    }
}
