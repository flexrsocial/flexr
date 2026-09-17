import Foundation
import StoreKit
import UIKit

/// FLEXR Premium über den App Store kaufen.
///
/// Für Funktionen, die in dieser App wirken, ist StoreKit der einzige
/// zulässige Kaufweg (App Review Guideline 3.1.1) — Stripe bleibt dem Browser.
/// Was beide gemeinsam haben: **Die App schaltet nichts frei.** Sie reicht nur
/// den signierten Beleg beim Server ein; ob daraus Premium wird, entscheidet
/// der Server, nachdem er die Signatur gegen Apples Wurzelzertifikat geprüft
/// hat (siehe `backend/app/store_billing.py`). Eine manipulierte App kann sich
/// hier nichts erschleichen.
///
/// Drei Wege führen zu einem Beleg, und alle drei münden in `einreichen(_:)`:
///
///  1. Der Kauf selbst (`kaufen(produktID:)`).
///  2. `bestehendeKaeufeAbgleichen()` beim Start. Das ist kein Beiwerk,
///     sondern der Weg zurück aus jeder Störung: Wer beim Kauf gerade keine
///     Verbindung hatte, das Gerät gewechselt oder die App neu installiert
///     hat, bekommt sein Premium dadurch von selbst wieder — ohne den Knopf
///     „Käufe wiederherstellen", den er erst suchen müsste.
///  3. `Transaction.updates` — Verlängerungen, Rückerstattungen und Käufe, die
///     erst nach einer Freigabe durch die Eltern zustande kommen. Dieser
///     Strom läuft, solange die App läuft, und **muss** beim Start geöffnet
///     werden: Apple stellt darüber Belege zu, die sonst niemand abholt.
@MainActor
@Observable
final class StoreKitService {

    /// Was ein Kaufversuch ergeben hat.
    enum Ausgang: Equatable {
        case erfolgreich
        case abgebrochen
        /// Apple wartet noch auf eine Freigabe (z. B. „Kauf bitten").
        case ausstehend
        case fehlgeschlagen(String)
    }

    private let api: FlexrAPI

    /// Der Preis, wie der App Store ihn in der Sprache und Währung des Kontos
    /// schreibt. Bewusst nicht selbst formatiert: Apple rechnet Währung und
    /// Steuer je nach Land, und der angezeigte Preis muss der sein, der auch
    /// abgebucht wird.
    private(set) var preis: String?
    private(set) var laeuftKauf = false

    private var produkt: Product?
    private var beobachter: Task<Void, Never>?

    init(api: FlexrAPI) {
        self.api = api
    }

    // Bewusst kein `deinit` mit `beobachter?.cancel()`: Der Dienst lebt so
    // lange wie die App (eine Instanz im AppContainer), und der Strom der
    // Transaktionen *soll* die ganze Zeit offen sein — Apple stellt darüber
    // Verlängerungen und Rückerstattungen zu, die sonst niemand abholt.

    /// Den Strom der Transaktionen öffnen. Einmal beim Start, nicht je Bildschirm.
    func beobachten() {
        guard beobachter == nil else { return }
        beobachter = Task { [weak self] in
            for await ergebnis in Transaction.updates {
                await self?.einreichen(ergebnis, meldend: false)
            }
        }
    }

    /// Produktdaten laden, damit der echte Preis dasteht, bevor jemand tippt.
    @discardableResult
    func produktLaden(_ produktID: String) async -> Product? {
        if let produkt, produkt.id == produktID { return produkt }
        do {
            let gefunden = try await Product.products(for: [produktID]).first
            produkt = gefunden
            preis = gefunden?.displayPrice
            return gefunden
        } catch {
            return nil
        }
    }

    /// Kaufvorgang starten.
    func kaufen(produktID: String) async -> Ausgang {
        guard let produkt = await produktLaden(produktID) else {
            return .fehlgeschlagen(FlexrStrings.current(.purchaseUnavailable))
        }

        laeuftKauf = true
        defer { laeuftKauf = false }

        do {
            switch try await produkt.purchase() {
            case .success(let ergebnis):
                return await einreichen(ergebnis, meldend: true)
            case .userCancelled:
                return .abgebrochen
            case .pending:
                // „Kauf bitten" und ähnliche Freigaben. Kommt der Kauf später
                // zustande, meldet Apple ihn über Transaction.updates - der
                // Beobachter oben fängt ihn dann auf.
                return .ausstehend
            @unknown default:
                return .fehlgeschlagen(FlexrStrings.current(.purchaseFailed))
            }
        } catch {
            return .fehlgeschlagen(error.localizedDescription)
        }
    }

    /// Laufende Berechtigungen beim Server nachreichen. Läuft still.
    func bestehendeKaeufeAbgleichen() async {
        for await ergebnis in Transaction.currentEntitlements {
            await einreichen(ergebnis, meldend: false)
        }
    }

    /// Den signierten Beleg beim Server einreichen — der einzige Ort, an dem
    /// aus einem Kauf eine Berechtigung wird.
    @discardableResult
    private func einreichen(
        _ ergebnis: VerificationResult<Transaction>, meldend: Bool
    ) async -> Ausgang {
        // `unverified` heißt: Das Gerät selbst hält den Beleg für nicht
        // vertrauenswürdig. Der Server würde ihn ohnehin ablehnen - ihn
        // trotzdem zu schicken, hieße nur, eine Fälschung weiterzureichen.
        guard case .verified(let transaktion) = ergebnis else {
            return meldend ? .fehlgeschlagen(FlexrStrings.current(.purchaseFailed)) : .abgebrochen
        }

        do {
            _ = try await api.submitAppleTransaction(ergebnis.jwsRepresentation)
            // Erst jetzt abschließen: Ein nicht abgeschlossener Kauf wird von
            // Apple beim nächsten Start erneut zugestellt. Genau das soll er
            // auch, solange der Server ihn nicht angenommen hat.
            await transaktion.finish()
            return .erfolgreich
        } catch {
            return .fehlgeschlagen(error.localizedDescription)
        }
    }

    /// Abo verwalten und kündigen — beim App Store, nicht bei uns: Apple ist
    /// der Händler, wir könnten das Abo gar nicht beenden.
    func aboVerwalten() async {
        guard
            let szene = UIApplication.shared.connectedScenes
                .compactMap({ $0 as? UIWindowScene })
                .first
        else { return }
        try? await AppStore.showManageSubscriptions(in: szene)
    }
}
