import tkinter as tk
from datetime import datetime

class AppWindow(tk.Canvas):
    def __init__(self, master, gui, app_name, app_main, animate_resize=False):
        super().__init__(master, bg="#1e1e1e", bd=2, highlightthickness=0)
        self.gui = gui
        self.app_name = app_name
        self.app_main = app_main
        self.is_maximized = False
        self.was_maximized = False
        self.animate_resize = animate_resize
        self._drag_data = {"x": 0, "y": 0}
        self._normal_geometry = None
        self.saved_geometry = None
        self.resize_after_id = None

        self.place(x=100, y=100, width=400, height=430)  # Fensterhöhe: 400px Inhalt + 30px Titelbar

        self.shadow = self.create_rectangle(5, 5, 405, 435, fill="#000000", outline="", stipple="gray50")
        self.tag_lower(self.shadow)

        self.build_ui()
        self.bind("<Configure>", self.on_resize_debounced)
        self.bind_all("<Escape>", lambda e: self.close_app())

    def on_resize_debounced(self, event):
        if self.resize_after_id:
            self.after_cancel(self.resize_after_id)
        self.resize_after_id = self.after(100, self.handle_resize)

    def handle_resize(self):
        width = self.winfo_width()
        height = self.winfo_height()
        titlebar_height = 30  # Höhe der Titelbar
        content_height = max(height - titlebar_height, 0)  # Berechne die Höhe des Inhaltsbereichs

        # Aktualisiere die Schattenbox
        self.coords(self.shadow, 5, 5, width + 5, height + 5)
        
        # Aktualisiere Titelbar und Content
        self.itemconfig(self.titlebar_id, width=width)
        self.itemconfig(self.content_id, width=width, height=content_height)
        self.content_canvas.config(width=width, height=content_height)
        self.content_canvas.itemconfig(self.content_canvas_window, width=width)
        self.coords(self.resize_handle_id, width, height)

        # Die innere Frame-Höhe auf den verfügbaren Inhalt anpassen
        self.inner_content_frame.config(width=width, height=content_height)

        self.resize_after_id = None
        self.inner_content_frame.event_generate("<<ContentResized>>")


    def build_ui(self):
        # Titlebar
        self.titlebar = tk.Frame(self, bg="#2c2c2c", height=30)
        self.titlebar_id = self.create_window(0, 0, anchor="nw", window=self.titlebar)

        self.label = tk.Label(self.titlebar, text=self.app_name, bg="#2c2c2c", fg="white", font=("Segoe UI", 10))
        self.label.pack(side="left", padx=10)

        self.close_button = tk.Button(self.titlebar, text="✖", bg="#ff5c5c", fg="white",
                                      font=("Segoe UI", 10, "bold"), activebackground="#ff1c1c", borderwidth=0,
                                      command=self.close_app)
        self.close_button.pack(side="right", padx=2, pady=2)

        self.max_button = tk.Button(self.titlebar, text="□", bg="#2c2c2c", fg="white",
                                    font=("Segoe UI", 10, "bold"), borderwidth=0, command=self.maximize_restore_app)
        self.max_button.pack(side="right", padx=2, pady=2)

        self.min_button = tk.Button(self.titlebar, text="−", bg="#2c2c2c", fg="white",
                                    font=("Segoe UI", 10, "bold"), borderwidth=0, command=self.minimize_app)
        self.min_button.pack(side="right", padx=2, pady=2)

        # Content-Canvas ohne Scrollbar
        self.content_canvas = tk.Canvas(self, bg="#1e1e1e", highlightthickness=0)
        self.content_id = self.create_window(0, 30, anchor="nw", window=self.content_canvas)

        self.inner_content_frame = tk.Frame(self.content_canvas, bg="#1e1e1e", height=400)

        self.content_canvas_window = self.content_canvas.create_window((0, 0), window=self.inner_content_frame, anchor="nw")

        def update_scrollregion(event=None):
            bbox = self.content_canvas.bbox("all")
            if bbox:
                x1, y1, x2, y2 = bbox
                if y2 < self.content_canvas.winfo_height():
                    y2 = self.content_canvas.winfo_height()
                self.content_canvas.configure(scrollregion=(x1, y1, x2, y2))

        self.inner_content_frame.bind("<Configure>", update_scrollregion)
        self.content_canvas.bind("<Configure>", update_scrollregion)
        self.inner_content_frame.pack_propagate(False)

        # Resize-Event an Canvas binden
        self.bind("<Configure>", lambda e: self.update_canvas_size())

        # App-Inhalt laden
        self.app_main(self.inner_content_frame)

        # Resize Handle
        self.resize_handle = tk.Frame(self, bg="#444", cursor="bottom_right_corner", width=10, height=10)
        self.resize_handle_id = self.create_window(400, 430, anchor="se", window=self.resize_handle)

        # Fenster verschieben
        for widget in [self.titlebar, self.label]:
            widget.bind("<ButtonPress-1>", self.start_move)
            widget.bind("<B1-Motion>", self.do_move)
            widget.bind("<Double-Button-1>", self.toggle_maximize_restore)

        # Resize starten
        self.resize_handle.bind("<ButtonPress-1>", self.start_resize)
        self.resize_handle.bind("<B1-Motion>", self.do_resize)

    def update_canvas_size(self):
        width = self.winfo_width()
        height = self.winfo_height()
        titlebar_height = 30  # Höhe der Titelbar
        content_height = max(height - titlebar_height, 0)

        self.content_canvas.config(width=width, height=content_height)
        self.inner_content_frame.config(width=width)
        self.content_canvas.itemconfig(self.content_canvas_window, width=width)

        self.event_generate("<<ContentResized>>")

    def close_app(self):
        if self.app_name in self.gui.open_apps:
            button = self.gui.open_apps[self.app_name]["button"]
            button.destroy()
            del self.gui.open_apps[self.app_name]
        self.destroy()

    def minimize_app(self):
        self.saved_geometry = (self.winfo_x(), self.winfo_y(), self.winfo_width(), self.winfo_height())
        self.was_maximized = self.is_maximized
        self.place_forget()
        self.is_maximized = False

    def maximize_restore_app(self):
        if not self.is_maximized:
            if self._normal_geometry is None:
                self._normal_geometry = (self.winfo_x(), self.winfo_y(), self.winfo_width(), self.winfo_height())
            # Maximierung basierend auf der Höhe des Wurzels und der Titelbar
            self.place(x=0, y=0, width=self.gui.root.winfo_width(), height=self.gui.root.winfo_height() - 40)
            self.handle_resize()  # Größe anpassen
            self.master.tk.call("raise", self._w)
            self.is_maximized = True
            self.max_button.config(text="❐")
        else:
            if self._normal_geometry:
                x, y, w, h = self._normal_geometry
                self.place(x=x, y=y, width=w, height=h)
                self.handle_resize()  # Größe wiederherstellen
                self._normal_geometry = None
            self.master.tk.call("raise", self._w)
            self.is_maximized = False
            self.max_button.config(text="□")


    def toggle_maximize_restore(self, event=None):
        self.maximize_restore_app()

    def start_move(self, event):
        self.master.tk.call("raise", self._w)
        self._drag_data["x"] = event.x_root
        self._drag_data["y"] = event.y_root
        self.start_x = self.winfo_x()
        self.start_y = self.winfo_y()

    def do_move(self, event):
        if self.is_maximized:
            return
        dx = event.x_root - self._drag_data["x"]
        dy = event.y_root - self._drag_data["y"]
        new_x = self.start_x + dx
        new_y = self.start_y + dy

        max_width = self.gui.root.winfo_width() - self.winfo_width()
        max_height = self.gui.root.winfo_height() - self.winfo_height() - 40

        snap_margin = 20
        new_x = max(0, min(new_x, max_width))
        new_y = max(0, min(new_y, max_height))

        if abs(new_x) < snap_margin:
            new_x = 0
        if abs(new_y) < snap_margin:
            new_y = 0
        if abs(new_x - max_width) < snap_margin:
            new_x = max_width
        if abs(new_y - max_height) < snap_margin:
            new_y = max_height

        self.place(x=new_x, y=new_y)

    def start_resize(self, event):
        self._resize_data = {
            "x": event.x_root,
            "y": event.y_root,
            "width": self.winfo_width(),
            "height": self.winfo_height()
        }

    def do_resize(self, event):
        dx = event.x_root - self._resize_data["x"]
        dy = event.y_root - self._resize_data["y"]

        new_width = max(200, self._resize_data["width"] + dx)
        new_height = max(150, self._resize_data["height"] + dy)

        max_w = self.gui.root.winfo_width()
        max_h = self.gui.root.winfo_height() - 40

        new_width = min(new_width, max_w)
        new_height = min(new_height, max_h)

        if self.animate_resize:
            steps = 5
            for _ in range(steps):
                step_width = self.winfo_width() + (new_width - self.winfo_width()) // steps
                step_height = self.winfo_height() + (new_height - self.winfo_height()) // steps
                self.place(width=step_width, height=step_height)
                self.update()

        self.place(width=new_width, height=new_height)
        self.handle_resize()
