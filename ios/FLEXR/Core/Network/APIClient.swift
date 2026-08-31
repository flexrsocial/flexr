import Foundation

enum HTTPMethod: String {
    case get = "GET"
    case post = "POST"
    case patch = "PATCH"
    case put = "PUT"
    case delete = "DELETE"
}

/// HTTP-Zugriff auf das FLEXR-Backend.
///
/// Fasst zusammen, was in der Android-App auf Retrofit und zwei OkHttp-
/// Interceptoren verteilt ist: Basisadresse, JSON-Kodierung, Authentifizierung
/// und die zentrale Behandlung abgelaufener Sitzungen.
final class APIClient: @unchecked Sendable {

    let baseURL: URL
    private let session: URLSession
    private let sessionStore: SessionStore
    /// Nur der eigene Backend-Client meldet 401 als Sitzungsende; für die
    /// öffentliche PLZ-Datenbank wäre das unsinnig.
    private let reportsSessionExpiry: Bool

    private let decoder: JSONDecoder = {
        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        return decoder
    }()

    private let encoder: JSONEncoder = {
        let encoder = JSONEncoder()
        encoder.keyEncodingStrategy = .convertToSnakeCase
        return encoder
    }()

    init(baseURL: URL, sessionStore: SessionStore, reportsSessionExpiry: Bool = true) {
        self.baseURL = baseURL
        self.sessionStore = sessionStore
        self.reportsSessionExpiry = reportsSessionExpiry

        let configuration = URLSessionConfiguration.default
        configuration.timeoutIntervalForRequest = 30
        configuration.timeoutIntervalForResource = 120
        configuration.waitsForConnectivity = false
        configuration.httpAdditionalHeaders = ["Accept": "application/json"]
        session = URLSession(configuration: configuration)
    }

    // MARK: - Anfragen

    @discardableResult
    func send<Response: Decodable>(
        _ method: HTTPMethod,
        _ path: String,
        query: [String: String] = [:],
        body: (any Encodable)? = nil,
        headers: [String: String] = [:],
        as type: Response.Type = Response.self
    ) async throws -> Response {
        let data = try await perform(method, path, query: query, body: body, headers: headers)
        do {
            return try decoder.decode(Response.self, from: data)
        } catch {
            throw APIErrorParser.fromTransport(error)
        }
    }

    /// Für Endpunkte ohne Antwortkörper (`204`/`None`).
    func send(
        _ method: HTTPMethod,
        _ path: String,
        query: [String: String] = [:],
        body: (any Encodable)? = nil,
        headers: [String: String] = [:]
    ) async throws {
        _ = try await perform(method, path, query: query, body: body, headers: headers)
    }

    /// Für Antworten, die auch `null` sein dürfen (z. B. `/api/moderation/notice`).
    func sendOptional<Response: Decodable>(
        _ method: HTTPMethod,
        _ path: String,
        as type: Response.Type
    ) async throws -> Response? {
        let data = try await perform(method, path, query: [:], body: nil, headers: [:])
        guard !data.isEmpty else { return nil }
        do {
            return try decoder.decode(Response?.self, from: data)
        } catch {
            throw APIErrorParser.fromTransport(error)
        }
    }

    /// Lädt eine Bilddatei direkt in den Objekt-Storage (S3/Cloudflare R2).
    ///
    /// Bewusst gegen die absolute Presigned-URL und ohne die eigenen Header:
    /// ein Authorization-Header würde die S3-Signatur ungültig machen.
    func upload(to absoluteURL: String, contentType: String, data: Data) async throws {
        guard let url = URL(string: absoluteURL) else {
            throw FlexrAPIError(statusCode: -1, message: "Ungültige Upload-Adresse.")
        }
        var request = URLRequest(url: url, timeoutInterval: 60)
        request.httpMethod = HTTPMethod.put.rawValue
        request.setValue(contentType, forHTTPHeaderField: "Content-Type")

        do {
            let (responseData, response) = try await session.upload(for: request, from: data)
            guard let http = response as? HTTPURLResponse else { return }
            guard (200..<300).contains(http.statusCode) else {
                throw APIErrorParser.fromResponse(statusCode: http.statusCode, body: responseData)
            }
        } catch {
            throw APIErrorParser.fromTransport(error)
        }
    }

    // MARK: - Innenleben

    private func perform(
        _ method: HTTPMethod,
        _ path: String,
        query: [String: String],
        body: (any Encodable)?,
        headers: [String: String] = [:]
    ) async throws -> Data {
        guard var components = URLComponents(
            url: baseURL.appendingPathComponent(path),
            resolvingAgainstBaseURL: false
        ) else {
            throw FlexrAPIError(statusCode: -1, message: "Ungültige Adresse.")
        }
        if !query.isEmpty {
            components.queryItems = query.map { URLQueryItem(name: $0.key, value: $0.value) }
        }
        guard let url = components.url else {
            throw FlexrAPIError(statusCode: -1, message: "Ungültige Adresse.")
        }

        var request = URLRequest(url: url)
        request.httpMethod = method.rawValue

        // Auth-Header ausschließlich an eigene /api/-Pfade — dieselbe Regel wie
        // der AuthHeaderInterceptor der Android-App.
        if isOwnBackend(path: url.path) {
            if let token = sessionStore.token {
                request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
            }
            request.setValue(sessionStore.deviceID, forHTTPHeaderField: "X-Device-Id")
        }

        // Zusatz-Header je Aufruf - aktuell nur X-Flexr-Background, mit dem der
        // Hintergrundabgleich sich als solcher ausweist (siehe
        // ActivityRefreshService).
        for (name, value) in headers {
            request.setValue(value, forHTTPHeaderField: name)
        }

        if let body {
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
            do {
                request.httpBody = try encoder.encode(AnyEncodable(body))
            } catch {
                throw FlexrAPIError(statusCode: -1, message: "Anfrage konnte nicht erstellt werden.")
            }
        }

        let data: Data
        let response: URLResponse
        do {
            (data, response) = try await session.data(for: request)
        } catch {
            throw APIErrorParser.fromTransport(error)
        }

        guard let http = response as? HTTPURLResponse else { return data }

        if http.statusCode == 401, reportsSessionExpiry, isOwnBackend(path: url.path),
           !url.path.hasPrefix("/api/auth/") {
            // Sitzung ist weg: Token verwerfen und die App zurück auf den Login
            // führen. Entspricht dem 401-Zweig der `api()`-Funktion im Web.
            sessionStore.handleUnauthorized()
        }

        guard (200..<300).contains(http.statusCode) else {
            throw APIErrorParser.fromResponse(statusCode: http.statusCode, body: data)
        }
        return data
    }

    private func isOwnBackend(path: String) -> Bool { path.hasPrefix("/api/") }
}

/// Erlaubt `any Encodable` als Anfragekörper, ohne jeden Aufruf zu generisieren.
private struct AnyEncodable: Encodable {
    private let write: (Encoder) throws -> Void

    init(_ wrapped: any Encodable) {
        write = { encoder in try wrapped.encode(to: encoder) }
    }

    func encode(to encoder: Encoder) throws { try write(encoder) }
}

// MARK: - Basisadresse

enum APIConfiguration {

    /// Aus der Info.plist (`FLEXRAPIBaseURL`, gefüllt aus der Build-Einstellung
    /// `FLEXR_API_BASE_URL`). In Debug-Builds lässt sich das über das
    /// Startargument `-FlexrAPIBaseURL http://localhost:8000/` überschreiben —
    /// das ist die Entsprechung des `local`-Flavors der Android-App.
    static var baseURL: URL {
        #if DEBUG
        if let override = UserDefaults.standard.string(forKey: "FlexrAPIBaseURL"),
           let url = URL(string: override.trimmingCharacters(in: .whitespaces)) {
            return url
        }
        #endif
        if let configured = Bundle.main.object(forInfoDictionaryKey: "FLEXRAPIBaseURL") as? String,
           let url = URL(string: configured), url.scheme != nil {
            return url
        }
        return URL(string: "https://flexr.social/")!
    }
}
