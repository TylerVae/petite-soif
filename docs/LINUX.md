# Petite Soif sous Linux (EXPÉRIMENTAL)

Version **expérimentale** pour session **X11** (testée au mieux : Linux Mint). XWayland peut fonctionner ; **Wayland pur n'est pas pris en charge**
(pas de fleur toujours au premier plan, pas de poursuite du curseur). Rien ne quitte ton ordinateur : aucune connexion réseau, comme sous Windows.

## Ce qui marche / ne marche pas
| | Linux (X11) |
|---|---|
| Fleur au premier plan | oui (indication « toujours au premier plan » du gestionnaire de fenêtres) |
| Rappels, escalade, popup, paramètres | oui |
| Inactivité clavier/souris | oui avec `libXss` (paquet `libxss1`) ; sinon repli souris seule et **5 rappels répétés au maximum** entre deux gorgées |
| Lancement au démarrage | oui, via `~/.config/autostart/petite-soif.desktop` |
| Sons | oui, via `paplay`, `pw-play` ou `aplay` (le premier trouvé) ; aucun son si aucun n'est installé |
| Raccourci global | **pas encore** (« Récupérer la fleur » reste dans le menu de l'icône) |
| Données | `~/.config/PetiteSoif/` (jamais dans le dossier de l'appli) |

## Installer et lancer (archive)
```bash
tar xzf PetiteSoif-linux-x86_64.tar.gz
sudo apt install libxcb-cursor0 libxss1     # Mint / Ubuntu / Debian ; libxss1 est facultatif
./PetiteSoif/PetiteSoif
```
Vérifier le téléchargement : `sha256sum -c PetiteSoif-…tar.gz.sha256`.

## Lancer depuis le code (sans archive)
```bash
git checkout linux-x11
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python petite_soif.pyw
```

## Construire l'archive soi-même
```bash
pip install -r requirements-build.txt
sh tools/build_linux.sh          # -> PetiteSoif-linux-x86_64.tar.gz + .sha256
```
Pour une compatibilité large, construire sur une distribution ancienne : le workflow `release-linux.yml` utilise AlmaLinux 8 (glibc 2.28).
Un build fait sur une distribution récente ne démarrera pas sur une plus ancienne.

## Check-list de test (Mint, session X11)
1. `echo $XDG_SESSION_TYPE` → doit afficher `x11`.
2. Lancer l'appli : la fleur apparaît, reste au-dessus des autres fenêtres, l'icône est dans la zone de notification.
3. Clic droit : popup ; clic gauche maintenu : « gorgée » (son + XP).
4. Régler les rappels à 1 / 2 / 3 minutes (Paramètres) et vérifier l'escalade, les sons, la poursuite du curseur.
5. Ne plus toucher clavier/souris 3 min : la fleur doit venir t'attendre (inactivité détectée). Si elle ne le fait jamais, `libxss1` manque.
6. Paramètres > Système > « Lancer au démarrage » : le fichier `~/.config/autostart/petite-soif.desktop` doit apparaître, puis disparaître en décochant. Se déconnecter/reconnecter pour vérifier.
7. Polices : le texte doit être lisible (Noto Sans / DejaVu Sans à défaut de Segoe UI) ; l'emoji ⚙️ doit s'afficher.
8. Vérifier que `~/.config/PetiteSoif/` contient config.json et `donnees/`, et que le dossier de l'appli ne contient rien de nouveau.
9. Noter tout écart (distribution, version, X11/Wayland, message d'erreur dans `~/.config/PetiteSoif/donnees/erreurs.log`) pour le rapport.

## Limites connues
- Jamais exécutée sous Linux par son auteur au moment de l'écriture : elle a été préparée depuis Windows, seuls les tests communs y ont tourné.
- Sans zone de notification (certains environnements GNOME sans extension), l'icône est absente : lancer l'appli depuis un terminal pour la quitter avec Ctrl+C.
- La mise en page des paramètres est calée sur Segoe UI : de légers décalages sont possibles avec d'autres polices.
