# Asset Placeholders

Lege deine Dateien in die jeweiligen Ordner. Die App lädt sie automatisch
wenn sie vorhanden sind — andernfalls greift ein Emoji/Text-Fallback.

---

## assets/  (App-weite Bilder)

| Datei       | Größe     | Verwendung                                          |
|-------------|-----------|-----------------------------------------------------|
| icon.ico    | multi-res | Windows EXE-Icon (Taskleiste, Explorer) — Vorrang   |
| icon.png    | 256×256   | App-Icon, Fallback wenn keine .ico vorhanden        |
| splash.png  | 420×180   | Splash-Screen beim Start                            |
| logo.png    | ≥ 40 px H | Logo im Onboarding-Wizard (wird auf 40 px skaliert) |

---

## assets/icons/  (Kategorie- und Status-Icons, alle PNG)


### Status-Icons

| Datei      | Empf. Größe | Fallback | Verwendung                              |
|------------|-------------|----------|-----------------------------------------|
| check.png  | 16×16       | ✓        | Dependency-Check: Erfolg                |
| error.png  | 16×16       | ✗        | Dependency-Check: Fehler                |

### Onboarding-Step-Icons

| Datei        | Empf. Größe | Fallback | Verwendung                              |
|--------------|-------------|----------|-----------------------------------------|
| shop.png     | 32×32       | 🛒       | „Plugin Shop öffnen"-Schritt + Leerseite |
| download.png | 32×32       | ⬇        | „Plugin installieren"-Schritt           |
| play.png     | 32×32       | ▶        | „Dateien konvertieren"-Schritt          |

---

## Hinweise

- Alle Icons werden automatisch auf die Zielgröße skaliert (SmoothTransformation).
- Transparenter Hintergrund (PNG mit Alpha) wird empfohlen.
- Fehlende Dateien führen **nicht** zu Fehlern — der Emoji-Fallback wird genutzt.
- Für Plugin-eigene Icons: `PluginMeta.icon_name = "mein_icon"` → `assets/icons/mein_icon.png`
