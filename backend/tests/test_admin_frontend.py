from pathlib import Path


ADMIN_HTML = Path(__file__).resolve().parents[2] / "frontend" / "admin.html"


def test_fotoablehnung_sendet_strukturierten_grund():
    """Das Admin-UI darf nicht auf den generischen Backend-Fallback fallen."""
    html = ADMIN_HTML.read_text(encoding="utf-8")

    assert "PHOTO_REJECTION_REASONS" in html
    assert "const rejection = askPhotoRejection()" in html
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


def test_foermliche_meldungen_sind_im_admin_bedienbar():
    html = ADMIN_HTML.read_text(encoding="utf-8")

    assert 'id="noticesTableWrap"' in html
    assert "async function loadNotices()" in html
    assert "'/api/admin/notices'" in html
    assert "`/api/admin/notices/${id}/decide`" in html
    assert "stats.open_notices" in html
