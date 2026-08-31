import BackgroundTasks
import Foundation
import UserNotifications

/// Hintergrundabgleich für die Aktivitäts-Benachrichtigungen: neues Match,
/// wartende Profile im Suchradius und die Erinnerung nach sieben Tagen ohne
/// Nutzung.
///
/// Kein APNs — aus demselben Grund wie bei ``MessageRefreshService``: FLEXR
/// braucht dafür keinen Push-Dienst, und diese Anlässe vertragen die
/// Verzögerung, die `BGAppRefreshTask` mit sich bringt. Das System entscheidet,
/// wann die App laufen darf; `earliestBeginDate` ist eine Untergrenze, keine
/// Zusage.
///
/// Welche Anlässe überhaupt ankommen, entscheidet der Server anhand der
/// notify_*_push-Schalter. Die App fragt das nicht noch einmal ab: eine zweite
/// Regel hier liefe bei jeder Änderung auseinander und wäre erst nach dem
/// nächsten App-Update wirksam.
@MainActor
final class ActivityRefreshService {

    static let taskIdentifier = "social.flexr.app.activity.refresh"
    /// Match und Erinnerung vertragen eine Stunde Verzug, ein Chat nicht —
    /// deshalb seltener als der Nachrichtenabgleich.
    private static let minimumInterval: TimeInterval = 60 * 60

    private let session: SessionStore
    private let notifications: NotificationRepository

    init(session: SessionStore, notifications: NotificationRepository) {
        self.session = session
        self.notifications = notifications
    }

    // MARK: - Planung

    func schedule() {
        guard session.isLoggedInNow, session.notificationsEnabled else { return }
        let request = BGAppRefreshTaskRequest(identifier: Self.taskIdentifier)
        request.earliestBeginDate = Date(timeIntervalSinceNow: Self.minimumInterval)
        try? BGTaskScheduler.shared.submit(request)
    }

    func cancel() {
        BGTaskScheduler.shared.cancel(taskRequestWithIdentifier: Self.taskIdentifier)
    }

    // MARK: - Durchlauf

    func handle(_ task: BGAppRefreshTask) {
        // Der nächste Lauf wird sofort angemeldet: iOS plant immer nur einen.
        schedule()

        let work = Task { @MainActor in
            let success = await run()
            task.setTaskCompleted(success: success)
        }
        task.expirationHandler = { work.cancel() }
    }

    /// Liefert `false`, wenn der Abgleich am Netz gescheitert ist.
    @discardableResult
    func run() async -> Bool {
        guard session.token?.isEmpty == false else { return true }
        // Derselbe App-weite Schalter wie beim Nachrichtenabgleich — er steht
        // über den serverseitigen Einstellungen.
        guard session.notificationsEnabled else { return true }

        guard let offen = try? await notifications.pending() else { return false }
        guard !offen.isEmpty else { return true }

        var angezeigt: [String] = []
        for eintrag in offen where await show(eintrag) {
            angezeigt.append(eintrag.id)
        }

        // Nur Angezeigtes gilt als zugestellt: fehlt die Systemberechtigung,
        // bleibt der Eintrag liegen und wird nachgeholt, sobald der Nutzer sie
        // erteilt — statt ungesehen zu verfallen.
        guard (try? await notifications.markDelivered(angezeigt)) != nil else { return false }
        return true
    }

    private func show(_ notification: PushNotification) async -> Bool {
        let center = UNUserNotificationCenter.current()
        let settings = await center.notificationSettings()
        guard settings.authorizationStatus == .authorized
            || settings.authorizationStatus == .provisional
        else { return false }

        let content = UNMutableNotificationContent()
        content.title = notification.title
        content.body = notification.body
        content.sound = .default
        content.userInfo = ["target": notification.target ?? ""]

        // Server-ID als Kennung: derselbe Anlass ersetzt seine eigene Meldung,
        // verdrängt aber keine fremde.
        let request = UNNotificationRequest(
            identifier: "flexr.activity.\(notification.id)",
            content: content,
            trigger: nil
        )
        try? await center.add(request)
        return true
    }
}
