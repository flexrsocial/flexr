import Foundation

/// Fehler des Backends mit anzeigbarer, deutscher Meldung.
///
/// Entspricht `FlexrApiException` der Android-App und damit derselben Logik wie
/// die `api()`-Funktion im Web-Frontend.
struct FlexrAPIError: Error, LocalizedError, Equatable {
    let statusCode: Int
    let message: String
    /// Bei einer befristeten Chat-Sperre: bis wann sie gilt.
    var mutedUntil: Date?
    /// Begründung der Maßnahme und Widerspruchsweg (Art. 17 DSA).
    var moderationReason: String?
    var appealHint: String?

    var isUnauthorized: Bool { statusCode == 401 }
    var isPaymentRequired: Bool { statusCode == 402 }
    var isMessagingMuted: Bool { mutedUntil != nil }

    var errorDescription: String? { message }
}

/// Übersetzt HTTP- und Transportfehler in [FlexrAPIError].
///
/// `detail` kann beim FastAPI-Backend ein String, eine Pydantic-Fehlerliste
/// oder ein Objekt sein — alle drei Formen werden behandelt.
enum APIErrorParser {

    static func fromResponse(statusCode: Int, body: Data?) -> FlexrAPIError {
        guard
            let body,
            let root = try? JSONSerialization.jsonObject(with: body) as? [String: Any],
            let detail = root["detail"]
        else {
            return FlexrAPIError(statusCode: statusCode, message: defaultMessage(statusCode))
        }

        switch detail {
        case let text as String:
            return FlexrAPIError(statusCode: statusCode, message: text)

        case let issues as [[String: Any]]:
            let joined = issues.compactMap { $0["msg"] as? String }.joined(separator: ", ")
            return FlexrAPIError(
                statusCode: statusCode,
                message: joined.isEmpty ? defaultMessage(statusCode) : joined
            )

        case let object as [String: Any]:
            var mutedUntil: Date?
            if object["reason"] as? String == "messaging_muted" {
                mutedUntil = ServerTime.parse(object["muted_until"] as? String)
            }
            return FlexrAPIError(
                statusCode: statusCode,
                message: (object["message"] as? String) ?? defaultMessage(statusCode),
                mutedUntil: mutedUntil,
                // Sperre und Ban tragen Begründung und Widerspruchshinweis mit.
                moderationReason: object["moderation_reason"] as? String,
                appealHint: object["appeal_hint"] as? String
            )

        default:
            return FlexrAPIError(statusCode: statusCode, message: defaultMessage(statusCode))
        }
    }

    /// Transportfehler (kein Netz, Zeitüberschreitung) und alles Unerwartete.
    static func fromTransport(_ error: Error) -> FlexrAPIError {
        if let apiError = error as? FlexrAPIError { return apiError }

        if let urlError = error as? URLError {
            switch urlError.code {
            case .timedOut:
                return FlexrAPIError(
                    statusCode: 0,
                    message: "Zeitüberschreitung. Bitte Verbindung prüfen und erneut versuchen."
                )
            case .notConnectedToInternet, .dataNotAllowed:
                return FlexrAPIError(statusCode: 0, message: "Keine Internetverbindung.")
            case .cannotFindHost, .cannotConnectToHost, .dnsLookupFailed:
                return FlexrAPIError(statusCode: 0, message: "Server nicht erreichbar.")
            case .cancelled:
                return FlexrAPIError(statusCode: 0, message: "Abgebrochen.")
            default:
                return FlexrAPIError(
                    statusCode: 0,
                    message: "Verbindung fehlgeschlagen. Bitte erneut versuchen."
                )
            }
        }

        if error is DecodingError {
            return FlexrAPIError(statusCode: -1, message: "Unerwartete Antwort des Servers.")
        }

        return FlexrAPIError(statusCode: -1, message: error.localizedDescription)
    }

    static func defaultMessage(_ code: Int) -> String {
        switch code {
        case 401: return "Ungültige oder abgelaufene Anmeldung."
        case 402: return "Probemonat abgelaufen. Bitte Abo abschließen."
        case 403: return "Zugriff nicht möglich."
        case 404: return "Nicht gefunden."
        case 409: return "Bereits vorhanden."
        case 429: return "Zu viele Versuche. Bitte kurz warten."
        case 500...599: return "Serverfehler. Bitte später erneut versuchen."
        default: return "Fehler (\(code))"
        }
    }
}
