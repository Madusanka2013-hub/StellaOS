import tkinter as tk
import os
import urllib.request
import json

def main(parent):
    print("[AppManager] main() gestartet")

    apps_folder = os.path.join(os.getcwd(), "scripts", "apps")
    os.makedirs(apps_folder, exist_ok=True)

    card_hoehe = 60
    padding = 12
    cards = []

    background_color = "#1e1e1e"
    card_color = "#2a2a2a"
    accent_color = "#00cc66"      # Installieren-Button
    uninstall_color = "#cc3333"   # Deinstallieren-Button
    button_color = "#333333"
    text_color = "#ffffff"
    font_family = "Segoe UI"

    parent.config(bg=background_color)

    try:
        url = "https://lod-community.de/apps/listapps.php"
        print(f"[AppManager] Lade App-Liste von {url}...")
        response = urllib.request.urlopen(url)
        data = response.read().decode()
        app_names = json.loads(data)
        print(f"[AppManager] Antwort erhalten: {app_names}")
    except Exception as e:
        print(f"[AppManager] Fehler beim Laden der App-Liste: {e}")
        app_names = []

    def install_app(app_name, button):
        print(f"[AppManager] Installiere {app_name}...")
        app_url = f"https://lod-community.de/apps/{app_name}"
        local_path = os.path.join(apps_folder, app_name)

        try:
            urllib.request.urlretrieve(app_url, local_path)
            print(f"[AppManager] {app_name} erfolgreich heruntergeladen.")
            button.config(text="Deinstallieren", bg=uninstall_color, command=lambda: uninstall_app(app_name, button))
        except Exception as e:
            print(f"[AppManager] Fehler beim Herunterladen von {app_name}: {e}")

    def uninstall_app(app_name, button):
        print(f"[AppManager] Deinstalliere {app_name}...")
        local_path = os.path.join(apps_folder, app_name)

        try:
            if os.path.exists(local_path):
                os.remove(local_path)
                print(f"[AppManager] {app_name} entfernt.")
            button.config(text="Installieren", bg=accent_color, command=lambda: install_app(app_name, button))
        except Exception as e:
            print(f"[AppManager] Fehler beim Deinstallieren von {app_name}: {e}")

    for name in app_names:
        frame = tk.Frame(parent, height=card_hoehe, bg=card_color, bd=0, relief="flat", highlightthickness=0)
        frame.pack_propagate(False)

        label = tk.Label(frame, text=name, bg=card_color, fg=text_color, font=(font_family, 10, "bold"), anchor="w")
        label.pack(side="left", padx=15)

        local_app_path = os.path.join(apps_folder, name)
        is_installed = os.path.exists(local_app_path)

        button_text = "Deinstallieren" if is_installed else "Installieren"
        button_bg = uninstall_color if is_installed else accent_color

        btn = tk.Button(frame, text=button_text, bg=button_bg, fg=text_color, font=(font_family, 9, "bold"),
                        activebackground=button_color, relief="flat", width=12)
        btn.pack(side="right", padx=15)

        if is_installed:
            btn.config(command=lambda n=name, b=btn: uninstall_app(n, b))
        else:
            btn.config(command=lambda n=name, b=btn: install_app(n, b))

        cards.append(frame)

    parent.cards = cards

    def update_layout(event=None):
        verfügbare_breite = parent.winfo_width()

        scrollbar_width = 0
        if hasattr(parent.master, 'master'):
            for child in parent.master.master.winfo_children():
                if isinstance(child, tk.Scrollbar):
                    scrollbar_width = child.winfo_width()

        if scrollbar_width == 0:
            scrollbar_width = 10

        verfügbare_breite -= scrollbar_width + 10

        card_min_breite = 300
        spaltenanzahl = max(1, verfügbare_breite // (card_min_breite + padding))
        print(f"[AppManager] update_layout: verfügbare_breite={verfügbare_breite}, spaltenanzahl={spaltenanzahl}")

        dynamische_card_breite = (verfügbare_breite - (spaltenanzahl + 1) * padding) // spaltenanzahl
        print(f"[AppManager] dynamische_card_breite={dynamische_card_breite}")

        row, col = 0, 0

        for card in cards:
            card.config(width=dynamische_card_breite, height=card_hoehe)

            if col < spaltenanzahl - 1:
                extra_padx = (padding, padding)
            else:
                extra_padx = (padding, padding + 8)

            card.grid(row=row, column=col, padx=extra_padx, pady=(padding // 2), sticky="ew")

            col += 1
            if col >= spaltenanzahl:
                col = 0
                row += 1

    parent.bind("<<ContentResized>>", update_layout)
    parent.after(50, update_layout)
