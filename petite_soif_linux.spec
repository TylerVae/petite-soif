# -*- mode: python ; coding: utf-8 -*-
# Build Linux EXPÉRIMENTAL : python -m PyInstaller --noconfirm petite_soif_linux.spec   (voir tools/build_linux.sh)
# Mode "dossier" (onedir). Pas de QtDBus exclu ici : Qt s'en sert pour l'icône de la zone de notification.
import shutil
from pathlib import Path

ROOT = Path(SPECPATH)
EXCLUDES = [
    "tkinter", "unittest", "pydoc", "PySide6.QtMultimedia", "PySide6.QtNetwork",
    "PySide6.QtQml", "PySide6.QtQuick", "PySide6.QtSql", "PySide6.QtOpenGL",
    "PySide6.QtPdf", "PySide6.QtTest",
    "socket", "_socket", "ssl", "_ssl",  # aucune connexion réseau dans l'appli
]

a = Analysis([str(ROOT / "petite_soif.pyw")], pathex=[str(ROOT)], excludes=EXCLUDES, noarchive=False,
             datas=[(str(ROOT / "assets" / "fonts"), "assets/fonts")])
a.binaries = [b for b in a.binaries if not any(k in b[0].lower() for k in ("qt6network", "qtuiotouchplugin"))]
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="PetiteSoif", console=False, upx=False)
coll = COLLECT(exe, a.binaries, a.datas, name="PetiteSoif", upx=False)

out = Path(DISTPATH) / "PetiteSoif"
for f in ("LICENSE", "THIRD_PARTY_NOTICES.md"):
    shutil.copy2(ROOT / f, out / f)
shutil.copy2(ROOT / "docs" / "LINUX.md", out / "LINUX.md")
shutil.copytree(ROOT / "LICENSES", out / "LICENSES", dirs_exist_ok=True)
