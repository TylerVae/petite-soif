#!/bin/sh
# Build Linux EXPÉRIMENTAL -> PetiteSoif-linux-x86_64.tar.gz + .sha256 (à lancer depuis la racine du repo).
# Pour une compatibilité large, lancer sur une distribution ANCIENNE (glibc 2.28 : AlmaLinux 8, comme le workflow CI).
set -eu
python3 -m PyInstaller --noconfirm --clean petite_soif_linux.spec
name="${1:-PetiteSoif-linux-x86_64}"
tar -C dist -czf "$name.tar.gz" PetiteSoif
sha256sum "$name.tar.gz" > "$name.tar.gz.sha256"
cat "$name.tar.gz.sha256"
