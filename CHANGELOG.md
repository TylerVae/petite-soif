# Changelog

## 2.0.0

The big one: a real settings window, a language switch, and XP to unlock new plants for your pot.

### New
- **Settings window** ("Carnet" style, 6 tabs): Reminders, Hydration, Flower & sound, My plant, System, About.
  Everything applies right away, nothing to save. Reachable from the pot (hover → ⚙), the pop-up and the tray icon.
- **Insistence**: *Gentle*, *Normal* or *Pushy* (the flower circles around your cursor).
- **Language switch FR | EN** at the bottom left of the settings window; the choice is saved and also applies to the pop-up
  and the tray menu. On first launch the language follows Windows. The app version is shown next to the switch.
- **My plant**: every sip earns XP (+5 first sip of the day, +1 per sip, +3 per glass). Every 200 XP unlocks a new plant
  (ten to discover, each with its own way of getting thirsty and of falling asleep: no spoilers here).
  Pick the plant that lives in your pot from the shelf; the next one stays a "?" until you earn it.
  XP is computed from your local history, nothing extra is stored.
- **Unlock everything** switch in **My plant** (with a confirmation): turns XP off and makes every plant available.
  Reversible at any time, your XP is never lost.
- **+XP pop** above the flower after each sip, and a **"New plant!"** label (with a little shake) that stays above the flower until you open **My plant**.
- **News dot**: a red dot on the pop-up gear and the "My plant" tab when something is new.
- **Do not disturb button** (💤 / 🔔) when you hover the pot and in the right-click pop-up, next to the settings gear: one click = 30 minutes, 🔔 to resume (other durations in the tray menu).
- **Icons follow your plant**: tray icon, taskbar and settings window show the plant in your pot.
- **Report a bug** link always visible at the bottom left of the settings window and in the tray menu; it opens a pre-filled GitHub bug form.
- **Check for updates** link in Settings → About (opens the Releases page in your browser; the app itself never connects to anything).
- **Keyboard shortcut field** with a bigger, centred keyboard icon.
- **Sliders** with an audible tick; softer and lower UI sounds (drop, water).
- README in English first, French below, with a bilingual demo.

### Changed
- Pop-up redesigned to match the settings window (colours, rounded corners, bigger green settings button).
- Small text is now **Segoe UI** (system font, crisp on Windows); titles and labels stay in **Baloo 2**.
  DM Sans was removed (licence file and notice too).
- Sleeping "Z"s now rise from the pot instead of above the head.
- While asleep ("Do not disturb"), the flower only redraws 4 times per second to stay light on your CPU.
- The plants are vector drawings rendered with Qt's SVG module (already part of PySide6, about 0.7 MB more on disk).

### Fixed
- A hand-edited `config.json` with an absurd value (size 0, volume 7, text instead of a number…) no longer breaks the app: the value is clamped or reset.
- The history database now carries a schema version, to make future updates safe.
- When updating from V1 (a config without language), the language now follows Windows instead of staying French.
- The exe now carries its version and description (right-click → Properties → Details).
- The exe no longer ships unused network code (Qt Network, Python socket and OpenSSL): about 4 MB lighter.
- The first-launch question, the "already running" message and the pre-filled bug report are now translated.

### Privacy (unchanged)
No network calls, all data stays in `%APPDATA%\PetiteSoif\`, keystrokes are never read.

## 1.0.0
First public release: the thirsty flower, escalating reminders, daily goal, history, tray icon, Windows startup.
