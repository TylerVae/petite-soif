# Petite Soif : consignes pour Claude Code

Ce fichier est public (il est dans le repo). Il ne doit contenir **aucune donnée personnelle**.
Le contexte de session et les tâches en cours sont dans `HANDOFF.md` (non publié, ignoré par git).

## Le projet
Appli Windows (Python 3 + PySide6-Essentials) : une fleur en pot toujours au premier plan qui
rappelle de boire de l'eau. Distribuée en `.exe` (PyInstaller, mode dossier) via les GitHub Releases.

## Phase actuelle
v1.0.0 publiée (repo public + Release). Correctifs éventuels en `v1.0.x`, nouveautés en V2 (détail dans
`HANDOFF.md` en local). Chaque session lit `HANDOFF.md` au début et le met à jour à la fin.

## Workflow git
- `main` reste toujours publiable. Chaque chantier (V2 : paramètres, visuels, sons…) se fait sur sa
  propre branche, fusionnée dans `main` une fois testée. Le rappeler au mainteneur en début de chantier.
- Publier = aligner `__version__`, tagger `vX.Y.Z`, pousser le tag (le workflow crée la Release).
- Tout push, tag ou changement de réglage du repo GitHub se fait après un "go" explicite.

## Architecture
- `petite_soif.pyw` : point d'entrée.
- `soif/main.py` : contrôleur (timer, escalade, absence, ne pas déranger, tray, raccourci global).
- `soif/flower.py` : fenêtre de la fleur (modes home/follow/dock/hold/poof, particules, gestes souris).
- `soif/painter.py` : dessin vectoriel QPainter de la fleur classique ; dispatche vers `plantes.py` pour les autres plantes.
- `soif/plantes.py` : les autres plantes, dessinées en SVG paramétré (soif 0..3 + sommeil) et rendues par QtSvg avec un cache.
  Le choix se fait dans `config.json` (clé `plante`) ou dans Paramètres > Ma plante. Ne jamais nommer les plantes dans le README,
  le changelog ni les visuels publics : les découvrir fait partie du jeu.
- `soif/popup.py` : pop-up clic droit (total, objectif, +50 cl, 7 jours).
- `soif/storage.py` : SQLite, une "journée" commence à `heure_reset` (6 h).
- `soif/sounds.py` : sons synthétisés + lecture `winsound` (volume via copies atténuées dans `sons/.cache`).
- `soif/winapi.py` : `GetLastInputInfo`, `RegisterHotKey`, `SetWindowPos(HWND_TOPMOST)`, clé `Run` du registre.
- `soif/config.py` : chemins, défauts, `__version__`.

## Règles non négociables
1. **Vie privée.** Toutes les données utilisateur vont dans `%APPDATA%\PetiteSoif\`, jamais dans
   le dossier du code. Aucun appel réseau dans l'appli. Ne jamais lire le contenu des frappes clavier.
   *Pourquoi :* « rien ne quitte ton ordinateur » est la promesse du README. Elle évite tout serveur, toute donnée personnelle à protéger,
   toute panne réseau et réduit les faux positifs antivirus. Ouvrir une page dans le navigateur (lien GitHub) n'est pas un appel réseau de l'appli.
   Si on la révise un jour (ex. vérification de mise à jour), ce doit être une décision du mainteneur : désactivée par défaut, annoncée dans le README.
2. **Avant chaque commit**, vérifier qu'aucun de ces éléments n'est indexé : `config.json`, `donnees/`,
   `sons/`, `*.db`, `*.log`, `*.csv`, `HANDOFF.md`, chemins `C:\Users\…`, adresse e-mail, nom réel, token.
   Commande : `git diff --cached --name-only` puis une recherche de ces motifs dans le diff.
3. **Jamais de push automatique.** Montrer le diff, attendre un "go" explicite du mainteneur, puis pousser.
4. **Release = tag.** `__version__` dans `soif/config.py` doit correspondre au tag (`v1.0.0` ↔ `1.0.0`).
   Le workflow `.github/workflows/release.yml` construit et publie l'exe quand un tag `v*` est poussé.
5. **Dépendances figées** dans `requirements*.txt`. Pas de nouvelle dépendance sans le signaler
   (licence + poids + justification). Ne pas réintroduire QtMultimedia (licence FFmpeg, poids).
6. **Licences.** Garder `LICENSE`, `THIRD_PARTY_NOTICES.md` et `LICENSES/` à jour et copiés à côté
   de l'exe (le `.spec` le fait).
7. Ne jamais ajouter de moyen de paiement ni activer de service payant (runners "larger", etc.).

## Commandes
- Tests : `.venv\Scripts\python -m unittest discover -s tests -t .` (Qt hors écran, données dans un dossier temporaire ;
  aucune dépendance en plus). Ils tournent aussi en CI à chaque pull request et push sur `main` (`.github/workflows/tests.yml`, lecture seule).
- Lancer depuis le code : `py -m pip install -r requirements.txt` puis `pyw petite_soif.pyw`
- Build local : `build.bat` → `dist\PetiteSoif\PetiteSoif.exe`
- Régénérer l'icône : `py tools\make_icon.py`
- Régénérer les GIF du README : `.venv\Scripts\python tools\make_demo.py en` puis `fr` (Pillow requis, outil de dev seulement) ;
  l'image des états : `.venv\Scripts\python tools\make_etats.py`. Ces trois outils ne montrent que la fleur classique.
- Régénérer l'aperçu social : `.venv\Scripts\python tools\make_social.py` → `docs\petite_soif_vX.Y.Z_cover.png`
  (non versionné), à téléverser à la main dans Settings > Social preview à chaque nouvelle version.

## Façon de travailler avec le mainteneur
- Répondre en français, termes anglais acceptés quand ils sont plus précis.
- Poser toutes les questions de clarification nécessaires, challenger les idées, proposer des alternatives.
- Pas de flatterie. Pas de "genre" comme tic de langage.
- Conditionnel pour tout fait externe non recoupé par deux sources fiables.
- Récaps "quoi faire" : courts, une ligne par sujet.
