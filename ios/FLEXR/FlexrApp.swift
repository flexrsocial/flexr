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
    lazy var appModel = AppModel(container: container)

    func application(
        _ application: UIApplication,
        didFinishLaunchingWithOptions options: [UIApplication.LaunchOptionsKey: Any]? = nil
    ) -> Bool {
        UNUserNotificationCenter.current().delegate = self

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
        appModel.openChatsTab()
    }
}
