import SwiftUI

/// Rechtstexte, nativ gesetzt.
///
/// Tabellen scrollen bei Bedarf waagerecht in ihrem eigenen Container, damit die
/// Seite selbst nie seitlich verrutscht.
struct LegalView: View {

    let document: LegalDocument
    let onBack: () -> Void

    private var page: LegalPage { LegalContent.page(for: document) }

    var body: some View {
        VStack(spacing: 0) {
            BackHeader(title: document.title, onBack: onBack)
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
                    HStack(alignment: .top, spacing: 0) {
                        Text("\(row.0):")
                            .flexrText(.bodyMedium)
                            .foregroundStyle(FlexrColor.chalk)
                            .frame(width: 140, alignment: .leading)
                        Text(row.1)
                            .flexrText(.bodyMedium)
                            .foregroundStyle(FlexrColor.chalkDim)
                    }
                }
            }
            .padding(.bottom, 8)

        case .table(let headers, let rows):
            LegalTable(headers: headers, rows: rows)

        case .faq(let question, let answer):
            FaqRow(question: question, answer: answer)
        }
    }

    /// a), b), c) … — mehr als 26 Punkte hat keiner der Texte.
    private static func letter(at index: Int) -> String {
        let scalar = UnicodeScalar(UInt8(97 + min(index, 25)))
        return "\(Character(scalar)))"
    }
}

private struct LegalTable: View {

    let headers: [String]
    let rows: [[String]]

    private static let columnWidth: CGFloat = 200

    var body: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            VStack(alignment: .leading, spacing: 0) {
                HStack(alignment: .top, spacing: 0) {
                    ForEach(headers, id: \.self) { header in
                        Text(header)
                            .flexrText(.titleSmall)
                            .foregroundStyle(FlexrColor.chalkDim)
                            .frame(width: Self.columnWidth, alignment: .leading)
                            .padding(.trailing, 10)
                    }
                }
                .padding(.bottom, 6)

                ForEach(rows.indices, id: \.self) { index in
                    let row = rows[index]
                    HairlineDivider(color: FlexrColor.steel)
                    HStack(alignment: .top, spacing: 0) {
                        ForEach(row.indices, id: \.self) { cellIndex in
                            Text(row[cellIndex])
                                .flexrText(.bodySmall)
                                .foregroundStyle(FlexrColor.chalkDim)
                                .frame(width: Self.columnWidth, alignment: .leading)
                                .padding(.trailing, 10)
                        }
                    }
                    .padding(.vertical, 8)
                }
            }
        }
        .padding(.bottom, 12)
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
