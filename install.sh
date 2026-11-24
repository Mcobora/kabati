#!/usr/bin/env bash
set -e
mkdir -p ~/.local/bin ~/.local/share/icons/hicolor/scalable/apps ~/.local/share/applications
install -m 755 kabati/main.py ~/.local/bin/kabati
install -m 644 assets/kabati.svg ~/.local/share/icons/hicolor/scalable/apps/kabati.svg
install -m 644 kabati.desktop ~/.local/share/applications/kabati.desktop
