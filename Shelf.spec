# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules


ICON_PATH = "src/shelf/ui/assets/shelf_icon.icns"
CHROMA_HIDDEN_IMPORTS = sorted(
    set(collect_submodules("chromadb.telemetry") + collect_submodules("chromadb.api"))
)
EXCLUDES = [
    "sentence_transformers",
    "transformers",
    "torch",
    "torchvision",
    "torchaudio",
    "onnxruntime",
    "sklearn",
    "scipy",
    "pytest",
    "py",
    "test",
    "tests",
]


a = Analysis(
    ["src/shelf/__main__.py"],
    pathex=["src"],
    binaries=[],
    datas=[("src/shelf/ui/assets", "shelf/ui/assets")],
    hiddenimports=CHROMA_HIDDEN_IMPORTS,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=EXCLUDES,
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Shelf",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="Shelf",
)

app = BUNDLE(
    coll,
    name="Shelf.app",
    icon=ICON_PATH,
    bundle_identifier="com.shelf.app",
    info_plist={
        "CFBundleDisplayName": "Shelf",
        "CFBundleName": "Shelf",
        "CFBundleShortVersionString": "0.1.0",
        "CFBundleVersion": "0.1.0",
        "NSPrincipalClass": "NSApplication",
    },
)
