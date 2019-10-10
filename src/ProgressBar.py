import threading
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import sys

from tktools import center_left_window

class AsyncProgressBar(threading.Thread):
    def __init__(self, tk_root, steps, label, callback):
        self.root = tk_root
        self.steps = steps
        self.label = label
        self.callback = callback
        threading.Thread.__init__(self)
        self.daemon = True
        self.progress = ttk.Progressbar(
            self.root,
            orient=tk.HORIZONTAL,
            length=300,
            mode="determinate",
        )
        self.progressText = tk.StringVar()
        progressLabel = tk.Label(self.root, textvariable=self.progressText)
        progressLabel.pack(pady=5, padx=10)
        self.progress.pack(pady=5, padx=10)
        self.start()

    def run(self):
        for i in range(self.steps):
            self.progressText.set('{}: {}/{} Complete'.format(
                self.label,
                i,
                self.steps
            ))
            self.progress['value'] = 100 * i / self.steps
            self.root.update()
            self.callback(i)
        self.root.destroy()


class AsyncProgressRoot(tk.Tk):
    def __init__(self, steps, label, callback):
        tk.Tk.__init__(self)
        self.title("L.I.R.A.")
        self.resizable(False, False)
        center_left_window(self, 320, 57)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.progressBar = AsyncProgressBar(
            self,
            steps,
            label,
            callback
        )

    def on_closing(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.destroy()
            # archiver.stop()
            sys.exit()