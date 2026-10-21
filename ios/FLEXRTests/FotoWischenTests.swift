import CoreGraphics
import XCTest

@testable import FLEXR

/// Seit 21.10.2026 blättert im Match-Profil ein waagrechtes Wischen auf dem
/// Foto durch die Fotos (vorher nur über die Vollbildansicht oder die Striche).
/// Gleiche Regeln wie `FotoWischenTest` auf Android.
final class FotoWischenTests: XCTestCase {

    private func index(_ aktuell: Int, von anzahl: Int, x: CGFloat, y: CGFloat = 0) -> Int {
        FotoWischen.photoIndex(after: aktuell, count: anzahl, translation: CGSize(width: x, height: y),
                               threshold: 100)
    }

    func testNachLinksKommtDasNaechsteNachRechtsDasVorige() {
        XCTAssertEqual(index(1, von: 4, x: -150), 2)
        XCTAssertEqual(index(1, von: 4, x: 150), 0)
    }

    func testKurzeBewegungUnterDerSchwelleWechseltNicht() {
        XCTAssertEqual(index(1, von: 4, x: -99), 1)
        XCTAssertEqual(index(1, von: 4, x: 99), 1)
        XCTAssertEqual(index(1, von: 4, x: -100), 2)
    }

    func testAmErstenUndLetztenFotoBleibtEsStehen() {
        XCTAssertEqual(index(0, von: 3, x: 300), 0)
        XCTAssertEqual(index(2, von: 3, x: -300), 2)
    }

    func testMitEinemFotoPassiertNichts() {
        XCTAssertEqual(index(0, von: 1, x: -300), 0)
    }

    /// Eher senkrecht gewischt (etwa beim Scrollen) zählt nicht als Blättern.
    func testSenkrechteBewegungZaehltNicht() {
        XCTAssertEqual(index(1, von: 4, x: -150, y: 200), 1)
        XCTAssertEqual(index(1, von: 4, x: -150, y: 120), 2)
    }

    func testStandardschwelleWieAndroid() {
        XCTAssertEqual(FotoWischen.threshold, 40)
    }
}
