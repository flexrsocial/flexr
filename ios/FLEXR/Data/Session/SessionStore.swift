import Combine
import Foundation

/// Sitzungszustand der App: JWT, stabile Geräte-ID und Nutzereinstellungen.
///
/// Ersetzt den `localStorage` der Web-App und entspricht dem `SessionStore` der
/// Android-Fassung. Der Token liegt im Keychain, alles Übrige in den
/// `UserDefaults` — dort, wo es hingehört und wo es beim Löschen der App
/// verschwindet.
///
/// Alle Zugriffe sind über ein Lock abgesichert: Die Header-Erzeugung im
/// Netzwerk-Client läuft nicht auf dem Hauptthread.
final class SessionStore: @unchecked Sendable {

    private enum Keys {
        static let token = "access_token"
        static let deviceID = "device_id"
        static let userID = "user_id"
        static let notificationsEnabled = "notifications_enabled"
        static let lastNotifiedMessage = "last_notified_message_id"
        static let verifiedHintDismissed = "verified_hint_dismissed"
        static let keychainSeeded = "keychain_seeded"
    }

    private let defaults: UserDefaults
    private let lock = NSLock()

    private let loggedInSubject: CurrentValueSubject<Bool, Never>

    /// Feuert, sobald das Backend eine Anmeldung als abgelaufen zurückweist (401).
    private let expiredSubject = PassthroughSubject<Void, Never>()

    var isLoggedIn: AnyPublisher<Bool, Never> { loggedInSubject.removeDuplicates().eraseToAnyPublisher() }
    var sessionExpired: AnyPublisher<Void, Never> { expiredSubject.eraseToAnyPublisher() }
    var isLoggedInNow: Bool { loggedInSubject.value }

    init(defaults: UserDefaults = .standard) {
        self.defaults = defaults
        // Der Keychain überlebt das Löschen der App, die UserDefaults nicht.
        // Ohne diesen Abgleich wäre man nach einer Neuinstallation noch
        // angemeldet, während Geräte-ID und Einstellungen weg sind.
        if !defaults.bool(forKey: Keys.keychainSeeded) {
            Keychain.remove(Keys.token)
            defaults.set(true, forKey: Keys.keychainSeeded)
        }
        loggedInSubject = CurrentValueSubject(Keychain.string(for: Keys.token)?.isEmpty == false)
    }

    // MARK: - Token

    var token: String? {
        lock.lock()
        defer { lock.unlock() }
        return Keychain.string(for: Keys.token)
    }

    func save(token: String) {
        lock.lock()
        Keychain.set(token, for: Keys.token)
        lock.unlock()
        loggedInSubject.send(true)
    }

    // MARK: - Nutzer

    var userID: String? {
        get {
            lock.lock()
            defer { lock.unlock() }
            return defaults.string(forKey: Keys.userID)
        }
        set {
            lock.lock()
            defaults.set(newValue, forKey: Keys.userID)
            lock.unlock()
        }
    }

    /// Abmelden. Die Geräte-ID bleibt bewusst erhalten: sie ist an das Gerät
    /// gebunden (Mehrfachkonto-Erkennung / Ban-Evasion-Schutz im Backend) und
    /// darf sich durch ein simples Ausloggen nicht ändern.
    func clear() {
        lock.lock()
        Keychain.remove(Keys.token)
        defaults.removeObject(forKey: Keys.userID)
        defaults.removeObject(forKey: Keys.lastNotifiedMessage)
        // Bestätigter Hinweis gilt pro Konto — beim Abmelden zurücksetzen.
        defaults.removeObject(forKey: Keys.verifiedHintDismissed)
        lock.unlock()
        loggedInSubject.send(false)
    }

    /// Vom Netzwerk-Client bei einem 401 aufgerufen.
    func handleUnauthorized() {
        clear()
        expiredSubject.send(())
    }

    // MARK: - Einstellungen

    var notificationsEnabled: Bool {
        get {
            lock.lock()
            defer { lock.unlock() }
            return defaults.object(forKey: Keys.notificationsEnabled) as? Bool ?? true
        }
        set {
            lock.lock()
            defaults.set(newValue, forKey: Keys.notificationsEnabled)
            lock.unlock()
        }
    }

    /// Ob der Hinweis „Dein Profil ist verifiziert" bereits bestätigt wurde.
    var verifiedHintDismissed: Bool {
        get {
            lock.lock()
            defer { lock.unlock() }
            return defaults.bool(forKey: Keys.verifiedHintDismissed)
        }
        set {
            lock.lock()
            defaults.set(newValue, forKey: Keys.verifiedHintDismissed)
            lock.unlock()
        }
    }

    var lastNotifiedMessageID: String? {
        get {
            lock.lock()
            defer { lock.unlock() }
            return defaults.string(forKey: Keys.lastNotifiedMessage)
        }
        set {
            lock.lock()
            defaults.set(newValue, forKey: Keys.lastNotifiedMessage)
            lock.unlock()
        }
    }

    // MARK: - Geräte-ID

    /// Stabile, zufällige Geräte-ID — entspricht `flexr_device_id` im Web und
    /// erfüllt das vom Backend erwartete Format `^[A-Za-z0-9-]{8,64}$`.
    ///
    /// Bewusst keine Hardware-Kennung (`identifierForVendor` o. Ä.): die ID ist
    /// nicht geräteübergreifend rückverfolgbar und verschwindet mit der App.
    var deviceID: String {
        lock.lock()
        defer { lock.unlock() }
        if let existing = defaults.string(forKey: Keys.deviceID), !existing.isEmpty {
            return existing
        }
        let generated = UUID().uuidString
        defaults.set(generated, forKey: Keys.deviceID)
        return generated
    }
}
