import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from PIL import Image, ImageTk
import threading
import subprocess
import shutil
import os
import sys
import platform
import re

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
sys.path.append(ROOT_DIR)
from core.voe_scraper import get_best_m3u8_from_voe

class BaseTkApp:
    def __init__(self, root, parent):
        self.root = root
        self.parent = parent
        self.width = 0
        self.height = 0

        self.container = tk.Frame(self.parent)
        self.container.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(self.container, bg="#1e1e2e", highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)

        self.scrollbar = tk.Scrollbar(self.container, orient="vertical", command=self.canvas.yview)
        self.scrollbar.pack(side="right", fill="y")

        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.content_frame = tk.Frame(self.canvas, bg="#1e1e2e")
        self.canvas_window = self.canvas.create_window((0, 0), window=self.content_frame, anchor="nw")

        self.content_frame.bind("<Configure>", self.on_content_configure)
        self.parent.bind("<<ContentResized>>", self.handle_resize_event)
        self.root.after(100, self.setup_initial)
        self.canvas.bind("<Configure>", self.on_canvas_configure)
        self.bind_mousewheel()
        self.canvas.bind("<Enter>", lambda e: self.canvas.focus_set())

    def bind_mousewheel(self):
        system = platform.system()
        widgets = [self.canvas, self.content_frame, self.container, self.parent, self.root]
        
        for widget in widgets:
            if system == 'Windows':
                widget.bind("<MouseWheel>", self.on_mousewheel_windows)
            elif system == 'Linux':
                widget.bind("<Button-4>", self.on_mousewheel_linux_up)
                widget.bind("<Button-5>", self.on_mousewheel_linux_down)
            elif system == 'Darwin':
                widget.bind("<MouseWheel>", self.on_mousewheel_mac)

    def on_mousewheel_windows(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def on_mousewheel_linux_up(self, event):
        self.canvas.yview_scroll(-1, "units")

    def on_mousewheel_linux_down(self, event):
        self.canvas.yview_scroll(1, "units")

    def on_mousewheel_mac(self, event):
        self.canvas.yview_scroll(int(-1 * event.delta), "units")


    def setup_initial(self):
        self.width = self.parent.winfo_width()
        self.height = self.parent.winfo_height()
        self.resize()

    def on_content_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_canvas_configure(self, event):
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_window, width=canvas_width)

    def handle_resize_event(self, event=None):
        self.width = self.parent.winfo_width()
        self.height = self.parent.winfo_height()
        self.resize()

    def resize(self):
        pass

class DownloadApp(BaseTkApp):
    def __init__(self, root, parent):
        super().__init__(root, parent)
        self.anime_dir = "Movies/Anime"
        self.process_handles = {}
        self.progressbars = {}
        self.season_frames = {}
        self.season_states = {}
        self.check_ffmpeg()
        self.init_ui()

    def check_ffmpeg(self):
        if not shutil.which("ffmpeg"):
            ffmpeg_path = os.path.join(os.getcwd(), "ffmpeg.exe")
            if not os.path.exists(ffmpeg_path):
                messagebox.showerror("Fehler: ffmpeg fehlt", "Das Programm 'ffmpeg' wurde nicht gefunden. Bitte lade es herunter und speichere es im Projektverzeichnis oder im Systempfad.")
                self.root.quit()

    def init_ui(self):
                # ← Zurück Button definieren und verstecken
        self.back_button = tk.Button(self.content_frame, text="← Zurück", font=("Segoe UI", 12),
                             bg="#f38ba8", fg="#1e1e2e", command=self.back_to_anime_select)
        self.back_button.pack(anchor="w", padx=10)
        self.back_button.pack_forget()
        self.cover_label = tk.Label(self.content_frame, bg="#1e1e2e")
        self.cover_label.pack(pady=10)
        self.title_label = tk.Label(self.content_frame, text="Wähle einen Anime", font=("Segoe UI", 16), fg="#89b4fa", bg="#1e1e2e")
        self.title_label.pack(pady=(0, 10))
        self.anime_selector = ttk.Combobox(self.content_frame, state="readonly")
        self.anime_selector.pack(pady=10)
        self.anime_selector.bind("<<ComboboxSelected>>", self.load_seasons)
        self.season_frame = tk.Frame(self.content_frame, bg="#1e1e2e")
        self.season_frame.pack(pady=10, fill="both", expand=True)
        self.load_anime_options()
        
    def back_to_anime_select(self):
        self.anime_selector.set("")  # Auswahl leeren
        for widget in self.season_frame.winfo_children():
            widget.destroy()  # Staffel-Frames löschen
        self.cover_label.configure(image="", text="Wähle einen Anime")  # Cover reset
        self.title_label.config(text="Wähle einen Anime")  # Titel-Label reset
        self.anime_selector.config(state="readonly")  # Dropdown wieder aktivieren
        self.back_button.pack_forget()  # Zurück-Button wieder verstecken


    def load_anime_options(self):
        if not os.path.exists(self.anime_dir):
            return
        self.animes = [d for d in os.listdir(self.anime_dir) if os.path.isdir(os.path.join(self.anime_dir, d))]
        self.anime_selector['values'] = self.animes

        def toggle_season(self, frame):
            if frame.winfo_ismapped():
                frame.pack_forget()
            else:
                frame.pack(fill="x", padx=20, pady=5)
                
    def load_seasons(self, event=None):
        for widget in self.season_frame.winfo_children():
            widget.destroy()

        anime = self.anime_selector.get()
        self.anime_selector.config(state="disabled")  # Dropdown sperren
        self.back_button.pack(anchor="w", padx=10)  # Zurück-Button anzeigen

        anime_path = os.path.join(self.anime_dir, anime)
        cover_path = os.path.join(anime_path, "Cover", "cover.jpg")
        self.display_cover(cover_path)

        links_dir = os.path.join(anime_path, "Links")
        if not os.path.exists(links_dir):
            print(f"Kein Links-Ordner gefunden in {anime_path}")
            return

        if not hasattr(self, 'episode_buttons'):
            self.episode_buttons = {}

        for file in sorted(os.listdir(links_dir)):
            if file.startswith("Season_") and file.endswith(".txt"):
                season_path = os.path.join(links_dir, file)
                season_num = file.replace("Season_", "").replace(".txt", "").lstrip("0") or "1"

                # → Container-Frame für Staffel-Header und Episoden-Frame
                container = tk.Frame(self.season_frame, bg="#1e1e2e")
                container.pack(fill="x", pady=5, padx=5)

                # Header-Frame
                header = tk.Frame(container, bg="#313244")
                header.pack(fill="x")

                label = tk.Label(header, text=f"Staffel {season_num}", font=("Segoe UI", 12), fg="#cdd6f4", bg="#313244", cursor="hand2")
                label.pack(side="left", padx=10)

                # Collapse-Toggle Funktion
                def toggle(season=season_num):
                    frame = self.season_frames[season]
                    if self.season_states[season]:
                        frame.pack_forget()
                        self.season_states[season] = False
                    else:
                        frame.pack(fill="x", padx=20, pady=5)
                        self.season_states[season] = True

                label.bind("<Button-1>", lambda e, s=season_num: toggle(s))

                all_eps_exist = self.check_all_episodes_exist(anime, season_num, season_path)
                if all_eps_exist:
                    btn = tk.Button(header, text="🗑️ Ganze Staffel löschen", bg="#f38ba8", fg="#1e1e2e",
                                    command=lambda a=anime, s=season_num, p=season_path: self.delete_season(a, s, p))
                else:
                    btn = tk.Button(header, text="⬇ Ganze Staffel", bg="#89b4fa", fg="#1e1e2e",
                                    command=lambda p=season_path, a=anime, s=season_num: self.download_season(p, a, s))
                btn.pack(side="right", padx=10)

                # Episoden-Frame (standardmäßig versteckt) — im selben Container!
                episode_frame = tk.Frame(container, bg="#45475a")
                self.season_frames[season_num] = episode_frame
                self.season_states[season_num] = False

                with open(season_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if "Episode" in line and "http" in line:
                            ep_match = re.search(r'Episode\s*:?\s*([0-9]+)', line, re.IGNORECASE)
                            if not ep_match:
                                continue
                            ep_num = int(ep_match.group(1))
                            url_match = re.search(r'(https?://[^\s]+)', line)
                            if not url_match:
                                continue
                            voe_url = url_match.group(1)

                            ep_line = tk.Frame(episode_frame, bg="#45475a")
                            ep_line.pack(fill="x", pady=2)

                            lbl = tk.Label(ep_line, text=f"Episode {ep_num}", fg="#cdd6f4", bg="#45475a")
                            lbl.pack(side="left")

                            out_path = os.path.join(self.anime_dir, anime, f"Staffel{int(season_num):02}",
                                                    f"{anime} - S{int(season_num):02}E{ep_num:02} - Deutsch.mp4")

                            key = (anime, season_num, ep_num)

                            if os.path.exists(out_path):
                                btn_ep = tk.Button(ep_line, text="🗑️", bg="#f38ba8", fg="#1e1e2e",
                                                command=lambda p=out_path, b=ep_line: self.delete_episode(p, b))
                                progress = None
                            else:
                                btn_ep = tk.Button(ep_line, text="⬇", bg="#89b4fa", fg="#1e1e2e",
                                                command=lambda v=voe_url, a=anime, s=season_num, e=ep_num:
                                                self.download_single(v, a, s, e))
                                progress = ttk.Progressbar(ep_line, length=100, mode="determinate")
                                progress.pack(side="right", padx=5)
                                self.progressbars[key] = progress

                            btn_ep.pack(side="right")
                            self.episode_buttons[key] = btn_ep

                 
    def display_cover(self, path):
        try:
            image = Image.open(path)
            image.thumbnail((300, 450))
            photo = ImageTk.PhotoImage(image)
            self.cover_label.configure(image=photo)
            self.cover_label.image = photo
        except:
            self.cover_label.configure(image="", text="Kein Cover gefunden")
            
    def check_all_episodes_exist(self, anime, season, season_path):
        with open(season_path, 'r', encoding='utf-8') as f:
            for line in f:
                if "Episode" in line and "http" in line:
                    ep_match = re.search(r'Episode\s*:?:?\s*([0-9]+)', line, re.IGNORECASE)
                    if not ep_match:
                        continue
                    ep_num = int(ep_match.group(1))
                    out_path = os.path.join(self.anime_dir, anime, f"Staffel{int(season):02}",
                                            f"{anime} - S{int(season):02}E{ep_num:02} - Deutsch.mp4")
                    if not os.path.exists(out_path):
                        return False
        return True

    def delete_episode(self, filepath, ep_line):
        if os.path.exists(filepath):
            os.remove(filepath)
            messagebox.showinfo("Gelöscht", f"{os.path.basename(filepath)} wurde gelöscht.")
        ep_line.destroy()
        self.load_seasons()
    
    def delete_season(self, anime, season, season_path):
        with open(season_path, 'r', encoding='utf-8') as f:
            for line in f:
                if "Episode" in line and "http" in line:
                    ep_match = re.search(r'Episode\s*:?:?\s*([0-9]+)', line, re.IGNORECASE)
                    if not ep_match:
                        continue
                    ep_num = int(ep_match.group(1))
                    out_path = os.path.join(self.anime_dir, anime, f"Staffel{int(season):02}",
                                            f"{anime} - S{int(season):02}E{ep_num:02} - Deutsch.mp4")
                    if os.path.exists(out_path):
                        os.remove(out_path)
        messagebox.showinfo("Staffel gelöscht", f"Staffel {season} wurde gelöscht.")
        self.load_seasons()
        
    def download_single(self, voe_url, anime_name, season, ep_num):
        threading.Thread(
            target=self._download_episode,
            args=(voe_url, anime_name, season, ep_num, 1, 1),
            daemon=True
        ).start()

    
    def _download_episode(self, voe_url, anime_name, season, ep_num, total_count=1, current_index=1):
        from urllib.parse import urlparse, parse_qs, unquote

        base_path = os.path.join(self.anime_dir, anime_name)
        out_dir = os.path.join(base_path, f"Staffel{int(season):02}")
        os.makedirs(out_dir, exist_ok=True)

        self.title_label.config(text=f"{anime_name} – Episode {ep_num} ({current_index}/{total_count})")

        m3u8_raw = get_best_m3u8_from_voe(voe_url)
        parsed_url = urlparse(m3u8_raw)
        query_params = parse_qs(parsed_url.query)

        if 'mu' in query_params and "master.m3u8" in unquote(query_params['mu'][0]):
            m3u8 = unquote(query_params['mu'][0])
            print(f"🎯 MASTER via mu: {m3u8}")
        else:
            m3u8 = m3u8_raw
            print(f"🎯 MASTER direkt: {m3u8}")

        if not m3u8 or not m3u8.startswith("http"):
            print(f"❌ Ungültige m3u8: {m3u8}")
            return

        out_path = os.path.join(out_dir, f"{anime_name} - S{int(season):02}E{ep_num:02} - Deutsch.mp4")

        try:
            duration_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                            "-of", "default=noprint_wrappers=1:nokey=1", m3u8]
            duration_result = subprocess.run(duration_cmd, capture_output=True, text=True)
            duration = float(duration_result.stdout.strip())
        except Exception as e:
            print(f"❌ Dauer-Fehler: {e}")
            duration = None

        key = (anime_name, season, ep_num)
        progress = self.progressbars.get(key)
        if progress:
            progress["value"] = 0

        try:
            gpu_check = subprocess.run(["ffmpeg", "-hide_banner", "-encoders"], capture_output=True, text=True)
            if "h264_nvenc" in gpu_check.stdout:
                cmd = [
                    "ffmpeg", "-y", "-hwaccel", "nvdec", "-user_agent", "Mozilla/5.0", "-i", m3u8,
                    "-c:v", "h264_nvenc", "-preset", "fast", "-rc:v", "vbr", "-cq:v", "23", "-b:v", "0",
                    "-c:a", "copy", "-vf", "scale=-1:720", "-threads", "0", out_path
                ]
            else:
                raise Exception("NVENC nicht verfügbar")
        except Exception:
            cmd = [
                "ffmpeg", "-y", "-user_agent", "Mozilla/5.0", "-i", m3u8,
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
                "-c:a", "copy", "-vf", "scale=-1:720", "-threads", "0", out_path
            ]

        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        time_pattern = re.compile(r"time=(\d+):(\d+):(\d+)\.(\d+)")

        for line in proc.stdout:
            match = time_pattern.search(line)
            if match and duration:
                h, m, s, ms = map(int, match.groups())
                current_time = h * 3600 + m * 60 + s + ms / 100
                percent = (current_time / duration) * 100
                if progress:
                    progress.after(0, lambda p=progress, v=percent: p.config(value=v))

        proc.wait()

        if proc.returncode == 0:
            print(f"✅ Erfolgreich: Episode {ep_num}")

            # Progressbar entfernen
            progress = self.progressbars.pop(key, None)
            if progress:
                progress.destroy()

            # ALTEN Button entfernen & durch 🗑️ ersetzen
            def replace_button_safely():
                # Entferne Progressbar im UI-Thread
                prog = self.progressbars.pop(key, None)
                if prog:
                    prog.destroy()

                # Entferne alten Download-Button
                old_btn = self.episode_buttons.pop(key, None)
                if old_btn:
                    old_btn.destroy()

                # Füge 🗑️ Button hinzu
                ep_line = prog.master if prog else old_btn.master
                btn_delete = tk.Button(ep_line, text="🗑️", bg="#f38ba8", fg="#1e1e2e",
                    command=lambda p=out_path, b=ep_line: self.delete_episode(p, b))
                btn_delete.pack(side="right")

            self.root.after(0, replace_button_safely)


        else:
            print(f"❌ Fehler bei Episode {ep_num}")

        self.title_label.config(text="Bereit")
    

    def download_season(self, filepath, anime_name, season):
        threading.Thread(
            target=self._download_thread,
            args=(filepath, anime_name, season),
            daemon=True
        ).start()

    def _download_thread(self, filepath, anime_name, season):
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if "Episode" in line and "http" in line]

        episode_jobs = []

        for idx, line in enumerate(lines, 1):
            try:
                parts = line.strip().split("|")
                ep_tag = next((p for p in parts if "Episode" in p), None)
                url_match = re.search(r'(https?://[^\s]+)', line)
                if not ep_tag or not url_match:
                    continue
                ep_match = re.search(r'Episode\s*:?:?\s*([0-9]+)', ep_tag, re.IGNORECASE)
                if not ep_match:
                    continue
                ep_num = int(ep_match.group(1))
                voe_url = url_match.group(1)

                out_path = os.path.join(self.anime_dir, anime_name, f"Staffel{int(season):02}",
                                        f"{anime_name} - S{int(season):02}E{ep_num:02} - Deutsch.mp4")
                if os.path.exists(out_path):
                    print(f"⏩ Überspringe Episode {ep_num}, existiert bereits.")
                    continue

                episode_jobs.append((voe_url, anime_name, season, ep_num, len(lines), idx))
            except Exception as e:
                print(f"🔥 Fehler bei Zeile {idx}: {e}")
                continue

        total_eps = len(episode_jobs)
        success_count = 0

        for i in range(0, total_eps, 5):
            batch = episode_jobs[i:i + 5]
            threads = []

            for voe_url, anime, season, ep_num, total, idx in batch:
                t = threading.Thread(
                    target=self._download_episode,
                    args=(voe_url, anime, season, ep_num, total, idx),
                    daemon=True
                )
                threads.append(t)
                t.start()

            # Auf alle Threads im aktuellen Batch warten
            for t in threads:
                t.join()
                success_count += 1

        self.title_label.config(text=f"✅ Staffel {season}: {success_count}/{total_eps} Episoden geladen.")
        messagebox.showinfo("Fertig", f"Staffel {season} wurde heruntergeladen.\n{success_count}/{total_eps} Episoden erfolgreich geladen.")


        

def main(parent=None):
    if parent is None:
        root = tk.Tk()
        root.title("Anime Downloader")
        frame = tk.Frame(root, width=600, height=600)
        frame.pack(fill="both", expand=True)
        app = DownloadApp(root, frame)
        root.mainloop()
    else:
        DownloadApp(parent.master, parent)

if __name__ == "__main__":
    main()
