import CryptoKit
import Foundation
import UIKit

/// Bildspeicher für Profilfotos.
///
/// Profilfotos sind der Inhalt dieser App — sie dürfen nicht bei jedem Anzeigen
/// neu aus dem Netz kommen. `AsyncImage` aus SwiftUI hält nichts auf der Platte
/// und richtet sich ansonsten nach den HTTP-Cache-Headern; fehlen die (R2
/// lieferte lange gar keine), ist praktisch jede Anzeige ein Roundtrip und ein
/// Empfangsloch lässt die Bilder schlicht verschwinden.
///
/// Deshalb ein eigener Speicher, der die Header bewusst ignoriert — genau wie
/// der Coil-Loader der Android-App mit `respectCacheHeaders(false)`. Die
/// Objektschlüssel sind UUIDs und werden nie überschrieben: ein einmal
/// geladenes Bild bleibt gültig.
actor ImageStore {

    static let shared = ImageStore()

    private let memory: NSCache<NSString, UIImage> = {
        let cache = NSCache<NSString, UIImage>()
        cache.totalCostLimit = 96 * 1024 * 1024
        return cache
    }()

    private let directory: URL
    private let session: URLSession
    /// Mehrfach angeforderte Bilder teilen sich einen Ladevorgang.
    private var inFlight: [String: Task<UIImage?, Never>] = [:]

    private static let diskLimitBytes = 150 * 1024 * 1024

    init() {
        let caches = FileManager.default.urls(for: .cachesDirectory, in: .userDomainMask)[0]
        directory = caches.appendingPathComponent("bilder", isDirectory: true)
        try? FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)

        let configuration = URLSessionConfiguration.default
        configuration.requestCachePolicy = .reloadIgnoringLocalCacheData
        configuration.urlCache = nil
        configuration.timeoutIntervalForRequest = 30
        session = URLSession(configuration: configuration)
    }

    func image(for urlString: String) async -> UIImage? {
        let key = Self.key(for: urlString)

        if let cached = memory.object(forKey: key as NSString) { return cached }

        if let data = try? Data(contentsOf: fileURL(key)), let image = UIImage(data: data) {
            memory.setObject(image, forKey: key as NSString, cost: data.count)
            return image
        }

        if let running = inFlight[key] { return await running.value }

        let task = Task<UIImage?, Never> { [session] in
            guard let url = URL(string: urlString) else { return nil }
            guard let (data, response) = try? await session.data(from: url) else { return nil }
            if let http = response as? HTTPURLResponse, !(200..<300).contains(http.statusCode) {
                return nil
            }
            guard let image = UIImage(data: data) else { return nil }
            self.persist(data, key: key)
            return image
        }
        inFlight[key] = task
        let image = await task.value
        inFlight[key] = nil

        if let image {
            memory.setObject(image, forKey: key as NSString, cost: Self.cost(of: image))
        }
        return image
    }

    /// Wird beim Abmelden geleert — die Fotos gehören zum abgemeldeten Konto.
    func clear() {
        memory.removeAllObjects()
        try? FileManager.default.removeItem(at: directory)
        try? FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
    }

    // MARK: - Platte

    private nonisolated func persist(_ data: Data, key: String) {
        try? data.write(to: fileURL(key), options: .atomic)
        Task.detached(priority: .utility) { [directory] in
            Self.trim(directory: directory)
        }
    }

    private nonisolated func fileURL(_ key: String) -> URL {
        directory.appendingPathComponent(key)
    }

    /// Grob der belegte Bildspeicher — genauer muss es für ein Cache-Limit nicht sein.
    private nonisolated static func cost(of image: UIImage) -> Int {
        Int(image.size.width * image.scale * image.size.height * image.scale * 4)
    }

    private nonisolated static func key(for urlString: String) -> String {
        let digest = SHA256.hash(data: Data(urlString.utf8))
        return digest.map { String(format: "%02x", $0) }.joined()
    }

    /// Ältestes zuerst wegwerfen, sobald das Verzeichnis über der Grenze liegt.
    private static func trim(directory: URL) {
        let keys: [URLResourceKey] = [.contentAccessDateKey, .fileSizeKey]
        guard let files = try? FileManager.default.contentsOfDirectory(
            at: directory,
            includingPropertiesForKeys: keys
        ) else { return }

        let entries = files.compactMap { url -> (URL, Date, Int)? in
            guard let values = try? url.resourceValues(forKeys: Set(keys)),
                  let size = values.fileSize
            else { return nil }
            return (url, values.contentAccessDate ?? .distantPast, size)
        }

        var total = entries.reduce(0) { $0 + $1.2 }
        guard total > diskLimitBytes else { return }

        for entry in entries.sorted(by: { $0.1 < $1.1 }) {
            try? FileManager.default.removeItem(at: entry.0)
            total -= entry.2
            if total <= diskLimitBytes { break }
        }
    }
}
