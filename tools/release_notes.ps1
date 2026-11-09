# Notes de Release : section du CHANGELOG pour ce tag + mode d'emploi + empreinte SHA-256.
# Usage (appelé par release.yml) : pwsh tools/release_notes.ps1 v2.0.0 PetiteSoif-v2.0.0-windows.zip > notes.md
param([string]$Tag, [string]$Zip)
$ver = $Tag.TrimStart('v')
$out = @()
$in = $false
foreach ($l in (Get-Content CHANGELOG.md -Encoding UTF8)) {
    if ($l -match '^## ') { $in = $l.StartsWith("## $ver"); continue }
    if ($in) { $out += $l }
}
if (-not ($out -join '').Trim()) { throw "Section $ver introuvable dans CHANGELOG.md" }
$sha = (Get-Content "$Zip.sha256" -Raw).Trim()
($out -join "`n").Trim()
@"


---

## Install
1. Download ``$Zip`` below and extract it.
2. Run ``PetiteSoif.exe``. To update from an older version: quit it from the tray icon first. Your settings and history are kept.

**"Windows protected your PC"?** The exe is not digitally signed (a certificate apparently costs about `$200 a year), so Windows shows this screen for any program it doesn't know yet. Click **More info -> Run anyway**. You can check the download yourself: the code is public, GitHub builds the exe from it, and the SHA-256 of the zip is:

``$sha``
"@
