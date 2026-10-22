import XCTest

@testable import FLEXR

/// Mail-Links, die die Web-App am iPhone über `flexr://` weiterreicht
/// (seit 2.4.16), und die gleichen Pfade über https.
final class MailLinkTests: XCTestCase {

    private func ziel(_ adresse: String) -> MailLinkZiel? {
        MailLinkZiel(url: URL(string: adresse)!)
    }

    func testPasswortLinkMitToken() {
        XCTAssertEqual(ziel("flexr://flexr.social/app/open/?reset=abc-123_x"), .passwort(token: "abc-123_x"))
        XCTAssertEqual(ziel("https://flexr.social/app/open/?reset=abc"), .passwort(token: "abc"))
    }

    func testReiter() {
        XCTAssertEqual(ziel("flexr://flexr.social/app/open/matches"), .reiter(.matches))
        XCTAssertEqual(ziel("flexr://flexr.social/app/open/swipe"), .reiter(.swipe))
    }

    func testOhneReiterOderUnbekanntOeffnetNurDieApp() {
        XCTAssertEqual(ziel("flexr://flexr.social/app/open/"), .app)
        XCTAssertEqual(ziel("flexr://flexr.social/app/open/irgendwas"), .app)
        XCTAssertEqual(ziel("flexr://flexr.social/app/open/?reset="), .app)
    }

    func testFremdeLinksBleibenUnberuehrt() {
        // Rückkehr aus dem Stripe-Checkout und andere Ziele gehen weiter
        // ihren eigenen Weg (RootView.onOpenURL).
        XCTAssertNil(ziel("flexr://checkout/success"))
        XCTAssertNil(ziel("flexr://flexr.social/app/"))
        XCTAssertNil(ziel("https://example.com/app/open/?reset=abc"))
        XCTAssertNil(ziel("flexr://flexr.social/app/opener"))
    }
}
