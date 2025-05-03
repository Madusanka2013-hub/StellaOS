import tkinter as tk
from datetime import datetime

class CanvasShortcut:
    def __init__(self, canvas, app_name, gui, x=0, y=0):
        self.canvas = canvas
        self.app_name = app_name
        self.gui = gui

        self.icon_id = self.canvas.create_text(
            x, y,
            text="🗂",
            font=("Segoe UI", 32),
            fill="white"
        )
        self.label_id = self.canvas.create_text(
            x, y + 42,
            text=app_name,
            font=("Segoe UI", 9),
            fill="white"
        )

        self.items = [self.icon_id, self.label_id]

        for item in self.items:
            self.canvas.tag_bind(item, "<Button-1>", self.start_drag)
            self.canvas.tag_bind(item, "<B1-Motion>", self.on_drag)
            self.canvas.tag_bind(item, "<ButtonRelease-1>", self.stop_drag)
            self.canvas.tag_bind(item, "<Button-3>", self.right_click_menu)

        self._drag_data = {"x": 0, "y": 0}
        self._click_time = None
        self._was_dragged = False

    def start_drag(self, event):
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y
        self._click_time = datetime.now()
        self._was_dragged = False

    def on_drag(self, event):
        dx = event.x - self._drag_data["x"]
        dy = event.y - self._drag_data["y"]
        if abs(dx) > 3 or abs(dy) > 3:
            self._was_dragged = True

        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()

        x, y = self.canvas.coords(self.icon_id)
        new_x = x + dx
        new_y = y + dy

        icon_w, icon_h = 32, 32
        new_x = max(0, min(new_x, canvas_w - icon_w))
        new_y = max(0, min(new_y, canvas_h - icon_h - 16))

        delta_x = new_x - x
        delta_y = new_y - y

        for item in self.items:
            self.canvas.move(item, delta_x, delta_y)

        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def stop_drag(self, event):
        duration = (datetime.now() - self._click_time).total_seconds()
        if not self._was_dragged and duration < 0.3:
            self.gui.launch_app(self.app_name)
        else:
            x, y = self.canvas.coords(self.icon_id)
            mode = "max" if self.gui.is_maximized() else "normal"
            self.gui.shortcut_positions.setdefault(self.app_name, {})[mode] = [x, y]
            self.gui.save_config()

    def right_click_menu(self, event):
        menu = tk.Menu(self.canvas, tearoff=0,
                       bg="#292a2d",
                       fg="#e8eaed",
                       activebackground="#5f6368",
                       activeforeground="white",
                       bd=0,
                       relief="flat",
                       font=("Segoe UI", 10))
        menu.add_command(label="Verknüpfung löschen", command=self.delete_shortcut)
        menu.tk_popup(event.x_root, event.y_root)

    def delete_shortcut(self):
        self.gui.remove_shortcut(self.app_name)
