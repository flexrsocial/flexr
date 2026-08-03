import CoreLocation
import Foundation

struct DeviceLocation: Sendable {
    let latitude: Double
    let longitude: Double
}

/// Gerätestandort über CoreLocation.
///
/// Native Entsprechung von `navigator.geolocation` im Web und des Fused
/// Location Providers auf Android, aber mit den iOS-Mechanismen: echte
/// Laufzeitberechtigung, reduzierte Genauigkeit wenn der Nutzer nur den
/// ungefähren Standort freigibt, und ein hartes Zeitlimit, damit der Start des
/// Decks nie am Fix hängt.
@MainActor
final class LocationRepository: NSObject, CLLocationManagerDelegate {

    private let manager = CLLocationManager()
    private var pendingLocation: CheckedContinuation<DeviceLocation?, Never>?
    private var pendingAuthorization: CheckedContinuation<Bool, Never>?

    /// 5 Minuten — für eine Umkreissuche in km völlig ausreichend.
    private static let maxLocationAge: TimeInterval = 300
    private static let locationTimeout: Duration = .seconds(6)

    override init() {
        super.init()
        manager.delegate = self
        // Kilometergenau reicht; alles Feinere kostet nur Akku.
        manager.desiredAccuracy = kCLLocationAccuracyKilometer
    }

    var authorizationStatus: CLAuthorizationStatus { manager.authorizationStatus }

    var hasPermission: Bool {
        switch manager.authorizationStatus {
        case .authorizedAlways, .authorizedWhenInUse: true
        default: false
        }
    }

    var isUndetermined: Bool { manager.authorizationStatus == .notDetermined }

    /// Berechtigung im Kontext erfragen: erst beim Öffnen des Decks ist
    /// erkennbar, wofür sie gebraucht wird (Umkreissuche).
    @discardableResult
    func requestPermission() async -> Bool {
        guard isUndetermined else { return hasPermission }
        return await withCheckedContinuation { continuation in
            pendingAuthorization = continuation
            manager.requestWhenInUseAuthorization()
        }
    }

    /// Aktuelle Position oder nil (keine Berechtigung, kein Fix, Zeitlimit).
    /// Zuerst wird die zuletzt bekannte Position versucht — die liegt meist
    /// sofort vor und reicht für eine Umkreissuche in Kilometern völlig aus.
    func currentLocation() async -> DeviceLocation? {
        guard hasPermission else { return nil }

        if let cached = manager.location,
           Date().timeIntervalSince(cached.timestamp) < Self.maxLocationAge {
            return DeviceLocation(
                latitude: cached.coordinate.latitude,
                longitude: cached.coordinate.longitude
            )
        }

        // Es läuft bereits eine Abfrage — nicht zwei parallel starten.
        guard pendingLocation == nil else { return nil }

        return await withTaskGroup(of: DeviceLocation?.self) { group in
            group.addTask { @MainActor in
                await withCheckedContinuation { continuation in
                    self.pendingLocation = continuation
                    self.manager.requestLocation()
                }
            }
            // Zeitlimit: kommt kein Fix, wird die wartende Fortsetzung selbst
            // mit nil beendet — sonst bliebe sie für immer hängen und jede
            // weitere Abfrage liefe ins Leere.
            group.addTask { @MainActor in
                try? await Task.sleep(for: Self.locationTimeout)
                self.finishLocation(with: nil)
                return nil
            }
            let first = await group.next() ?? nil
            group.cancelAll()
            return first
        }
    }

    // MARK: - CLLocationManagerDelegate

    nonisolated func locationManager(
        _ manager: CLLocationManager,
        didUpdateLocations locations: [CLLocation]
    ) {
        let location = locations.last.map {
            DeviceLocation(latitude: $0.coordinate.latitude, longitude: $0.coordinate.longitude)
        }
        Task { @MainActor in self.finishLocation(with: location) }
    }

    nonisolated func locationManager(_ manager: CLLocationManager, didFailWithError error: Error) {
        Task { @MainActor in self.finishLocation(with: nil) }
    }

    nonisolated func locationManagerDidChangeAuthorization(_ manager: CLLocationManager) {
        Task { @MainActor in
            guard manager.authorizationStatus != .notDetermined else { return }
            self.pendingAuthorization?.resume(returning: self.hasPermission)
            self.pendingAuthorization = nil
        }
    }

    private func finishLocation(with location: DeviceLocation?) {
        pendingLocation?.resume(returning: location)
        pendingLocation = nil
    }
}
