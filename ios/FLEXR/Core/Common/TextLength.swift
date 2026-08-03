import Foundation

extension String {

    /// Zeichenzahl so, wie das Backend sie zählt.
    ///
    /// FastAPI/Pydantic prüft Längen mit Pythons `len()`, und das zählt
    /// **Unicode-Codepoints**. Swifts `count` zählt dagegen Graphemcluster:
    /// „🏋️‍♀️" ist für Swift ein Zeichen, für Python fünf. Würde die Oberfläche
    /// nach `count` kappen, ließe sie Bios durch, die der Server anschließend
    /// mit 422 zurückweist — deshalb wird überall in Codepoints gerechnet.
    ///
    /// (Die Android-App rechnet in UTF-16-Einheiten und ist damit strenger als
    /// nötig; die Grenze ist dort dieselbe oder kleiner, nie größer.)
    var backendLength: Int { unicodeScalars.count }

    /// Auf `limit` Codepoints kürzen. Ein am Ende angeschnittener Graphemcluster
    /// wird mit entfernt, damit kein halbes Emoji stehen bleibt.
    func truncatedToBackendLength(_ limit: Int) -> String {
        guard backendLength > limit else { return self }
        var result = self
        while result.backendLength > limit, !result.isEmpty {
            result.removeLast()
        }
        return result
    }
}
