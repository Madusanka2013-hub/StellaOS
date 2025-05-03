import tkinter as tk
import platform

class BaseTkApp:
    def __init__(self, root, parent):
        self.root = root
        self.parent = parent
        self.width = 0
        self.height = 0

        self.container = tk.Frame(self.parent)
        self.container.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(self.container, bg="#1e1e1e", highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)

        self.scrollbar = tk.Scrollbar(
            self.container,
            orient="vertical",
            command=self.canvas.yview,
            bg="#1e1e1e",
            troughcolor="#2c2c2c",
            activebackground="#555555",
            relief="flat",
            bd=0
        )
        self.scrollbar.pack(side="right", fill="y")

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.content_frame = tk.Frame(self.canvas, bg="#1e1e1e")
        self.canvas_window = self.canvas.create_window((0, 0), window=self.content_frame, anchor="nw")

        self.content_frame.bind("<Configure>", self.on_content_configure)
        self.parent.bind("<<ContentResized>>", self.handle_resize_event)
        self.root.after(100, self.setup_initial)
        self.canvas.bind("<Configure>", self.on_canvas_configure)

        self.bind_mousewheel()
        self.canvas.bind("<Enter>", lambda e: self.canvas.focus_set())

    def bind_mousewheel(self):
        system = platform.system()
        widgets = [self.canvas, self.content_frame]

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
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def on_content_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.parent.event_generate("<<ContentResized>>")

    def handle_resize_event(self, event):
        self.width = self.parent.winfo_width()
        self.height = self.parent.winfo_height()


class MyApp(BaseTkApp):
    def __init__(self, root, parent):
        super().__init__(root, parent)
        self.populate_ui()

    def populate_ui(self):
        for i in range(50):
            label = tk.Label(self.content_frame, text=f"Zeile {i + 1}", bg="#1e1e1e", fg="#ffffff", font=("Segoe UI", 12))
            label.pack(anchor="w", padx=10, pady=5)


def main(parent=None):
    if parent is None:
        root = tk.Tk()
        root.title("My Tkinter App mit Scrollbar + Mausrad")
        frame = tk.Frame(root, width=600, height=400)
        frame.pack(fill="both", expand=True)
        app = MyApp(root, frame)
        root.mainloop()
    else:
        MyApp(parent.master, parent)


if __name__ == "__main__":
    main()
