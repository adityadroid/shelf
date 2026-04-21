set shell := ["zsh", "-cu"]

default:
    @just --list

sync:
    uv sync

build-icon:
    rm -rf build/icon.iconset && mkdir -p build/icon.iconset
    uv run python tools/build_icon.py
    iconutil -c icns "build/icon.iconset" -o "src/shelf/ui/assets/shelf_icon.icns"

run *args:
    uv run shelf {{args}}

gui:
    uv run shelf

test:
    uv run pytest

status:
    uv run shelf status

audit:
    uv run shelf audit

rebuild-all:
    uv run shelf rebuild-all

rebuild-fts:
    uv run shelf rebuild-fts

reindex-path path:
    uv run shelf reindex-path {{path}}

reindex-folder path:
    uv run shelf reindex-folder {{path}}

build-app: build-icon
    uv run pyinstaller --clean --noconfirm Shelf.spec

open-app: build-app
    open dist/Shelf.app

clean:
    rm -rf build dist .pytest_cache .mypy_cache
