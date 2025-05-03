## 🖥️ Windows-ähnliches GUI-Framework in Python

Dieses Python-basierte Projekt bietet eine benutzerfreundliche, an Windows angelehnte grafische Oberfläche (GUI), in der eigene Anwendungen entwickelt und integriert werden können. Die Umgebung unterstützt die einfache Erweiterung durch benutzerdefinierte Apps und eignet sich hervorragend als Grundlage für eigene GUI-Projekte.

---

### 🔧 Voraussetzungen

Damit das Programm ordnungsgemäß funktioniert, müssen folgende Komponenten installiert bzw. vorhanden sein:

#### 📦 Externe Tools
- [`ffmpeg.exe`](https://ffmpeg.org/)
- `ffprobe.exe`  
> Beide Dateien müssen entweder im Systempfad verfügbar sein oder sich im gleichen Verzeichnis wie das Hauptprogramm befinden.

#### 🐍 Python-Abhängigkeiten

Stelle sicher, dass folgende Python-Pakete installiert sind:

```bash
pip install selenium
pip install selenium-wire
pip install pillow
pip install bs4
pip install setuptools
```

### 📁 App-Manager & Beispiel-Apps

Das System enthält einen **App-Manager**, über den vorinstallierte Programme direkt gestartet werden können. Außerdem steht eine **Template-Datei** zur Verfügung, mit der du ganz einfach eigene Apps für die Umgebung entwickeln kannst.

#### Enthaltene Beispiel-Apps:

- **Scraper-App**  
  Diese App kann von der Website [`https://aniworld.to`](https://aniworld.to) automatisch **VOE-Links** zu Anime-Episoden extrahieren.

  > ⚠️ Hinweis:  
  > Aktuell unterstützt der Scraper keine Sprachauswahl.  
  > Er wählt automatisch die **ersten verfügbaren VOE-Links** aus.  
  > Das bedeutet:
  > - Wenn eine Folge auf **Deutsch (Dub)** verfügbar ist, wird diese verwendet.  
  > - Gibt es keine deutsche Version, wird automatisch die **Ger-Sub-Version** verwendet (deutsche Untertitel).

- **DownloadHelper**  
  Mit dieser Anwendung können die gescrapten **VOE-Videolinks** direkt heruntergeladen werden.

---

### ⚠️ Hinweis

Ich bin noch **Anfänger in der Python-Entwicklung**. Viele Funktionen sind experimentell, und es können noch **Fehler oder unerwartetes Verhalten** auftreten.  
Ich freue mich über Feedback, Verbesserungsvorschläge oder Pull Requests!
