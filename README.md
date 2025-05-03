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

### 🎬 Demo Videos

- [Video 1 ansehen](https://www.youtube.com/watch?v=vM62S5MKWBc)
- [Video 2 ansehen](https://www.youtube.com/watch?v=KcUHHAOiDZ0)
- [Video 3 ansehen](https://www.youtube.com/watch?v=qECRFLr1UVA)

---

### 💡 Hintergrund & Idee

Die ursprüngliche Idee hinter diesem Projekt war es, einen funktionierenden Downloader für die Plattform [`https://aniworld.to`](https://aniworld.to) zu entwickeln. Der Grund dafür war, dass viele der aktuell auf GitHub verfügbaren Tools Probleme beim Herunterladen von VOE-Streams haben. 

Das liegt daran, dass VOE kürzlich die Art und Weise geändert hat, wie ihre Videolinks verarbeitet und ausgeliefert werden. Die meisten bestehenden Downloader wurden seitdem nicht aktualisiert und unterstützen weder die neue Struktur von VOE noch andere aktuelle Streaming-Anbieter.

Aus dieser Motivation entstand zuerst der Scraper und der DownloadHelper. Während der Entwicklung kam jedoch die Idee auf, nicht nur ein einzelnes Tool zu bauen, sondern gleich eine offene Plattform zu schaffen:

> 🧩 Ein flexibles System, mit dem die Community eigene Apps entwickeln, austauschen und erweitern kann.

Durch den integrierten App-Manager lassen sich eigene Tools direkt ins System einbinden oder herunterladen. Entwickler:innen können ihre Anwendungen teilen oder mir zukommen lassen – auf Wunsch hoste ich sie zentral, sodass andere Nutzer:innen direkt darauf zugreifen können.

So soll ein gemeinschaftlich nutzbares System entstehen, das offen für Erweiterungen ist – von Downloadern bis hin zu ganz anderen Tools.

---

### 📜 Lizenz & Nutzungshinweis

‼️ Falls du dieses System nutzt oder weiterverbreitest, bist du dazu verpflichtet:

- einen klar sichtbaren Verweis auf diese GitHub-Seite anzugeben  
- das Projekt unter der Lizenz [GNU General Public License v3.0](https://www.gnu.org/licenses/gpl-3.0.de.html) zu kennzeichnen  
- sowie die unten genannten Mitwirkenden korrekt zu nennen

#### 👤 Mitwirkende:
- Madusanka2013 (Projektmitarbeit, Entwicklungsideen)

Danke, dass du dieses Projekt respektierst und zur weiteren Entwicklung beiträgst!



