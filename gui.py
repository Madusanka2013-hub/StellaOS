import tkinter as tk
from core.windows_gui import Windows7GUI

if __name__ == "__main__":
    root = tk.Tk()
    app = Windows7GUI(root)
    root.app = app
    root.mainloop()
