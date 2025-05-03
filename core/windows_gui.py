import tkinter as tk
from PIL import Image, ImageTk
import json, os, uuid, importlib.util
from datetime import datetime

from .app_window import AppWindow
from .canvas_shortcut import CanvasShortcut

CONFIG_DIR = os.path.join(os.getcwd(), "config")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")

class Windows7GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Mein OS Modern")
        self.root.geometry("1024x600")
        self.root.configure(bg="#121212")
        self.root.resizable(True, True)
        self.root.bind("<Configure>", self.on_resize)

        self.open_apps = {}
        self.desktop_shortcuts = {}
        self.shortcut_positions = {}
        self.start_menu_visible = False

        self.taskbar_height = 48
        self.start_menu_width = 260
        self.start_menu_height = 340

        self.content_frame = tk.Frame(self.root, bg="#121212")
        self.content_frame.place(x=0, y=0, relwidth=1.0)
        self.root.after(10, self.update_content_frame_height)

        self.taskbar = tk.Frame(self.root, bg="#202124", height=self.taskbar_height)
        self.root.after_idle(self.position_taskbar_initial)

        self.desktop_canvas = tk.Canvas(
            self.content_frame, bg="#121212",
            highlightthickness=0, bd=0
        )
        self.desktop_canvas.place(x=0, y=0, relwidth=1.0)
        self.update_desktop_canvas_height()

        self.current_bg_path = os.path.join(os.getcwd(), "scripts", "img", "bg.jpeg")
        self.bg_image = None
        self.background_image_id = None
        self.raw_bg_image = None

        self._start_menu_lock_y = None

        self.load_config()
        self.root.update_idletasks()
        self.load_background()

        self.create_taskbar_widgets()
        self.update_clock()

        self.root.bind("<Button-1>", self.global_click_handler)
        self.create_start_menu_once()
        self.render_desktop_icons()

        # <<< Start Ordner überwachen >>>
        self.watch_apps_folder()

    def update_content_frame_height(self):
        height = self.root.winfo_height()
        if height < 100:
            self.root.after(20, self.update_content_frame_height)
            return
        self.content_frame.place_configure(height=height - self.taskbar_height)

    def update_desktop_canvas_height(self):
        self.desktop_canvas.place_configure(height=self.root.winfo_height() - self.taskbar_height)

    def position_taskbar_initial(self):
        height = self.root.winfo_height()
        if height < 100:
            self.root.after(50, self.position_taskbar_initial)
            return
        self.taskbar.place(
            x=0,
            y=height - self.taskbar_height,
            relwidth=1.0,
            height=self.taskbar_height
        )

    def on_resize(self, event):
        if hasattr(self, "_resize_after_id"):
            self.root.after_cancel(self._resize_after_id)
        self._resize_after_id = self.root.after(200, lambda: self._handle_resize(event))

    def _handle_resize(self, event):
        self.update_content_frame_height()
        self.update_desktop_canvas_height()
        self.position_taskbar_initial()
        self._update_background_resize()

        if hasattr(self, "start_menu_frame") and self.start_menu_visible:
            if self._start_menu_lock_y is None:
                self._start_menu_lock_y = self.root.winfo_height() - self.taskbar_height - self.start_menu_height
            else:
                self._start_menu_lock_y = self.root.winfo_height() - self.taskbar_height - self.start_menu_height

            self.start_menu_frame.place_configure(
                x=0,
                y=self._start_menu_lock_y,
                width=self.start_menu_width,
                height=self.start_menu_height
            )

        for app in self.open_apps.values():
            inst = app["instance"]
            if inst.is_maximized:
                w, h = self.root.winfo_width(), self.root.winfo_height()
                inst.place(x=0, y=0, width=w, height=h - self.taskbar_height)
                inst.itemconfig(inst.titlebar_id, width=w)
                inst.itemconfig(inst.content_id, width=w, height=h - self.taskbar_height - 30)

    def ensure_config_dir(self):
        if not os.path.exists(CONFIG_DIR):
            os.makedirs(CONFIG_DIR)

    def load_config(self):
        self.ensure_config_dir()
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r") as f:
                data = json.load(f)
                self.current_bg_path = data.get("background", self.current_bg_path)
                self.shortcut_positions = data.get("positions", {})
                for app_name in data.get("shortcuts", []):
                    self.create_desktop_icon(app_name)

    def save_config(self):
        self.ensure_config_dir()
        shortcuts = list(self.desktop_shortcuts.keys())
        with open(CONFIG_PATH, "w") as f:
            json.dump({
                "background": self.current_bg_path,
                "shortcuts": shortcuts,
                "positions": self.shortcut_positions
            }, f, indent=2)

    def load_background(self):
        try:
            if os.path.exists(self.current_bg_path):
                self.raw_bg_image = Image.open(self.current_bg_path).convert("RGBA")
                self._update_background_resize()
        except Exception as e:
            print(f"Fehler beim Laden des Hintergrundbildes: {e}")

    def _update_background_resize(self):
        try:
            if self.raw_bg_image:
                image = self.raw_bg_image.resize((self.root.winfo_width(), self.root.winfo_height() - self.taskbar_height), Image.LANCZOS)
                self.bg_image = ImageTk.PhotoImage(image)
                if self.background_image_id:
                    self.desktop_canvas.itemconfig(self.background_image_id, image=self.bg_image)
                else:
                    self.background_image_id = self.desktop_canvas.create_image(0, 0, anchor="nw", image=self.bg_image)
                    self.desktop_canvas.lower(self.background_image_id)
        except Exception as e:
            print(f"Fehler beim Resizen des Hintergrundbildes: {e}")

    def change_background(self, image_path):
        if os.path.exists(image_path):
            self.current_bg_path = image_path
            self.root.update_idletasks()
            self.load_background()
            self.save_config()

    def is_maximized(self):
        return any(app["instance"].is_maximized for app in self.open_apps.values())

    def create_shortcut(self, app_name):
        if app_name in self.desktop_shortcuts:
            return
        self.create_desktop_icon(app_name)
        self.save_config()

    def create_desktop_icon(self, app_name):
        if app_name in self.desktop_shortcuts:
            return
        x_offset = 20 + (len(self.desktop_shortcuts) % 4) * 120
        y_offset = 40 + (len(self.desktop_shortcuts) // 4) * 100
        mode = "max" if self.is_maximized() else "normal"
        coords = self.shortcut_positions.get(app_name, {}).get(mode, [x_offset, y_offset])
        shortcut = CanvasShortcut(self.desktop_canvas, app_name, self, x=coords[0], y=coords[1])
        self.desktop_shortcuts[app_name] = shortcut

    def remove_shortcut(self, app_name):
        if app_name in self.desktop_shortcuts:
            shortcut = self.desktop_shortcuts[app_name]
            for item_id in shortcut.items:
                self.desktop_canvas.delete(item_id)
            del self.desktop_shortcuts[app_name]
            self.shortcut_positions.pop(app_name, None)
            self.save_config()

    def render_desktop_icons(self):
        for app in list(self.desktop_shortcuts):
            self.create_desktop_icon(app)

    def create_taskbar_widgets(self):
        self.start_button = tk.Button(self.taskbar, text="🎾 Start", command=self.toggle_start_menu,
                                      bg="#3c4043", fg="white", activebackground="#5f6368",
                                      font=("Segoe UI", 10, "bold"), relief="flat",
                                      padx=16, pady=6, bd=0, highlightthickness=0)
        self.start_button.pack(side="left", padx=6)

        self.taskbar_buttons_frame = tk.Frame(self.taskbar, bg="#202124")
        self.taskbar_buttons_frame.pack(side="left", padx=6)

        self.clock_label = tk.Label(self.taskbar, text="", bg="#202124", fg="#e8eaed", font=("Segoe UI", 10))
        self.clock_label.pack(side="right", padx=12)

    def update_clock(self):
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        self.clock_label.config(text=current_time)
        self.root.after(1000, self.update_clock)

    def global_click_handler(self, event):
        if self.start_menu_visible:
            widget = event.widget
            if not str(widget).startswith(str(self.start_menu_frame)) and widget != self.start_button:
                self.toggle_start_menu()

    def create_start_menu_once(self):
        self.start_menu_frame = tk.Frame(self.root, bg="#292a2d", bd=0)
        self.start_menu_frame.place_forget()

        self.start_menu_scrollbar = tk.Scrollbar(self.start_menu_frame, orient="vertical", bg="#3c3c3c",
                                                 activebackground="#5f6368", troughcolor="#292a2d",
                                                 bd=0, relief="flat", width=8)
        self.start_menu_scrollbar.pack(side="right", fill="y")

        self.start_menu_canvas = tk.Canvas(self.start_menu_frame, bg="#292a2d", highlightthickness=0, bd=0,
                                           yscrollcommand=self.start_menu_scrollbar.set)
        self.start_menu_canvas.pack(side="left", fill="both", expand=True)
        self.start_menu_scrollbar.config(command=self.start_menu_canvas.yview)

        self.start_menu_inner = tk.Frame(self.start_menu_canvas, bg="#292a2d")
        self.canvas_window = self.start_menu_canvas.create_window((0, 0), window=self.start_menu_inner, anchor="nw")

        self.start_menu_inner.bind("<Configure>", self._update_scroll_region)
        self.start_menu_canvas.bind("<Enter>", lambda e: self._bind_mousewheel())
        self.start_menu_canvas.bind("<Leave>", lambda e: self._unbind_mousewheel())

        for app in self.list_apps():
            self.add_app_button(app)

    def _bind_mousewheel(self):
        self.start_menu_canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbind_mousewheel(self):
        self.start_menu_canvas.unbind_all("<MouseWheel>")

    def _update_scroll_region(self, event=None):
        self.start_menu_canvas.configure(scrollregion=self.start_menu_canvas.bbox("all"))
        self.start_menu_canvas.itemconfig(self.canvas_window, width=self.start_menu_width)

    def add_app_button(self, app):
        btn = tk.Button(self.start_menu_inner, text="📁 " + app, bg="#3a3b3c", fg="#e8eaed",
                        activebackground="#5f6368", activeforeground="white", anchor="w",
                        padx=14, pady=6, relief="flat", bd=0, font=("Segoe UI", 10),
                        command=lambda a=app: self.launch_app(a), width=30)
        btn.pack(anchor="w", padx=13, pady=1)
        btn.bind("<Enter>", lambda e, b=btn: b.config(bg="#5f6368"))
        btn.bind("<Leave>", lambda e, b=btn: b.config(bg="#3a3b3c"))
        btn.bind("<Button-3>", lambda e, a=app: self.show_start_context_menu(e, a))

    def _on_mousewheel(self, event):
        self.start_menu_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def show_start_context_menu(self, event, app_name):
        menu = tk.Menu(self.root, tearoff=0, bg="#292a2d", fg="#e8eaed",
                       activebackground="#5f6368", activeforeground="white",
                       bd=0, relief="flat", font=("Segoe UI", 10))
        menu.add_command(label="Verknüpfung auf Desktop erstellen", command=lambda: self.create_shortcut(app_name))
        menu.tk_popup(event.x_root, event.y_root)

    def toggle_start_menu(self):
        self.start_menu_visible = not self.start_menu_visible
        if self.start_menu_visible:
            if not self.is_maximized():
                self._start_menu_lock_y = self.root.winfo_height() - self.taskbar_height - self.start_menu_height
            self.start_menu_frame.place_configure(
                x=0,
                y=self._start_menu_lock_y,
                width=self.start_menu_width,
                height=self.start_menu_height
            )
            self.start_menu_frame.lift()
        else:
            self._start_menu_lock_y = None
            self.start_menu_frame.place_forget()

    def list_apps(self):
        apps_folder = os.path.join(os.getcwd(), "scripts", "apps")
        if not os.path.exists(apps_folder):
            return []
        return [f[:-3] for f in os.listdir(apps_folder) if f.endswith(".py")]

    def launch_app(self, app_name):
        app_path = os.path.join(os.getcwd(), "scripts", "apps", f"{app_name}.py")
        try:
            unique_id = uuid.uuid4().hex
            spec = importlib.util.spec_from_file_location(f"{app_name}_{unique_id}", app_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            if app_name in self.open_apps:
                app_window = self.open_apps[app_name]["instance"]
                app_window.master.tk.call("raise", app_window._w)
                return

            app_window = AppWindow(self.content_frame, self, app_name, module.main)
            app_window.place(x=100, y=100)
            self.open_apps[app_name] = {"instance": app_window}
            self.add_to_taskbar(app_name, app_window)

            self.start_menu_frame.lower()
            self.start_menu_visible = False

        except Exception as e:
            print(f"Fehler beim Starten von {app_name}: {e}")

    def add_to_taskbar(self, app_name, app_window):
        btn = tk.Button(self.taskbar_buttons_frame, text=app_name, bg="#3c4043", fg="white",
                        font=("Segoe UI", 9), bd=0, relief="flat", padx=10, pady=5,
                        activebackground="#5f6368", activeforeground="white",
                        command=lambda: self.toggle_app_visibility(app_window))
        btn.pack(side="left", padx=3, pady=3)
        self.open_apps[app_name]["button"] = btn

    def toggle_app_visibility(self, app_window):
        if str(app_window.winfo_manager()) == "":
            if hasattr(app_window, "saved_geometry") and app_window.saved_geometry:
                x, y, w, h = app_window.saved_geometry
                app_window.place(x=x, y=y, width=w, height=h)
            else:
                app_window.place(x=100, y=100)
            app_window.master.tk.call("raise", app_window._w)
        else:
            app_window.place_forget()

    # <<<< NEU: Live-Überwachung für neue oder entfernte Apps >>>>
    def watch_apps_folder(self):
        current_apps = set(self.list_apps())
        if hasattr(self, "_last_apps"):
            if current_apps != self._last_apps:
                self.refresh_start_menu()
        self._last_apps = current_apps
        self.root.after(1000, self.watch_apps_folder)

    def refresh_start_menu(self):
        for widget in self.start_menu_inner.winfo_children():
            widget.destroy()
        for app in self.list_apps():
            self.add_app_button(app)
