import tkinter as tk
from PIL import Image, ImageTk
import os
import urllib.request

def main(parent):
    print("WallpaperChanger: main() gestartet")

    img_folder = os.path.join(os.getcwd(), "scripts", "img")
    os.makedirs(img_folder, exist_ok=True)  # Ordner anlegen, wenn nicht vorhanden

    default_image_path = os.path.join(img_folder, "default.jpg")
    if not os.path.exists(default_image_path):
        print(f"Default-Bild nicht gefunden — lade herunter nach {default_image_path}")
        image_url = "https://lod-community.de/apps/bg.jpeg"
        try:
            urllib.request.urlretrieve(image_url, default_image_path)
            print("Standard-Hintergrundbild heruntergeladen.")
        except Exception as e:
            print(f"Fehler beim Herunterladen des Standardbilds: {e}")

    preview_images = []
    buttons = []
    bild_breite = 100
    bild_hoehe = 75
    padding = 10

    for filename in os.listdir(img_folder):
        if filename.lower().endswith(("jpg", "jpeg", "png")):
            path = os.path.join(img_folder, filename)
            img = Image.open(path)
            img = img.resize((bild_breite, bild_hoehe), Image.LANCZOS)
            img_tk = ImageTk.PhotoImage(img)
            preview_images.append(img_tk)

            btn = tk.Button(
                parent,
                image=img_tk,
                command=lambda p=path: change_wallpaper(p, parent),
                bg="#2c2c2c",
                relief="flat",
                activebackground="#3c3c3c",
            )
            buttons.append(btn)

    parent.preview_images = preview_images
    parent.wallpaper_buttons = buttons

    def update_layout(event=None):
        canvas = parent.master  # Das ist dein content_canvas
        verfügbare_breite = canvas.winfo_width()

        spaltenanzahl = max(1, verfügbare_breite // (bild_breite + padding))
        print(f"[WallpaperChanger] update_layout: verfügbare_breite={verfügbare_breite}, spaltenanzahl={spaltenanzahl}")
        row, col = 0, 0

        for btn in buttons:
            btn.grid(row=row, column=col, padx=5, pady=5)
            col += 1
            if col >= spaltenanzahl:
                col = 0
                row += 1

    parent.bind("<<ContentResized>>", update_layout)
    parent.after(50, update_layout)

def change_wallpaper(image_path, parent):
    print(f"WallpaperChanger: change_wallpaper aufgerufen mit {image_path}")

    root = parent.winfo_toplevel()

    if hasattr(root, "app") and hasattr(root.app, "change_background"):
        root.app.change_background(image_path)
    else:
        print("WallpaperChanger: Fehler - root.app oder change_background nicht gefunden!")

    save_file = os.path.join(os.getcwd(), "scripts", "selected_wallpaper.txt")
    with open(save_file, "w") as f:
        f.write(image_path)

    print("WallpaperChanger: Hintergrund gespeichert!")
