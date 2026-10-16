import SwiftUI

/// Rechtstexte, nativ gesetzt.
///
/// Tabellen scrollen bei Bedarf waagerecht in ihrem eigenen Container, damit die
/// Seite selbst nie seitlich verrutscht.
struct LegalView: View {

    let document: LegalDocument
    let onBack: () -> Void

    @Environment(LanguageStore.self) private var languageStore

    private var page: LegalPage { LegalContent.page(for: document) }

    var body: some View {
        VStack(spacing: 0) {
            BackHeader(title: languageStore.strings(document.titleKey), onBack: onBack)
                .padding(.horizontal, 8)

            ScrollView {
                VStack(alignment: .leading, spacing: 0) {
                    if let intro = page.intro {
                        Text(intro)
                            .flexrText(.bodyMedium)
                            .foregroundStyle(FlexrColor.chalkDim)
                            .padding(.bottom, 20)
                    }
                    ForEach(page.blocks) { block in
                        LegalBlockView(block: block)
                    }
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(.horizontal, 20)
                .padding(.top, 16)
                .padding(.bottom, 48)
            }
        }
        .background(FlexrBackground())
    }
}

private struct LegalBlockView: View {

    let block: LegalBlock

    var body: some View {
        switch block {
        case .heading(let text):
            VStack(alignment: .leading, spacing: 6) {
                Text(text)
                    .flexrText(.titleMedium)
                    .foregroundStyle(FlexrColor.chalk)
                HairlineDivider(color: FlexrColor.steel)
            }
            .padding(.top, 24)
            .padding(.bottom, 10)

        case .paragraph(let text):
            Text(text)
                .flexrText(.bodyMedium)
                .foregroundStyle(FlexrColor.chalkDim)
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(.bottom, 8)

        case .note(let text):
            Text(text)
                .flexrText(.bodySmall)
                .foregroundStyle(FlexrColor.chalkDim)
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(.vertical, 8)

        case .bullets(let items):
            VStack(alignment: .leading, spacing: 8) {
                ForEach(items, id: \.self) { item in
                    HStack(alignment: .top, spacing: 10) {
                        Text("•").flexrText(.bodyMedium).foregroundStyle(FlexrColor.plate)
                        Text(item).flexrText(.bodyMedium).foregroundStyle(FlexrColor.chalkDim)
                    }
                }
            }
            .padding(.bottom, 8)

        case .lettered(let items):
            VStack(alignment: .leading, spacing: 8) {
                ForEach(items.indices, id: \.self) { offset in
                    let item = items[offset]
                    HStack(alignment: .top, spacing: 10) {
                        Text(Self.letter(at: offset))
                            .font(.flexrWorkSans(14, weight: 600))
                            .foregroundStyle(FlexrColor.chalk)
                        Text(item).flexrText(.bodyMedium).foregroundStyle(FlexrColor.chalkDim)
                    }
                }
            }
            .padding(.bottom, 8)

        case .keyValues(let rows):
            VStack(alignment: .leading, spacing: 6) {
                ForEach(rows.indices, id: \.self) { index in
                    let row = rows[index]
                    // Lange Schlüssel („Firmenbuchnummer:") liefen bis 2.4.11
                    // in den Wert daneben, der Doppelpunkt brach in eine
                    // eigene Zeile. Jetzt werden sie kleiner statt breiter.
                    HStack(alignment: .firstTextBaseline, spacing: 10) {
                        Text("\(row.0):")
                            .flexrText(.bodyMedium)
                            .foregroundStyle(FlexrColor.chalk)
                            .lineLimit(1)
                            .minimumScaleFactor(0.7)
                            .frame(width: 132, alignment: .leading)
                        Text(row.1)
                            .flexrText(.bodyMedium)
                            .foregroundStyle(FlexrColor.chalkDim)
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }
                }
            }
            .padding(.bottom, 8)

        case .table(let headers, let rows):
            LegalTable(headers: headers, rows: rows)

        case .faq(let question, let answer):
            FaqRow(question: question, answer: answer)

        case .withdrawalForm:
            WithdrawalFormView()
        }
    }

    /// a), b), c) … — mehr als 26 Punkte hat keiner der Texte.
    private static func letter(at index: Int) -> String {
        let scalar = UnicodeScalar(UInt8(97 + min(index, 25)))
        return "\(Character(scalar)))"
    }
}

/// Tabelle als Karte je Zeile: der erste Wert als Titel, die übrigen mit ihrer
/// Spaltenüberschrift darunter.
///
/// Bis 2.4.11 stand hier eine waagrecht scrollende Tabelle mit 200 pt je
/// Spalte. Alle Tabellen haben drei Spalten - die dritte lag auf dem Handy
/// ganz außerhalb des Bildes (beim Rücktrittsrecht ausgerechnet der Weg zur
/// Rückerstattung), die zweite war am Rand mitten im Wort abgeschnitten, und
/// die Höhe der unsichtbaren Spalte hinterließ große Lücken.
private struct LegalTable: View {

    let headers: [String]
    let rows: [[String]]

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            ForEach(rows.indices, id: \.self) { index in
                let row = rows[index]
                if index > 0 { HairlineDivider(color: FlexrColor.steel) }
                VStack(alignment: .leading, spacing: 8) {
                    if let titel = row.first {
                        Text(titel)
                            .flexrText(.titleSmall)
                            .foregroundStyle(FlexrColor.chalk)
                            .fixedSize(horizontal: false, vertical: true)
                    }
                    ForEach(Array(row.indices.dropFirst()), id: \.self) { cellIndex in
                        VStack(alignment: .leading, spacing: 2) {
                            if cellIndex < headers.count {
                                Text(headers[cellIndex].uppercased())
                                    .font(.flexrMono(10, weight: 500))
                                    .tracking(0.6)
                                    .foregroundStyle(FlexrColor.plate.opacity(0.85))
                            }
                            Text(row[cellIndex])
                                .flexrText(.bodySmall)
                                .foregroundStyle(FlexrColor.chalkDim)
                                .fixedSize(horizontal: false, vertical: true)
                        }
                    }
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(.vertical, 12)
            }
        }
        .padding(.horizontal, 14)
        .flexrSurface(fill: FlexrColor.surface2, border: FlexrColor.hairline)
        .padding(.bottom, 14)
    }
}

private struct FaqRow: View {

    let question: String
    let answer: String

    @State private var isExpanded = false

    var body: some View {
        Button {
            withAnimation(.easeOut(duration: 0.2)) { isExpanded.toggle() }
        } label: {
            VStack(alignment: .leading, spacing: 10) {
                HStack(alignment: .top, spacing: 12) {
                    Text(question)
                        .flexrText(.titleSmall)
                        .foregroundStyle(FlexrColor.chalk)
                        .frame(maxWidth: .infinity, alignment: .leading)
                    Image(systemName: isExpanded ? FlexrIcon.remove : FlexrIcon.add)
                        .font(.system(size: 15, weight: .semibold))
                        .foregroundStyle(FlexrColor.plate)
                }
                if isExpanded {
                    Text(answer)
                        .flexrText(.bodyMedium)
                        .foregroundStyle(FlexrColor.chalkDim)
                        .frame(maxWidth: .infinity, alignment: .leading)
                }
            }
            .padding(16)
            .contentShape(Rectangle())
            .flexrSurface(
                fill: FlexrColor.surface2,
                border: isExpanded ? FlexrColor.plate.opacity(0.35) : FlexrColor.hairline
            )
        }
        .buttonStyle(.plain)
        .padding(.bottom, 12)
    }
}
