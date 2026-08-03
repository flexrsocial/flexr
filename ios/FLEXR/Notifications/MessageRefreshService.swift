import BackgroundTasks
import Foundation
import UserNotifications

/// Hintergrundabgleich für neue Nachrichten.
///
/// Die Web-App konnte nur pollen, solange der Tab offen war; Android übernimmt
/// das mit WorkManager. Auf iOS ist die Entsprechung `BGAppRefreshTask`: das
/// System entscheidet, wann die App laufen darf, und lernt das aus dem
/// Nutzungsverhalten. Ein festes Intervall wie die 15 Minuten auf Android gibt
/// es hier nicht — `earliestBeginDate` ist eine Untergrenze, keine Zusage.
///
/// Bei neuen ungelesenen Nachrichten erscheint eine lokale Benachrichtigung.
/// Der lokale Bestand ist dadurch beim Öffnen der App bereits aktuell.
@MainActor
final class MessageRefreshService {

    static let taskIdentifier = "social.flexr.app.messages.refresh"
    private static let notificationIdentifier = "flexr.messages"
    private static let minimumInterval: TimeInterval = 15 * 60

    private let session: SessionStore
    private let matches: MatchRepository

    init(session: SessionStore, matches: MatchRepository) {
        self.session = session
        self.matches = matches
    }

    // MARK: - Planung
    //
    // Die Registrierung selbst liegt im AppDelegate — sie muss vor dem Ende von
    // didFinishLaunchingWithOptions laufen, sonst weist BGTaskScheduler sie zurück.

    func schedule() {
        guard session.isLoggedInNow, session.notificationsEnabled else { return }
        let request = BGAppRefreshTaskRequest(identifier: Self.taskIdentifier)
        request.earliestBeginDate = Date(timeIntervalSinceNow: Self.minimumInterval)
        try? BGTaskScheduler.shared.submit(request)
    }

    func cancel() {
        BGTaskScheduler.shared.cancel(taskRequestWithIdentifier: Self.taskIdentifier)
        UNUserNotificationCenter.current()
            .removeDeliveredNotifications(withIdentifiers: [Self.notificationIdentifier])
    }

    /// Berechtigung erst beim Einschalten im Konto erfragen, wo der Zweck
    /// offensichtlich ist.
    func requestNotificationPermission() async -> Bool {
        let center = UNUserNotificationCenter.current()
        let granted = (try? await center.requestAuthorization(options: [.alert, .sound, .badge])) ?? false
        return granted
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
        guard session.notificationsEnabled else { return true }

        guard let refreshed = try? await matches.refresh() else { return false }

        let unread = refreshed.filter { $0.unreadCount > 0 }
        guard !unread.isEmpty else {
            UNUserNotificationCenter.current()
                .removeDeliveredNotifications(withIdentifiers: [Self.notificationIdentifier])
            await setBadge(0)
            return true
        }

        let total = unread.reduce(0) { $0 + $1.unreadCount }
        await setBadge(total)

        // Nur bei wirklich neuen Nachrichten benachrichtigen — sonst würde jeder
        // Durchlauf dieselbe ungelesene Nachricht erneut melden.
        let newest = unread.compactMap(\.lastMessage).max { $0.createdAt < $1.createdAt }
        guard let newest, session.lastNotifiedMessageID != newest.id else { return true }
        session.lastNotifiedMessageID = newest.id

        await notify(
            senderNames: unread.map(\.profile.name),
            totalUnread: total,
            preview: newest.content
        )
        return true
    }

    private func notify(senderNames: [String], totalUnread: Int, preview: String) async {
        let center = UNUserNotificationCenter.current()
        let settings = await center.notificationSettings()
        guard settings.authorizationStatus == .authorized
            || settings.authorizationStatus == .provisional
        else { return }

        let content = UNMutableNotificationContent()
        content.title = senderNames.count == 1
            ? "Neue Nachricht von \(senderNames[0])"
            : "\(totalUnread) neue Nachrichten"
        content.body = senderNames.count == 1
            ? preview
            : Array(Set(senderNames)).sorted().joined(separator: ", ")
        content.sound = .default
        content.userInfo = ["openChats": true]

        let request = UNNotificationRequest(
            identifier: Self.notificationIdentifier,
            content: content,
            trigger: nil
        )
        try? await center.add(request)
    }

    private func setBadge(_ count: Int) async {
        try? await UNUserNotificationCenter.current().setBadgeCount(count)
    }
}
