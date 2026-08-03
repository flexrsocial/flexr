import AVFoundation
import SwiftUI
import UIKit

/// Frontkamera für die Live-Verifizierung.
///
/// AVFoundation statt CameraX, sonst dieselbe Idee: Vorschau plus Einzelbild.
/// Das Bild verlässt den Speicher nie als Datei, sondern geht direkt
/// komprimiert in den Upload.
@MainActor
@Observable
final class CameraController: NSObject {

    private(set) var isRunning = false
    private(set) var isConfigured = false

    @ObservationIgnored let session = AVCaptureSession()
    @ObservationIgnored private let output = AVCapturePhotoOutput()
    @ObservationIgnored private let queue = DispatchQueue(label: "social.flexr.camera")
    @ObservationIgnored private var captureContinuation: CheckedContinuation<UIImage?, Never>?

    var authorizationStatus: AVAuthorizationStatus {
        AVCaptureDevice.authorizationStatus(for: .video)
    }

    var hasPermission: Bool { authorizationStatus == .authorized }

    func requestPermission() async -> Bool {
        if hasPermission { return true }
        return await AVCaptureDevice.requestAccess(for: .video)
    }

    func start() async {
        guard hasPermission else { return }
        if !isConfigured { configure() }
        guard isConfigured, !isRunning else { return }
        isRunning = true
        await withCheckedContinuation { continuation in
            queue.async { [session] in
                session.startRunning()
                continuation.resume()
            }
        }
    }

    func stop() {
        guard isRunning else { return }
        isRunning = false
        queue.async { [session] in session.stopRunning() }
    }

    private func configure() {
        session.beginConfiguration()
        session.sessionPreset = .photo

        guard
            let device = AVCaptureDevice.default(
                .builtInWideAngleCamera,
                for: .video,
                position: .front
            ),
            let input = try? AVCaptureDeviceInput(device: device),
            session.canAddInput(input),
            session.canAddOutput(output)
        else {
            session.commitConfiguration()
            return
        }

        session.addInput(input)
        session.addOutput(output)
        session.commitConfiguration()
        isConfigured = true
    }

    /// Nimmt ein Bild auf. Liefert nil, wenn die Aufnahme scheitert.
    func capture() async -> UIImage? {
        guard isRunning, captureContinuation == nil else { return nil }
        let settings = AVCapturePhotoSettings()
        return await withCheckedContinuation { continuation in
            captureContinuation = continuation
            output.capturePhoto(with: settings, delegate: self)
        }
    }

    private func finish(with image: UIImage?) {
        captureContinuation?.resume(returning: image)
        captureContinuation = nil
    }
}

extension CameraController: AVCapturePhotoCaptureDelegate {

    nonisolated func photoOutput(
        _ output: AVCapturePhotoOutput,
        didFinishProcessingPhoto photo: AVCapturePhoto,
        error: Error?
    ) {
        let image = photo.fileDataRepresentation().flatMap(UIImage.init(data:))
        Task { @MainActor in self.finish(with: image) }
    }
}

/// Kameravorschau als SwiftUI-Ansicht.
struct CameraPreview: UIViewRepresentable {

    let session: AVCaptureSession

    func makeUIView(context: Context) -> PreviewView {
        let view = PreviewView()
        view.previewLayer.session = session
        view.previewLayer.videoGravity = .resizeAspectFill
        return view
    }

    func updateUIView(_ view: PreviewView, context: Context) {
        if view.previewLayer.session !== session {
            view.previewLayer.session = session
        }
    }

    final class PreviewView: UIView {
        override class var layerClass: AnyClass { AVCaptureVideoPreviewLayer.self }

        var previewLayer: AVCaptureVideoPreviewLayer {
            // swiftlint:disable:next force_cast
            layer as! AVCaptureVideoPreviewLayer
        }
    }
}
