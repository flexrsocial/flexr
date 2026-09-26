"""Erzeugt den QR-Code zur iPhone-Installationsanleitung (icons/qr-ios-install.svg).

Den Link "iOS: jetzt installieren" im Beta-Hinweis tippen auch Leute am
Computer oder auf Android an. Aufs iPhone kommt FLEXR aber nur aus Safari auf
dem iPhone selbst - die Anleitung zeigt ihnen deshalb diesen Code, den die
iPhone-Kamera direkt oeffnet. Statisch statt im Browser erzeugt: die Adresse
aendert sich nicht, und eine QR-Bibliothek in der App waere dafuer zu viel.

    python3 frontend/brand/build_ios_qr.py

Nach einer Aenderung die Versionsnummer im <img> (app/index.html) hochzaehlen
(nginx liefert /icons/ ein Jahr lang als unveraenderlich aus).
"""
from pathlib import Path

import qrcode
import qrcode.image.svg

ZIEL = Path(__file__).resolve().parent.parent / "icons" / "qr-ios-install.svg"
ADRESSE = "https://flexr.social/app/?ios=installieren"


def main() -> None:
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
        image_factory=qrcode.image.svg.SvgPathFillImage,
    )
    qr.add_data(ADRESSE)
    qr.make(fit=True)
    qr.make_image().save(ZIEL)
    print(f"{ZIEL} ({qr.version}) -> {ADRESSE}")


if __name__ == "__main__":
    main()
