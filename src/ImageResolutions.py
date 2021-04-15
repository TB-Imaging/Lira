import tkinter as tk
from tkinter import messagebox
import os
import sys
import cv2
import numpy as np
from PIL import ImageTk, Image

from base import *
from tktools import center_left_window

class ImageResolutions(tk.Toplevel):

    def __init__(self, parent, images_pathnames):
        tk.Toplevel.__init__(self, parent)
        self.finished = False
        self.images_pathnames = list(images_pathnames)

        self.resolutions = [[0.41, 0.41] for i in self.images_pathnames]

        self.title = "Image Resolutions"
        self.index = 0
        self.lastButton = tk.Button(self, text="Previous", command=self.previousImage,
                                    state=tk.DISABLED)
        self.lastButton.grid(row=3, column=0, padx=10, pady=5)
        self.nextButton = tk.Button(self, text="Next", command=self.nextImage)
        self.nextButton.grid(row=3, column=2, padx=10, pady=5)
        if len(self.resolutions) == 1:
            self.nextButton.config(state=tk.DISABLED)
        tk.Label(self, text="Input the resolution for each image before proceeding").grid(
            row=0, column=0, columnspan=3, padx=5)
        tk.Label(self, text="Resolution X:").grid(row=1, column=0, sticky=tk.E)
        tk.Label(self, text="           Y:").grid(row=2, column=0, sticky=tk.E)
        tk.Label(self, text="microns/pixel").grid(row=1, column=2)
        tk.Label(self, text="microns/pixel").grid(row=2, column=2)

        self.canvasFrame = tk.Frame(self, bd=5, relief=tk.SUNKEN)
        self.canvasFrame.grid(row=5, column=0, columnspan=3)

        self.img = None
        self.loadImage()  # assign self.img

        self.canvas = tk.Canvas(
            self.canvasFrame,
            bg="#000000",
            width=280,
            height=280,
            # scrollregion=(
            #     0, 0, 200, 500
            # )
        )
        self.canvas.image = ImageTk.PhotoImage(
            Image.fromarray(self.img))  # Literally because tkinter can't handle references properly and needs this.
        self.canvas.config(scrollregion=(0, 0, self.canvas.image.width(), self.canvas.image.height()))
        self.canvas_image_config = self.canvas.create_image(
            0, 0,
            image=self.canvas.image,
            anchor="nw"
        )  # So we can change the image later
        self.canvas.pack(side=tk.LEFT)

        self.var_resX = tk.DoubleVar(self, 0.41)
        vcmdx = (self.register(self.validateResX), '%P')
        self.resX = tk.Entry(self, textvariable=self.var_resX, validate="all",
                            validatecommand=vcmdx, width=5)
        self.resX.grid(row=1, column=1, pady=10, padx=10, columnspan=1)

        self.var_resY = tk.DoubleVar(self, 0.41)
        vcmdy = (self.register(self.validateResY), '%P')
        self.resY = tk.Entry(self, textvariable=self.var_resY, validate="all",
                            validatecommand=vcmdy, width=5)
        self.resY.grid(row=2, column=1, pady=10, padx=10, columnspan=1)

        self.fileName = tk.Label(self, text=self.images_pathnames[self.index][1])
        self.fileName.grid(row=4, column=0, columnspan=3, sticky=tk.E+tk.W)

        finishButton = tk.Button(self, text="Finish", command=self.finish)
        finishButton.grid(row=6, column=2, sticky=tk.E, pady=5, padx=10)
        # center_left_window(self, 340, 493)

    def loadImage(self):

        print(self.images_pathnames[self.index][0])
        self.img = np.load(self.images_pathnames[self.index][0])
        # self.img = cv2.resize(self.img, (0, 0), switching to thumbnails
        #                       fx=280 / self.img.shape[1],
        #                       fy=280 / self.img.shape[0])
        self.img = cv2.cvtColor(self.img, cv2.COLOR_BGR2RGB)  # We need to convert so it will display the proper colors

    def validateResX(self, numstring):
        try:
            self.resolutions[self.index][0] = float(numstring)
            return len(numstring) <= 5
        except ValueError:
            return False

    def validateResY(self, numstring):
        try:
            self.resolutions[self.index][1] = float(numstring)
            return len(numstring) <= 5
        except ValueError:
            return False

    def previousImage(self):
        print("index:", self.index, "image:", self.images_pathnames[self.index][1], 'path:', self.images_pathnames[
            self.index][0])
        if self.index > 0: self.index -= 1
        if self.index == 0:
            self.lastButton.config(state=tk.DISABLED)
        self.nextButton.config(state=tk.NORMAL)
        self.var_resX.set(self.resolutions[self.index][0])
        self.var_resY.set(self.resolutions[self.index][1])
        self.fileName.config(text=self.images_pathnames[self.index][1])
        self.updateImage()

    def nextImage(self):
        print("index:", self.index, "image:", self.images_pathnames[self.index][1], 'path:', self.images_pathnames[
            self.index][0])
        if self.index < len(self.images_pathnames) - 1: self.index += 1
        if self.index == len(self.images_pathnames) - 1:
            self.nextButton.config(state=tk.DISABLED)
        self.lastButton.config(state=tk.NORMAL)
        self.var_resX.set(self.resolutions[self.index][0])
        self.var_resY.set(self.resolutions[self.index][1])
        self.fileName.config(text=self.images_pathnames[self.index][1])
        self.updateImage()

    def updateImage(self):
        self.loadImage()
        self.canvas.image = ImageTk.PhotoImage(
            Image.fromarray(self.img))
        self.canvas.itemconfig(self.canvas_image_config, image=self.canvas.image)

    def finish(self):
        if not tk.messagebox.askyesno("Are You Finished?",
            "Are you ready to proceed?"):
            return
        for res in self.resolutions:
            if res[0] == 0 or res[1] == 0:
                messagebox.showwarning("Invalid Entry",
                                        "One or more of the input resolutions is/are 0.0. "
                                        "Please ensure that all resolutions are valid "
                                        "before proceeding.")
                return
        self.finished = True
        self.destroy()

    def show(self):
        self.wm_deiconify()
        self.wait_window()
        if not self.finished:
            sys.exit('Exiting...')
        return self.resolutions

    def cancel(self):
        self.destroy()