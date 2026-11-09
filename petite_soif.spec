# -*- mode: python ; coding: utf-8 -*-
# Build : python -m PyInstaller --noconfirm petite_soif.spec   (ou build.bat)
# Mode "dossier" (onedir) : moins de faux positifs antivirus, DLL Qt remplaçables (LGPL).
import shutil
from pathlib import Path

ROOT = Path(SPECPATH)
EXCLUDES = [
    "tkinter", "unittest", "pydoc", "PySide6.QtMultimedia", "PySide6.QtNetwork",
    "PySide6.QtQml", "PySide6.QtQuick", "PySide6.QtSql", "PySide6.QtOpenGL",
    "PySide6.QtPdf", "PySide6.QtTest", "PySide6.QtDBus",
    "socket", "_socket", "ssl", "_ssl",  # l'appli n'ouvre aucune connexion : ni ces modules, ni leurs DLL OpenSSL
]

a = Analysis([str(ROOT / "petite_soif.pyw")], pathex=[str(ROOT)], excludes=EXCLUDES, noarchive=False,
             datas=[(str(ROOT / "assets" / "fonts"), "assets/fonts")])
# Moteur OpenGL logiciel de secours de Qt (19,7 Mo) : l'appli dessine en raster (QPainter) et n'utilise pas OpenGL
a.binaries = [b for b in a.binaries if "opengl32sw" not in b[0].lower()]
# Qt Network et le seul plugin Qt qui en dépend (entrée tactile TUIO, par réseau) : inutiles, retirés
a.binaries = [b for b in a.binaries if not any(k in b[0].lower() for k in ("qt6network", "qtuiotouchplugin"))]

# Infos de version de l'exe (Propriétés > Détails), lues dans soif/config.py pour rester alignées avec le tag
import re
from PyInstaller.utils.win32.versioninfo import (FixedFileInfo, StringFileInfo, StringStruct, StringTable, VarFileInfo,
                                                 VarStruct, VSVersionInfo)
VERSION = re.search(r'__version__ = "([\d.]+)"', (ROOT / "soif" / "config.py").read_text(encoding="utf-8")).group(1)
vt = tuple((list(map(int, VERSION.split("."))) + [0, 0, 0])[:4])
info = VSVersionInfo(
    ffi=FixedFileInfo(filevers=vt, prodvers=vt, mask=0x3F, flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0),
    kids=[StringFileInfo([StringTable("040C04B0", [
        StringStruct("FileDescription", "Petite Soif"), StringStruct("FileVersion", VERSION),
        StringStruct("InternalName", "PetiteSoif"), StringStruct("OriginalFilename", "PetiteSoif.exe"),
        StringStruct("ProductName", "Petite Soif"), StringStruct("ProductVersion", VERSION),
        StringStruct("LegalCopyright", "MIT licence - github.com/TylerVae/petite-soif")])]),
          VarFileInfo([VarStruct("Translation", [0x040C, 1200])])])
Path(SPECPATH, "build").mkdir(exist_ok=True)
VERSION_FILE = Path(SPECPATH, "build", "version_info.txt")
VERSION_FILE.write_text(str(info), encoding="utf-8")
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [], exclude_binaries=True, name="PetiteSoif",
    console=False, icon=str(ROOT / "assets" / "icon.ico"), upx=False, version=str(VERSION_FILE),
)
coll = COLLECT(exe, a.binaries, a.datas, name="PetiteSoif", upx=False)

# Licences à côté de l'exe (obligatoire pour redistribuer Qt et Python)
out = Path(DISTPATH) / "PetiteSoif"
for f in ("LICENSE", "THIRD_PARTY_NOTICES.md"):
    shutil.copy2(ROOT / f, out / f)
shutil.copytree(ROOT / "LICENSES", out / "LICENSES", dirs_exist_ok=True)
