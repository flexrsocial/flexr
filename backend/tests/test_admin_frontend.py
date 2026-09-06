from pathlib import Path


ADMIN_HTML = Path(__file__).resolve().parents[2] / "frontend" / "admin.html"


def test_fotoablehnung_sendet_strukturierten_grund():
    """Das Admin-UI darf nicht auf den generischen Backend-Fallback fallen."""
    html = ADMIN_HTML.read_text(encoding="utf-8")

    assert "PHOTO_REJECTION_REASONS" in html
    # Seit 06.09.2026 ein eigener Dialog statt prompt() - der Aufruf ist
    # deshalb asynchron und bekommt das Foto mit, siehe
    # test_fotoablehnung_laeuft_ueber_einen_dialog unten.
    assert "const rejection = await askPhotoRejection(photo)" in html
    assert "body: JSON.stringify(rejection)" in html
    for reason in (
        "no_person",
        "not_account_holder",
        "multiple_people",
        "nudity",
        "violence",
        "minor",
        "contact_details",
        "third_party_rights",
        "unusable",
        "other",
    ):
        assert f"['{reason}'," in html


def test_fotoablehnung_laeuft_ueber_einen_dialog():
    """Vorher zwei verschachtelte prompt()-Fenster: der Pruefer musste die
    Nummer eines Grundes aus einer Liste 1-10 abtippen, ohne das Bild zu
    sehen (prompt blendet die Seite aus), und ein Vertipper brach den ganzen
    Vorgang ab. Bei einem Schritt, der mehrmals taeglich vorkommt."""
    html = ADMIN_HTML.read_text(encoding="utf-8")

    assert "rejectModalBackdrop" in html
    # Das zu beurteilende Bild steht im Dialog.
    assert 'id="rejectPreviewImg"' in html
    # Gruende als Auswahlliste, nicht als abzutippende Nummern.
    assert 'name="rejectReason"' in html
    assert "prompt(`Ablehnungsgrund auswählen" not in html
    # Das Ergaenzungsfeld gehoert nur zu "other".
    assert "radio.value === 'other' ? 'block' : 'none'" in html
    # Die globale Regel label{text-transform:uppercase} passt nicht zu einer
    # Liste ganzer Saetze und wird fuer die Gruende zurueckgesetzt.
    stelle = html.index(".reject-reasons label{")
    assert "text-transform:none" in html[stelle:stelle + 400]


def test_foermliche_meldungen_sind_im_admin_bedienbar():
    html = ADMIN_HTML.read_text(encoding="utf-8")

    assert 'id="noticesTableWrap"' in html
    assert "async function loadNotices()" in html
    assert "'/api/admin/notices'" in html
    assert "`/api/admin/notices/${id}/decide`" in html
    assert "stats.open_notices" in html
