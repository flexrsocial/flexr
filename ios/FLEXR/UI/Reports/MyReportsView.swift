import SwiftUI

/// „Meine Meldungen" — der Stand jeder abgegebenen Meldung.
///
/// Art. 16 Abs. 5 DSA verlangt, dass der Melder die Entscheidung über seine
/// Meldung erfährt. Eine stille Bearbeitung reicht dafür nicht: Hier steht zu
/// jeder Meldung das Aktenzeichen, ob sie noch läuft und, sobald entschieden
/// wurde, die Begründung im Wortlaut.
struct MyReportsView: View {

    let onBack: () -> Void

    @Environment(AppContainer.self) private var container

    @State private var isLoading = true
    @State private var reports: [MyReport] = []
    @State private var error: String?

    var body: some View {
        VStack(spacing: 0) {
            BackHeader(title: "Meine Meldungen", titleStyle: .headlineSmall, onBack: onBack)

            if isLoading {
                LoadingStateView()
            } else if let error {
                EmptyStateView(
                    icon: .symbol(FlexrIcon.report),
                    title: "Konnte nicht geladen werden",
                    message: error
                )
            } else if reports.isEmpty {
                EmptyStateView(
                    icon: .symbol(FlexrIcon.report),
                    title: "Keine Meldungen",
                    message: "Hier siehst du, was aus deinen Meldungen geworden ist — "
                        + "sobald du eine abgegeben hast."
                )
            } else {
                ScrollView {
                    LazyVStack(spacing: 10) {
                        ForEach(reports) { report in
                            ReportCard(report: report)
                        }
                    }
                    .padding(.top, 6)
                    .padding(.bottom, 24)
                }
            }
        }
        .padding(.horizontal, 20)
        .task { await load() }
    }

    private func load() async {
        isLoading = true
        error = nil
        do {
            reports = try await container.safety.myReports()
        } catch {
            self.error = error.localizedDescription
        }
        isLoading = false
    }
}

private struct ReportCard: View {

    let report: MyReport

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            HStack {
                Text(report.reference)
                    .flexrText(.mono)
                    .foregroundStyle(FlexrColor.plate)
                Spacer()
                OutcomePill(outcome: report.outcome)
            }

            if let createdAt = report.createdAt {
                Text("Gemeldet am \(ServerTime.formatDateTime(createdAt))")
                    .flexrText(.bodySmall)
                    .foregroundStyle(FlexrColor.chalkDim)
                    .padding(.top, 3)
            }

            Text(report.reason)
                .flexrText(.bodyMedium)
                .foregroundStyle(FlexrColor.chalk)
                .padding(.top, 9)

            if report.outcome == .open {
                Text(
                    "Wir prüfen deine Meldung innerhalb von 72 Stunden — bei Gefahr "
                        + "für eine Person sofort."
                )
                .flexrText(.bodySmall)
                .foregroundStyle(FlexrColor.chalkDim)
                .padding(.top, 9)
            } else if let note = report.decisionNote, !note.isEmpty {
                Text("Unsere Entscheidung")
                    .flexrText(.bodySmall)
                    .foregroundStyle(FlexrColor.chalkDim)
                    .padding(.top, 9)
                Text(note)
                    .flexrText(.bodyMedium)
                    .foregroundStyle(FlexrColor.chalk)
                    .padding(.top, 2)

                if let decidedAt = report.decidedAt {
                    Text(
                        "Entschieden am \(ServerTime.formatDateTime(decidedAt)). Bist du damit "
                            + "nicht einverstanden, schreib uns an flexr.social@proton.me."
                    )
                    .flexrText(.bodySmall)
                    .foregroundStyle(FlexrColor.chalkDim)
                    .padding(.top, 4)
                }
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(.horizontal, 14)
        .padding(.vertical, 12)
        .flexrSurface(fill: FlexrColor.surface2)
    }
}

private struct OutcomePill: View {

    let outcome: ReportOutcome

    private var content: (label: String, tint: Color) {
        switch outcome {
        case .open: ("in Prüfung", FlexrColor.chalkDim)
        case .noAction: ("kein Verstoß", FlexrColor.chalkDim)
        case .actionTaken: ("eingeschritten", FlexrColor.plate)
        }
    }

    var body: some View {
        Text(content.label)
            .flexrText(.bodySmall)
            .foregroundStyle(content.tint)
            .padding(.horizontal, 9)
            .padding(.vertical, 3)
            .overlay(Capsule().strokeBorder(FlexrColor.hairline, lineWidth: 1))
    }
}
