from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QByteArray, QRectF, Qt
from PySide6.QtGui import QGuiApplication, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer


ROOT = Path(__file__).resolve().parents[1]
SVG_PATH = ROOT / "src" / "shelf" / "ui" / "assets" / "shelf_icon.svg"
ICNS_PATH = ROOT / "src" / "shelf" / "ui" / "assets" / "shelf_icon.icns"
ICONSET_DIR = ROOT / "build" / "icon.iconset"


def main() -> int:
    app = QGuiApplication([])
    renderer = QSvgRenderer(QByteArray(SVG_PATH.read_bytes()))
    if not renderer.isValid():
        raise SystemExit("Invalid SVG icon")

    ICONSET_DIR.mkdir(parents=True, exist_ok=True)
    for path in ICONSET_DIR.glob("*.png"):
        path.unlink()

    for size in [16, 32, 128, 256, 512]:
        image = QImage(size, size, QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.transparent)
        painter = QPainter(image)
        renderer.render(painter, QRectF(0, 0, size, size))
        painter.end()
        image.save(str(ICONSET_DIR / f"icon_{size}x{size}.png"))

        retina = QImage(size * 2, size * 2, QImage.Format.Format_ARGB32)
        retina.fill(Qt.GlobalColor.transparent)
        retina_painter = QPainter(retina)
        renderer.render(retina_painter, QRectF(0, 0, size * 2, size * 2))
        retina_painter.end()
        retina.save(str(ICONSET_DIR / f"icon_{size}x{size}@2x.png"))

    try:
        from PIL import Image
    except ModuleNotFoundError:
        pass
    else:
        source = Image.open(ICONSET_DIR / "icon_512x512@2x.png")
        source.save(
            ICNS_PATH,
            format="ICNS",
            sizes=[(16, 16), (32, 32), (64, 64), (128, 128), (256, 256), (512, 512), (1024, 1024)],
        )

    app.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
