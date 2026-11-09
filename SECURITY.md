# Security policy / Politique de sécurité

## English

Petite Soif is a small free desktop app. It never connects to the internet, keeps all its data in `%APPDATA%\PetiteSoif\`
and never reads what you type (it only asks Windows how long ago the last keyboard or mouse activity was).

### Reporting a vulnerability

Please **do not post the details in a public issue**.

1. Go to the **Security** tab of this repository and click **Report a vulnerability** (private report, only the maintainer sees it).
2. If that button is missing, open a [Discussion](../../discussions) saying that you found a security problem, **without any detail**,
   and a private way to talk will be arranged.

This is a one-person hobby project: expect an answer within about a week, best effort, no bug bounty.

### What counts

- the app sending any data over the network, or reading what you type;
- a crafted `config.json`, history file or setting that makes the app run code or write outside `%APPDATA%\PetiteSoif\`;
- a release file whose SHA-256 does not match the one published with the release.

### What does not count

- the Windows SmartScreen warning ("Windows protected your PC"): the exe is not signed (see the README);
- an antivirus flagging the exe: this happens with apps packaged with PyInstaller, please also report it to the antivirus vendor.

### Supported versions

Only the latest release gets fixes.

## Français

Petite Soif est une petite appli de bureau gratuite. Elle ne se connecte jamais à internet, garde toutes ses données dans
`%APPDATA%\PetiteSoif\` et ne lit jamais ce que tu tapes (elle demande seulement à Windows depuis combien de temps il n'y a pas eu d'activité).

### Signaler une faille

**Ne publie pas les détails dans une issue publique.**

1. Va dans l'onglet **Security** du dépôt et clique sur **Report a vulnerability** (signalement privé, seul le mainteneur le voit).
2. Si ce bouton n'existe pas, ouvre une [Discussion](../../discussions) pour dire que tu as trouvé un problème de sécurité, **sans aucun détail** :
   un moyen privé d'échanger sera proposé.

Projet perso tenu par une seule personne : réponse sous environ une semaine, au mieux, sans prime.

### Ce qui compte

- l'appli qui envoie des données sur le réseau, ou qui lit ce que tu tapes ;
- un `config.json`, un historique ou un réglage fabriqué qui fait exécuter du code ou écrire en dehors de `%APPDATA%\PetiteSoif\` ;
- un fichier de release dont l'empreinte SHA-256 ne correspond pas à celle publiée avec la release.

### Ce qui ne compte pas

- l'avertissement SmartScreen (« Windows a protégé votre ordinateur ») : l'exe n'est pas signé (voir le README) ;
- un antivirus qui signale l'exe : ça arrive avec les applis empaquetées par PyInstaller, signale-le aussi à l'éditeur de l'antivirus.

### Versions prises en charge

Seule la dernière release reçoit des correctifs.
