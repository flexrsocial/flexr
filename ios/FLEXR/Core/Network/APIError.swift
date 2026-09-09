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
    /// Strukturiertes Detail-Objekt des Backends, z. B. „account_deleted" bei
    /// einem Login innerhalb der 30-Tage-Karenzzeit (siehe routers/auth.py).
    var code: String?

    var isUnauthorized: Bool { statusCode == 401 }
    var isPaymentRequired: Bool { statusCode == 402 }
    var isMessagingMuted: Bool { mutedUntil != nil }
    var isAccountDeleted: Bool { code == "account_deleted" }

    var errorDescription: String? { message }
}

/// Übersetzt HTTP- und Transportfehler in [FlexrAPIError].
///
/// `detail` kann beim FastAPI-Backend ein String, eine Pydantic-Fehlerliste
/// oder ein Objekt sein — alle drei Formen werden behandelt.
enum APIErrorParser {

    /// Texte der Standardmeldungen — siehe [FlexrStrings.current].
    private static var strings: FlexrStrings { FlexrStrings.current }

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
                appealHint: object["appeal_hint"] as? String,
                code: object["code"] as? String
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
                    message: strings(.errorTimeout)
                )
            case .notConnectedToInternet, .dataNotAllowed:
                return FlexrAPIError(statusCode: 0, message: strings(.errorNoInternet))
            case .cannotFindHost, .cannotConnectToHost, .dnsLookupFailed:
                return FlexrAPIError(statusCode: 0, message: strings(.errorUnreachable))
            case .cancelled:
                return FlexrAPIError(statusCode: 0, message: strings(.errorCancelled))
            default:
                return FlexrAPIError(
                    statusCode: 0,
                    message: strings(.errorConnection)
                )
            }
        }

        if error is DecodingError {
            return FlexrAPIError(statusCode: -1, message: strings(.errorUnexpectedResponse))
        }

        return FlexrAPIError(statusCode: -1, message: error.localizedDescription)
    }

    static func defaultMessage(_ code: Int) -> String {
        switch code {
        case 401: return strings(.errorUnauthorized)
        case 402: return strings(.errorPaymentRequired)
        case 403: return strings(.errorForbidden)
        case 404: return strings(.errorNotFound)
        case 409: return strings(.errorConflict)
        case 429: return strings(.errorRateLimited)
        case 500...599: return strings(.errorServer)
        default: return strings(.errorHttp, code)
        }
    }
}
