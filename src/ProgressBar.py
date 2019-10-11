import threading
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import sys
import time

from tktools import center_left_window

class AsyncProgressWorker(threading.Thread):
    def __init__(self, steps, callback):
        self.steps = steps
        self.step = 0
        self.callback = callback
        threading.Thread.__init__(self)
        self.daemon = True
        self.start()

    def run(self):
        for i in range(self.steps):
            self.callback(i)
            self.step += 1


class ProgressRoot(tk.Tk):
    def __init__(self, steps, label, callback):
        self.steps = steps
        self.label = label
        tk.Tk.__init__(self)
        self.title("L.I.R.A.")
        self.resizable(False, False)
        center_left_window(self, 320, 87)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.progress = ttk.Progressbar(
            self,
            orient=tk.HORIZONTAL,
            length=300,
            mode="determinate",
        )
        self.indeterminateProgress = ttk.Progressbar(
            self, orient=tk.HORIZONTAL,
            length=300,
            mode="indeterminate"
        )
        self.progressText = tk.StringVar()
        progressLabel = tk.Label(self, textvariable=self.progressText)
        progressLabel.pack(pady=5, padx=10)
        self.progress.pack(pady=5, padx=10)
        self.indeterminateProgress.pack(pady=5, padx=10)
        self.progressWorker = AsyncProgressWorker(
            steps=steps,
            callback=callback
        )
        self.after(0, self.updateProgressBar)

    def on_closing(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.destroy()
            sys.exit()

    def updateProgressBar(self):
        while self.progressWorker.step < self.steps:
            time.sleep(0.1)
            self.indeterminateProgress.step(5)
            step = self.progressWorker.step
            self.progress['value'] = 100 * step / self.steps
            self.progressText.set('{}: {}/{} Complete'.format(
                self.label,
                step,
                self.steps
            ))
            self.update()
        self.destroy()
