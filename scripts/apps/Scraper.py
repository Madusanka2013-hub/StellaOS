import tkinter as tk
from tkinter import scrolledtext
from tkinter import ttk
import threading
import os
import re
import httpx
from bs4 import BeautifulSoup

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
shutdown_event = threading.Event()
staffel_info = {}

def num(s):
    return int(re.search(r'\d+', s).group())

def ensure_folder(path):
    os.makedirs(path, exist_ok=True)

def extract_anime_name(url):
    match = re.search(r'/stream/([^/]+)', url) or re.search(r'/serie/stream/([^/]+)', url)
    return match.group(1).replace('-', ' ').title() if match else "Unbekannt"

def scrape_staffeln(url, base_url, cover_folder):
    try:
        global staffel_info
        with httpx.Client() as client:
            response = client.get(url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')

            cover_div = soup.find('div', class_='seriesCoverBox')
            if cover_div:
                img_tag = cover_div.find('img')
                if img_tag and img_tag.get('data-src'):
                    cover_url = base_url + img_tag['data-src']
                    ensure_folder(cover_folder)
                    cover_path = os.path.join(cover_folder, 'cover.jpg')
                    if not os.path.exists(cover_path):
                        cover_data = client.get(cover_url, headers=headers).content
                        with open(cover_path, 'wb') as f:
                            f.write(cover_data)

            stream_div = soup.find('div', {'id': 'stream'})
            if not stream_div:
                return "❌ Fehler: Stream Bereich nicht gefunden."

            season_links = [a for a in stream_div.find_all('ul')[0].find_all('a') if a.text.strip().lower() != 'filme']
            staffel_info.clear()

            for season_link in season_links:
                name = season_link.text.strip()
                season_url = base_url + season_link['href']
                season_response = client.get(season_url, headers=headers)
                season_soup = BeautifulSoup(season_response.text, 'html.parser')
                episodes = season_soup.find('div', {'id': 'stream'}).find_all('ul')[1].find_all('a', {'data-episode-id': True})
                episode_links = [base_url + ep['href'] for ep in episodes]
                staffel_info[name] = episode_links

        return "✅ Staffeln & Episoden gesammelt."
    except Exception as e:
        return f"❌ Fehler: {str(e)}"

def scrape_voe_link(episode_page_url, base_url):
    try:
        with httpx.Client(follow_redirects=True) as client:
            page = client.get(episode_page_url, headers=headers)
            soup = BeautifulSoup(page.text, 'html.parser')
            for player in soup.select(".generateInlinePlayer"):
                if player.select_one("i.icon.VOE"):
                    link_tag = player.select_one("a.watchEpisode")
                    if link_tag:
                        redirect_url = base_url + link_tag['href']
                        final_response = client.get(redirect_url, headers=headers)
                        return final_response.url
            return "Kein VOE Link gefunden"
    except Exception as e:
        return f"Fehler: {str(e)}"

class BaseTkApp:
    def __init__(self, root, parent):
        self.root = root
        self.parent = parent
        self.canvas = None
        self.width = 0
        self.height = 0
        self.root.after(100, self.setup_canvas)
        self.parent.bind("<<ContentResized>>", self.handle_resize_event)

    def setup_canvas(self):
        self.width = self.parent.winfo_width()
        self.height = self.parent.winfo_height()
        self.canvas = tk.Canvas(self.parent, bg="#0f0f11", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", self.on_resize)
        self.init_gui()

    def on_resize(self, event):
        self.width = event.width
        self.height = event.height
        self.resize()

    def handle_resize_event(self, event=None):
        self.width = self.parent.winfo_width()
        self.height = self.parent.winfo_height()
        if self.canvas:
            self.canvas.config(width=self.width, height=self.height)
        self.resize()

    def resize(self):
        pass

    def init_gui(self):
        pass

class AnimeScraperApp(BaseTkApp):
    def init_gui(self):
        outer = tk.Frame(self.canvas, bg="#0f0f11")
        outer.pack(expand=True, fill="both", padx=40, pady=30)

        self.header_label = tk.Label(outer, text="🎬 Anime Link Scraper", font=("Segoe UI", 28, "bold"),
                                     fg="#89b4fa", bg="#0f0f11", wraplength=800, justify="center")
        self.header_label.pack(anchor="center", pady=(0, 30))

        self.entry_frame = tk.Frame(outer, bg="#1e1e2e")
        self.entry_frame.pack(fill="x", pady=(0, 10), padx=10)
        self.entry_frame.configure(highlightbackground="#89b4fa", highlightthickness=2, bd=0)

        self.url_label = tk.Label(self.entry_frame, text="URL eingeben:", font=("Segoe UI", 12, "bold"),
                                  fg="#cdd6f4", bg="#1e1e2e")
        self.url_label.grid(row=0, column=0, sticky="w", padx=(10, 5), pady=10)

        self.url_entry = tk.Entry(self.entry_frame, font=("Segoe UI", 12), bg="#313244", fg="#f5f5f5",
                                  insertbackground="white", relief="flat")
        self.url_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=10, ipady=6)
        self.url_entry.insert(0, "https://aniworld.to/anime/stream/one-piece")
        self.entry_frame.columnconfigure(1, weight=1)

        button_frame = tk.Frame(outer, bg="#0f0f11")
        button_frame.pack(pady=(5, 5))

        tk.Button(button_frame, text="▶ Scannen", command=self.start_scan,
                  bg="#89b4fa", fg="#1e1e2e", font=("Segoe UI", 11, "bold"),
                  padx=15, pady=6, relief="flat").pack(side="left", padx=10)

        tk.Button(button_frame, text="✖ Abbrechen", command=self.stop_scan,
                  bg="#f38ba8", fg="#1e1e2e", font=("Segoe UI", 11, "bold"),
                  padx=15, pady=6, relief="flat").pack(side="left", padx=10)

        self.status_label = tk.Label(outer, text="Bereit", font=("Segoe UI", 10, "italic"), fg="#a6adc8", bg="#0f0f11")
        self.status_label.pack()

        self.progress = ttk.Progressbar(outer, orient="horizontal", length=400, mode="determinate")
        self.progress.pack(pady=(0, 10))

        output_frame = tk.Frame(outer, bg="#0f0f11")
        output_frame.pack(fill="both", expand=True, pady=10)

        tk.Label(output_frame, text="📄 Ausgabe:", font=("Segoe UI", 12, "bold"),
                 fg="#cdd6f4", bg="#0f0f11").pack(anchor="w", padx=5, pady=(0, 5))

        self.output = scrolledtext.ScrolledText(output_frame, height=20, bg="#11111b", fg="#cdd6f4",
                                                insertbackground="white", font=("Consolas", 10), relief="flat", bd=1)
        self.output.pack(fill="both", expand=True)

    def resize(self):
        if hasattr(self, 'entry_frame') and hasattr(self, 'url_label') and hasattr(self, 'url_entry'):
            if self.width < 600:
                self.url_label.grid(row=0, column=0, columnspan=2, sticky="w", padx=(10, 5), pady=(10, 0))
                self.url_entry.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=(0, 10), ipady=6)
            else:
                self.url_label.grid(row=0, column=0, sticky="w", padx=(10, 5), pady=10)
                self.url_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=10, ipady=6)
            self.entry_frame.columnconfigure(1, weight=1)

        # Dynamische Schriftgröße für Titel
        if hasattr(self, "header_label"):
            if self.width < 500:
                size = 16
            elif self.width < 700:
                size = 22
            else:
                size = 28
            self.header_label.config(font=("Segoe UI", size, "bold"))

    def start_scan(self):
        url = self.url_entry.get()
        current_anime_name = extract_anime_name(url)
        base_url = "https://aniworld.to" if "aniworld.to" in url else "https://s.to"
        self.output.delete(1.0, tk.END)
        shutdown_event.clear()
        self.status_label.config(text="🔍 Scannen läuft…")
        threading.Thread(target=self.scan_worker, args=(url, base_url, current_anime_name), daemon=True).start()

    def stop_scan(self):
        shutdown_event.set()
        self.status_label.config(text="❌ Scan abgebrochen")
        self.output.insert(tk.END, "\n\n❌ Scan abgebrochen!\n")
        self.output.see("end")

    def scan_worker(self, url, base_url, current_anime_name):
        base_folder = "Movies/Anime" if "aniworld.to" in url else "Movies/Serien"
        anime_folder = os.path.join(base_folder, current_anime_name)
        link_folder = os.path.join(anime_folder, "Links")
        cover_folder = os.path.join(anime_folder, "Cover")

        result = scrape_staffeln(url, base_url, cover_folder)
        self.output.insert(tk.END, result + "\n\n")
        self.output.see("end")

        if staffel_info and not shutdown_event.is_set():
            ensure_folder(link_folder)
            for staffel in sorted(staffel_info.keys(), key=num):
                if shutdown_event.is_set():
                    break
                episoden = staffel_info[staffel]
                staffel_num = num(staffel)
                self.output.insert(tk.END, f"\U0001F4FA Staffel {staffel_num}\n")
                self.progress['value'] = 0
                self.progress['maximum'] = len(episoden)
                filepath = os.path.join(link_folder, f"Season_{staffel_num:03}.txt")
                with open(filepath, 'w', encoding='utf-8') as f:
                    for idx, episode_page_url in enumerate(episoden, start=1):
                        if shutdown_event.is_set():
                            break
                        voe_link = scrape_voe_link(episode_page_url, base_url)
                        line = f"Anime: {current_anime_name} | Staffel: {staffel_num} | Episode {idx}: {voe_link}\n"
                        self.output.insert(tk.END, line)
                        f.write(line)
                        self.progress['value'] += 1
                        self.output.see("end")
                self.output.insert(tk.END, "\n")
                self.output.see("end")
            if not shutdown_event.is_set():
                self.status_label.config(text="✅ Fertig!")
                self.output.insert(tk.END, "\n\n✅ Fertig mit Scrapen!\n", "done")
                self.output.tag_config("done", foreground="#a6e3a1")
                self.output.see("end")
        else:
            self.status_label.config(text="⚠️ Keine Episoden")
            self.output.insert(tk.END, "\n⚠️ Keine Episoden gefunden.\n")
            self.output.see("end")

def main(parent):
    AnimeScraperApp(parent.master, parent)
