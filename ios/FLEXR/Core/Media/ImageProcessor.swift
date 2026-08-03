import CoreGraphics
import Foundation
import ImageIO
import UIKit
import UniformTypeIdentifiers

/// Fertig aufbereitetes Foto: Vollbild plus quadratisches Thumbnail.
struct PreparedPhoto: Equatable, Sendable {
    let full: Data
    let thumbnail: Data
    var mimeType: String = "image/jpeg"
}

struct PhotoTooSmallError: LocalizedError {
    let width: Int
    let height: Int

    var errorDescription: String? {
        "Foto zu klein (\(width)×\(height)). Mindestens "
            + "\(ImageProcessor.minEdgePx)×\(ImageProcessor.minEdgePx) Pixel."
    }
}

struct PhotoUnreadableError: LocalizedError {
    var errorDescription: String? { "Foto konnte nicht geladen werden." }
}

/// Bildaufbereitung vor dem Upload — die native Entsprechung der
/// Canvas-Verarbeitung im Web (`preparePhoto`) und des `ImageProcessor` der
/// Android-App:
///
/// - Mindestauflösung 600 px je Seite, sonst wirken Fotos auf den Karten pixelig
/// - Vollbild auf max. 1080 px lange Kante herunterskaliert, JPEG-Qualität 85
/// - quadratisches 256-px-Thumbnail (mittiger Cover-Crop) für kleine Avatare
/// - EXIF-Drehung wird angewandt, damit Hochformat-Aufnahmen nicht liegen
///
/// Läuft vollständig abseits des Hauptthreads.
enum ImageProcessor {

    static let minEdgePx = 600
    static let maxEdgePx = 1080
    static let thumbPx = 256
    static let selfieMaxEdgePx = 1280
    static let jpegQuality: CGFloat = 0.85
    static let maxPhotos = 6

    /// Aus den Rohdaten einer Bilddatei (Fotoauswahl).
    static func prepare(data: Data) async throws -> PreparedPhoto {
        try await run {
            guard let source = CGImageSourceCreateWithData(data as CFData, nil) else {
                throw PhotoUnreadableError()
            }
            let (pixelWidth, pixelHeight) = pixelSize(of: source)
            guard min(pixelWidth, pixelHeight) >= minEdgePx else {
                throw PhotoTooSmallError(width: pixelWidth, height: pixelHeight)
            }
            // ImageIO liefert das Bild bereits gedreht und heruntergerechnet;
            // das spart den Umweg über ein Vollbild in voller Auflösung.
            guard let full = thumbnail(from: source, maxEdge: maxEdgePx) else {
                throw PhotoUnreadableError()
            }
            guard
                let fullData = jpeg(full),
                let thumbData = jpeg(centerSquare(full, size: thumbPx))
            else { throw PhotoUnreadableError() }

            return PreparedPhoto(full: fullData, thumbnail: thumbData)
        }
    }

    /// Aufnahme aus der Kamera (Verifizierungs-Selfie) — bereits im Speicher.
    static func compressSelfie(_ image: UIImage) async throws -> Data {
        try await run {
            let scaled = scaleToMaxEdge(image, maxEdge: selfieMaxEdgePx)
            guard let data = jpeg(scaled) else { throw PhotoUnreadableError() }
            return data
        }
    }

    // MARK: - Innenleben

    private static func run<T: Sendable>(_ work: @escaping @Sendable () throws -> T) async throws -> T {
        try await Task.detached(priority: .userInitiated) { try work() }.value
    }

    private static func pixelSize(of source: CGImageSource) -> (Int, Int) {
        guard
            let properties = CGImageSourceCopyPropertiesAtIndex(source, 0, nil) as? [CFString: Any],
            let width = properties[kCGImagePropertyPixelWidth] as? Int,
            let height = properties[kCGImagePropertyPixelHeight] as? Int
        else { return (0, 0) }

        // Bei gedrehten Aufnahmen tauschen Breite und Höhe — für die
        // Mindestgröße ist das egal, für die Fehlermeldung aber nicht.
        let orientation = properties[kCGImagePropertyOrientation] as? UInt32 ?? 1
        return (5...8).contains(orientation) ? (height, width) : (width, height)
    }

    /// Skaliert und dreht in einem Schritt (`kCGImageSourceCreateThumbnail…`).
    private static func thumbnail(from source: CGImageSource, maxEdge: Int) -> UIImage? {
        let options: [CFString: Any] = [
            kCGImageSourceCreateThumbnailFromImageAlways: true,
            kCGImageSourceCreateThumbnailWithTransform: true,
            kCGImageSourceShouldCacheImmediately: true,
            kCGImageSourceThumbnailMaxPixelSize: maxEdge,
        ]
        guard let cgImage = CGImageSourceCreateThumbnailAtIndex(source, 0, options as CFDictionary)
        else { return nil }
        return UIImage(cgImage: cgImage)
    }

    private static func scaleToMaxEdge(_ image: UIImage, maxEdge: Int) -> UIImage {
        let longEdge = max(image.size.width, image.size.height)
        guard longEdge > CGFloat(maxEdge) else { return normalized(image) }
        let scale = CGFloat(maxEdge) / longEdge
        let target = CGSize(width: round(image.size.width * scale), height: round(image.size.height * scale))
        return render(size: target) { image.draw(in: CGRect(origin: .zero, size: target)) }
    }

    private static func centerSquare(_ image: UIImage, size: Int) -> UIImage {
        let side = min(image.size.width, image.size.height)
        let origin = CGPoint(x: (image.size.width - side) / 2, y: (image.size.height - side) / 2)
        let target = CGSize(width: CGFloat(size), height: CGFloat(size))
        let factor = CGFloat(size) / side

        return render(size: target) {
            image.draw(
                in: CGRect(
                    x: -origin.x * factor,
                    y: -origin.y * factor,
                    width: image.size.width * factor,
                    height: image.size.height * factor
                )
            )
        }
    }

    /// Zeichnet die Aufnahme in ihrer Blickrichtung neu, damit `imageOrientation`
    /// nicht weitergeschleppt wird.
    private static func normalized(_ image: UIImage) -> UIImage {
        guard image.imageOrientation != .up else { return image }
        return render(size: image.size) {
            image.draw(in: CGRect(origin: .zero, size: image.size))
        }
    }

    private static func render(size: CGSize, draw: () -> Void) -> UIImage {
        let format = UIGraphicsImageRendererFormat.default()
        format.scale = 1
        format.opaque = true
        return UIGraphicsImageRenderer(size: size, format: format).image { _ in draw() }
    }

    private static func jpeg(_ image: UIImage) -> Data? {
        image.jpegData(compressionQuality: jpegQuality)
    }
}
