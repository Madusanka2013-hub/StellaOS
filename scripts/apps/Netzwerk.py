import tkinter as tk
from tkinter import ttk, filedialog
import platform
import psutil
import time
import csv
import threading
import subprocess
import re

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


class NetwatchApp(BaseTkApp):
    def __init__(self, root, parent):
        super().__init__(root, parent)
        self.last_bytes = psutil.net_io_counters()
        self.last_time = time.time()
        self.download_history = []
        self.upload_history = []
        self.latency = 0
        self.max_points = 60
        self.interface = list(psutil.net_if_stats().keys())[0]
        self.show_upload = tk.BooleanVar(value=True)
        self.show_download = tk.BooleanVar(value=True)

        self.build_ui()
        self.update_graph()
        self.root.after(1000, self.update_latency_label)
        self.ping_thread = threading.Thread(target=self.ping_loop, daemon=True)
        self.ping_thread.start()

    def build_ui(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TLabel", background="#1e1e1e", foreground="white")
        style.configure("TButton", background="#333333", foreground="white", relief="flat")
        style.configure("TCheckbutton", background="#1e1e1e", foreground="white")
        style.configure("TCombobox", fieldbackground="#2a2a2a", background="#2a2a2a", foreground="white")

        top = tk.Frame(self.content_frame, bg="#1e1e1e")
        top.pack(fill="x", pady=5)
        ttk.Label(top, text="Netzwerkmonitor", font=("Segoe UI", 14, "bold"), anchor="center").pack()

        controls = tk.Frame(self.content_frame, bg="#1e1e1e")
        controls.pack(fill="x", padx=10, pady=5)
        ttk.Label(controls, text="Adapter:").pack(side="left")
        self.adapter_box = ttk.Combobox(controls, values=list(psutil.net_if_stats().keys()), width=18, state="readonly")
        self.adapter_box.current(0)
        self.adapter_box.pack(side="left", padx=(5, 10))
        self.adapter_box.bind("<<ComboboxSelected>>", self.change_adapter)

        ttk.Checkbutton(controls, text="⬇ Download", variable=self.show_download).pack(side="left", padx=5)
        ttk.Checkbutton(controls, text="⬆ Upload", variable=self.show_upload).pack(side="left", padx=5)
        ttk.Button(controls, text="Export CSV", command=self.export_csv).pack(side="right")

        self.graph_canvas = tk.Canvas(self.content_frame, bg="#121212", height=250, highlightthickness=0)
        self.graph_canvas.pack(fill="x", padx=10, pady=10)

        self.label_down = ttk.Label(self.content_frame, font=("Segoe UI", 10))
        self.label_down.pack(anchor="w", padx=10)
        self.label_up = ttk.Label(self.content_frame, font=("Segoe UI", 10))
        self.label_up.pack(anchor="w", padx=10)
        self.label_latency = ttk.Label(self.content_frame, font=("Segoe UI", 10))
        self.label_latency.pack(anchor="w", padx=10, pady=(0, 5))

    def change_adapter(self, event):
        self.interface = self.adapter_box.get()
        self.download_history.clear()
        self.upload_history.clear()

    def get_speed(self):
        now = time.time()
        current = psutil.net_io_counters(pernic=True).get(self.interface)
        if not current:
            return 0, 0
        elapsed = now - self.last_time
        self.last_time = now
        down = (current.bytes_recv - self.last_bytes.bytes_recv) * 8 / (elapsed * 1024 * 1024)
        up = (current.bytes_sent - self.last_bytes.bytes_sent) * 8 / (elapsed * 1024 * 1024)
        self.last_bytes = current
        return max(0, down), max(0, up)

    def export_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv")
        if not path:
            return
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Download (Mbit/s)", "Upload (Mbit/s)"])
            for d, u in zip(self.download_history, self.upload_history):
                writer.writerow([f"{d:.2f}", f"{u:.2f}"])

    def ping_loop(self):
        while True:
            try:
                output = subprocess.check_output(
                    ["ping", "-n", "1", "8.8.8.8"] if platform.system() == "Windows" else ["ping", "-c", "1", "8.8.8.8"],
                    stderr=subprocess.DEVNULL
                ).decode()
                match = re.search(r'time[=<]?(\d+\.?\d*)', output)
                if match:
                    self.latency = float(match.group(1))
                else:
                    self.latency = -1
            except:
                self.latency = -1
            time.sleep(5)

    def update_latency_label(self):
        self.label_latency.config(text=f"📡 Ping: {self.latency:.1f} ms" if self.latency >= 0 else "📡 Ping: -")
        self.root.after(1000, self.update_latency_label)

    def update_graph(self):
        w = self.graph_canvas.winfo_width()
        h = self.graph_canvas.winfo_height()
        self.graph_canvas.delete("all")
        down, up = self.get_speed()
        self.download_history.append(down)
        self.upload_history.append(up)

        if len(self.download_history) > self.max_points:
            self.download_history.pop(0)
            self.upload_history.pop(0)

        peak = max(self.download_history + self.upload_history + [1])
        scale = h / peak

        for i in range(6):
            y = h - i * h / 5
            self.graph_canvas.create_line(0, y, w, y, fill="#2a2a2a")

        x_step = w / self.max_points
        for i in range(1, len(self.download_history)):
            x1, x2 = (i - 1) * x_step, i * x_step
            if self.show_download.get():
                y1, y2 = h - self.download_history[i - 1] * scale, h - self.download_history[i] * scale
                self.graph_canvas.create_line(x1, y1, x2, y2, fill="#00ccff", width=2)
            if self.show_upload.get():
                y1u, y2u = h - self.upload_history[i - 1] * scale, h - self.upload_history[i] * scale
                self.graph_canvas.create_line(x1, y1u, x2, y2u, fill="#ff6600", width=2)

        self.label_down.config(text=f"⬇ Download: {down:.2f} Mbit/s")
        self.label_up.config(text=f"⬆ Upload: {up:.2f} Mbit/s")
        self.root.after(1000, self.update_graph)

    def resize(self):
        pass


def main(parent=None):
    if parent is None:
        root = tk.Tk()
        root.title("Netzwerkmonitor")
        frame = tk.Frame(root, width=900, height=600)
        frame.pack(fill="both", expand=True)
        app = NetwatchApp(root, frame)
        root.mainloop()
    else:
        NetwatchApp(parent.master, parent)


if __name__ == "__main__":
    main()