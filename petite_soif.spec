# -*- mode: python ; coding: utf-8 -*-
# Build : python -m PyInstaller --noconfirm petite_soif.spec   (ou build.bat)
# Mode "dossier" (onedir) : moins de faux positifs antivirus, DLL Qt remplaçables (LGPL).
import shutil
from pathlib import Path

ROOT = Path(SPECPATH)
EXCLUDES = [
    "tkinter", "unittest", "pydoc", "PySide6.QtMultimedia", "PySide6.QtNetwork",
    "PySide6.QtQml", "PySide6.QtQuick", "PySide6.QtSql", "PySide6.QtOpenGL",
    "PySide6.QtPdf", "PySide6.QtSvg", "PySide6.QtTest", "PySide6.QtDBus",
]

a = Analysis([str(ROOT / "petite_soif.pyw")], pathex=[str(ROOT)], excludes=EXCLUDES, noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [], exclude_binaries=True, name="PetiteSoif",
    console=False, icon=str(ROOT / "assets" / "icon.ico"), upx=False,
)
coll = COLLECT(exe, a.binaries, a.datas, name="PetiteSoif", upx=False)

# Licences à côté de l'exe (obligatoire pour redistribuer Qt et Python)
out = Path(DISTPATH) / "PetiteSoif"
for f in ("LICENSE", "THIRD_PARTY_NOTICES.md"):
    shutil.copy2(ROOT / f, out / f)
shutil.copytree(ROOT / "LICENSES", out / "LICENSES", dirs_exist_ok=True)
