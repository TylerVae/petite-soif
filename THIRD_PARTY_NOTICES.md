# Composants tiers

Le code de Petite Soif est sous licence MIT (voir `LICENSE`).
La version `.exe` embarque les composants suivants, chacun sous sa propre licence :

| Composant | Rôle | Licence | Source |
|---|---|---|---|
| Qt 6 / PySide6 (Essentials) + Shiboken6 | Fenêtres, dessin, icône de notification | LGPL-3.0 (`LICENSES/LGPL-3.0-only.txt`, qui renvoie à `LICENSES/GPL-3.0-only.txt`) | https://code.qt.io/cgit/pyside/pyside-setup.git · https://download.qt.io/official_releases/QtForPython/ |
| Python 3 | Interpréteur embarqué | PSF License 2.0 (`LICENSES/PSF-2.0.txt`) | https://www.python.org/downloads/source/ |
| Baloo 2 (police) | Titres de la fenêtre de paramètres | SIL Open Font License 1.1 (`LICENSES/OFL-1.1-Baloo2.txt`) | https://github.com/EkType/Baloo2 |
| PyInstaller (bootloader) | Lanceur du `.exe` | GPL-2.0 avec exception explicite autorisant la distribution de programmes compilés sous n'importe quelle licence | https://github.com/pyinstaller/pyinstaller |

## Qt et la LGPL
Qt est utilisé **sans modification**, sous forme de bibliothèques dynamiques (`.dll`)
livrées séparément dans le dossier `_internal/` de l'application.
Tu peux donc remplacer ces fichiers par ta propre version de Qt/PySide6 compatible
(même version majeure), ce que la LGPL-3.0 exige de rendre possible.
Les sources exactes de la version utilisée (PySide6 6.11.2) sont disponibles aux adresses ci-dessus.

Les sons sont générés par le programme lui-même (aucun fichier audio tiers).
