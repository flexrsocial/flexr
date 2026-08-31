import Foundation

/// Abholfach für die vom Server bereitgelegten App-Benachrichtigungen.
///
/// FLEXR nutzt kein APNs — neues Match, wartende Profile und die
/// Inaktivitäts-Erinnerung kommen über denselben Hintergrundabgleich, mit dem
/// ``MessageRefreshService`` schon neue Nachrichten meldet. Ob ein Anlass
/// überhaupt im Fach landet, entscheidet der Server anhand der Schalter unter
/// „Benachrichtigungen"; die App zeigt nur an, was ihr gereicht wird.
@MainActor
final class NotificationRepository {

    private let api: FlexrAPI

    init(api: FlexrAPI) {
        self.api = api
    }

    func pending() async throws -> [PushNotification] {
        try await api.pendingNotifications().map { $0.toDomain() }
    }

    /// Quittiert erst nach dem Anzeigen, nicht beim Abholen: bricht der
    /// Hintergrundlauf dazwischen ab, kommt die Nachricht im nächsten Durchgang
    /// erneut — besser doppelt als verschluckt.
    func markDelivered(_ ids: [String]) async throws {
        guard !ids.isEmpty else { return }
        try await api.markNotificationsDelivered(MarkDeliveredRequestDTO(ids: ids))
    }
}
