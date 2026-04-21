from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QByteArray, QRectF, Qt
from PySide6.QtGui import QGuiApplication, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer


ROOT = Path(__file__).resolve().parents[1]
SVG_PATH = ROOT / "src" / "shelf" / "ui" / "assets" / "shelf_icon.svg"
ICONSET_DIR = ROOT / "build" / "icon.iconset"


def main() -> int:
    app = QGuiApplication([])
    renderer = QSvgRenderer(QByteArray(SVG_PATH.read_bytes()))
    if not renderer.isValid():
        raise SystemExit("Invalid SVG icon")

    ICONSET_DIR.mkdir(parents=True, exist_ok=True)
    for path in ICONSET_DIR.glob("*.png"):
        path.unlink()

    for size in [16, 32, 64, 128, 256, 512, 1024]:
        image = QImage(size, size, QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.transparent)
        painter = QPainter(image)
        renderer.render(painter, QRectF(0, 0, size, size))
        painter.end()
        image.save(str(ICONSET_DIR / f"icon_{size}x{size}.png"))

        if size != 1024:
            retina = image.scaled(
                size * 2,
                size * 2,
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            retina.save(str(ICONSET_DIR / f"icon_{size}x{size}@2x.png"))

    app.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
