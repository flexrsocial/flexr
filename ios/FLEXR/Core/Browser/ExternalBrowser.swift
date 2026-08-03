import SafariServices
import SwiftUI

/// Öffnet eine externe Seite (Stripe-Checkout, Billing-Portal) in einem
/// `SFSafariViewController`.
///
/// Bewusst kein WKWebView: Zahlungsvorgänge gehören in die echte Browser-
/// Umgebung des Geräts — dort sind Adressleiste, Zertifikatsprüfung und die
/// gespeicherten Zahlungsmittel des Nutzers verfügbar, und die App bekommt zu
/// keinem Zeitpunkt Zahlungsdaten zu sehen. Es ist dieselbe Entscheidung wie
/// beim Chrome Custom Tab auf Android.
struct SafariSheet: UIViewControllerRepresentable {

    let url: URL

    func makeUIViewController(context: Context) -> SFSafariViewController {
        let configuration = SFSafariViewController.Configuration()
        configuration.entersReaderIfAvailable = false
        let controller = SFSafariViewController(url: url, configuration: configuration)
        controller.preferredBarTintColor = UIColor(FlexrColor.ink)
        controller.preferredControlTintColor = UIColor(FlexrColor.plate)
        controller.dismissButtonStyle = .close
        return controller
    }

    func updateUIViewController(_ controller: SFSafariViewController, context: Context) {}
}

extension View {
    /// Blendet eine externe Seite ein, sobald `url` gesetzt ist.
    func externalPage(_ url: Binding<ExternalURL?>) -> some View {
        sheet(item: url) { target in
            SafariSheet(url: target.url).ignoresSafeArea()
        }
    }
}

/// Identifizierbare Hülle, damit `.sheet(item:)` damit umgehen kann.
struct ExternalURL: Identifiable {
    let url: URL
    var id: String { url.absoluteString }

    init?(_ raw: String) {
        guard let url = URL(string: raw), url.scheme?.hasPrefix("http") == true else { return nil }
        self.url = url
    }
}
