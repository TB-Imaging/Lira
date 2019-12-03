import sys
import numpy as np
import cv2
import tkinter as tk
import os
import glob
from tkinter import messagebox

from base import *
from UserProgress import UserProgress
from Images import Images
from TypeOneDetections import TypeOneDetections
from PredictionGrids import PredictionGrids
from tktools import center_left_window

archive_dir = "../data/user_progress/"


def get_user_list():
    users = ['.'.join(f.split('.')[:-1]) for f in os.listdir(archive_dir) if f.endswith('.json')]
    return users


def inputFolderLoaded():
    img_dir = "../../Input Images/"
    return len([fname for fname in fnames(img_dir)]) > 0


class BeginDialog(tk.Toplevel):

    def __init__(self, parent):
        tk.Toplevel.__init__(self, parent)
        self.title = "Title"
        self.users = ['-'] + list(sorted(get_user_list()))
        self.userSet = set(self.users[1:])
        self.var_user = tk.StringVar()
        self.var_user.set('-')
        self.userMenu = tk.OptionMenu(self, self.var_user, *self.users, command=self.setUser)
        self.userMenu.grid(row=0, column=1, columnspan=3, sticky=tk.W, padx=10, pady=5)
        tk.Button(self, text="Delete", command=self.deleteUser).grid(row=0, column=0, padx=10, pady=5)
        tk.Label(self, text="User ID:").grid(row=1)
        tk.Label(self, text="Model:").grid(row=2, column=0)
        tk.Label(self, text="Restart:").grid(row=3)
        # tk.Label(self, text="BALB/c").grid(row=4, columnspan=2, sticky=tk.E)

        self.var_uid = tk.StringVar()
        self.var_restart = tk.BooleanVar()
        self.var_model = tk.StringVar()
        self.var_model.set('kramnik')
        self.return_uid = ""
        self.return_restart = False
        self.return_model = 'kramnik'

        vcmd = (self.register(self.enterUser), '%P')
        self.uid = tk.Entry(self, textvariable=self.var_uid, validate="all",
                            validatecommand=vcmd)
        self.uid.grid(row=1, column=1, pady=10, padx=10, columnspan=2)
        self.reset = tk.Checkbutton(self, variable=self.var_restart, state=tk.DISABLED, command=self.restart)
        self.reset.grid(row=3, column=1, pady=5, sticky=tk.W)
        self.balbc = tk.Radiobutton(self, text="BALB/c", value="balbc", variable=self.var_model)
        self.balbc.grid(row=2, column=1, pady=0, sticky=tk.W)
        self.kramnik = tk.Radiobutton(self, text="Kramnik", value="kramnik", variable=self.var_model)
        self.kramnik.grid(row=2, column=2, pady=0, sticky=tk.W)
        beginButton = tk.Button(self, text="Begin", command=self.begin)
        cancelButton = tk.Button(self, text="Cancel", command=self.cancel)
        beginButton.grid(row=4, column=2, sticky=tk.E, pady=5, padx=5)
        cancelButton.grid(row=4, column=0, sticky=tk.W, padx=5)
        center_left_window(self, 274, 168)

    def restart(self):
        if self.var_restart.get():
            self.balbc.config(state=tk.NORMAL)
            self.kramnik.config(state=tk.NORMAL)
        else:
            self.balbc.config(state=tk.DISABLED)
            self.kramnik.config(state=tk.DISABLED)

    def enterUser(self, ustring):
        if ustring not in self.userSet:
            self.var_user.set('-')
            self.var_restart.set(False)
            self.reset.config(state=tk.DISABLED)
            self.balbc.config(state=tk.NORMAL)
            self.kramnik.config(state=tk.NORMAL)
        else:
            self.var_user.set(ustring)
            self.reset.config(state=tk.NORMAL)
            if not self.var_restart.get():
                self.balbc.config(state=tk.DISABLED)
                self.kramnik.config(state=tk.DISABLED)
        return True

    def begin(self):
        # Assigning these variables to ensure that the program only continues
        # if the user clicks "begin"; otherwise program cancels.
        if self.var_restart.get() and not tk.messagebox.askyesno("Are You Sure?", "Are you sure you want to "
                                                                                  "restart and delete your "
                                                                                  "progress?".format(
                                                                                    self.var_user.get())):
            return
        if self.var_uid.get() == "":
            messagebox.showwarning("Empty User ID", "User ID is required.")
        elif self.var_uid.get() == "-":
            messagebox.showwarning("Bad ID", "Inappropriate User ID. Use a different User ID.")
        elif inputFolderLoaded():
            self.return_uid = self.var_uid.get()
            self.return_restart = self.var_restart.get()
            self.return_model = self.var_model.get()
            self.destroy()
        else:
            messagebox.showwarning("Empty Input", "No files in the input directory!")

    def setUser(self, str):
        if self.var_user.get() == '-':
            self.var_uid.set('')
        else:
            self.var_uid.set(self.var_user.get())
        self.reset.config(state=tk.NORMAL)

    def deleteUser(self):
        if self.var_user.get() == '-':
            return
        if not tk.messagebox.askyesno("Are You Sure?", "Are you sure you want to delete '{}'?".format(
            self.var_user.get())):
            return
        data_dir = "../data"
        # data_folders =
        user_file = self.var_user.get() + '.json'
        user_img_prefix = self.var_user.get() + '_img_'
        data_path1 = os.path.join(data_dir, '*', user_img_prefix) + '[0-9].npy'
        data_path2 = os.path.join(data_dir, '*', user_img_prefix) + '[0-9][0-9].npy'
        data_path3 = os.path.join(data_dir, '*', user_img_prefix) + '[0-9][0-9][0-9].npy'
        data_files = glob.glob(data_path1) + glob.glob(data_path2) + glob.glob(data_path3)
        # print(user_file, data_path1, data_files)
        for file in data_files:
            os.remove(file)
        os.remove(os.path.join(archive_dir, user_file))
        self.users = ['-'] + list(sorted(get_user_list()))
        self.userSet = set(self.users[1:])
        self.var_user.set('-')
        self.var_uid.set('')
        self.userMenu.grid_forget()
        self.userMenu = tk.OptionMenu(self, self.var_user, *self.users, command=self.setUser)
        self.userMenu.grid(row=0, column=1, columnspan=3, sticky=tk.W, padx=10, pady=5)

    def show(self):
        self.wm_deiconify()
        self.uid.focus_force()
        self.wait_window()
        return self.return_uid, self.return_restart, self.return_model

    def cancel(self):
        self.destroy()


class Dataset(object):
    # To store all our subdatasets throughout our pipeline and manage progress throughout pipeline

    def __init__(self, uid=None, restart=None, dialog=True):
        # Get uid if needed

        if dialog:
            root = tk.Tk()
            root.title("L.I.R.A.")
            root.withdraw()

            bd = BeginDialog(root)
            bd.resizable(False, False)
            uid, restart, model = bd.show()
            root.destroy()

            if uid != "":
                self.uid = uid
                self.restart = restart
                self.model = model
            else:
                sys.exit("Exiting...")

        if uid is not None:
            self.uid = uid
        else:
            self.uid = input("Input your Unique/User ID for this Dataset: ")

        # Initialize user progress to existing progress if it exists and default starting progress otherwise
        self.progress = UserProgress(self.uid, model=self.model)
        # Check whether to reload the imgs archive, and possibly restart our progress
        if restart is not None:
            self.restart = restart
        else:
            self.restart = input(
                "Would you like to reset your classification progress and restart from the beginning? (This will "
                "re-load all images) [Y\\N]: ").upper() == "Y "

        if self.restart:
            # User wants to restart, both imgs and progress
            self.imgs = Images(restart=True)
            self.progress.restart(model=self.model)
            self.type_one_detections = TypeOneDetections(self, self.uid, restart=True)
            self.prediction_grids = PredictionGrids(self, self.uid, restart=True)

        else:
            # User does not want to restart. Defaults to this if they didn't put in "Y"
            if self.progress.editing_started():
                # If they were already editing these images, resume progress
                self.imgs = Images(restart=False)
                self.type_one_detections = TypeOneDetections(self, self.uid, restart=False)
                self.prediction_grids = PredictionGrids(self, self.uid, restart=False)
            else:
                # If they weren't already editing these images (i.e. they haven't started editing), load the images.
                # No need to restart our progress since it's already the initial value.
                self.imgs = Images(restart=True)
                self.type_one_detections = TypeOneDetections(self, self.uid, restart=True)
                self.prediction_grids = PredictionGrids(self, self.uid, restart=True)

    def detect_type_ones(self, kivy=False):
        # Detect type ones, suppress them, and allow human-in-the-loop editing. If our user progress indicates they
        # have already done some or all of these steps, we will skip over the already-completed steps.

        # Only generate if user hasn't started editing (meaning they already had them generated before)
        if not self.progress["type_ones_started_editing"]:
            self.type_one_detections.generate()

        # Only edit if the user hasn't finished editing
        if not self.progress["type_ones_finished_editing"] and not kivy:
            self.type_one_detections.edit()

    def predict_grids(self):
        # Detect all predictions and allow human-in-the-loop editing If our user progress indicates they have already
        # done some or all of these steps, we will skip over the already-completed steps.

        # Only generate if user hasn't started editing (meaning they already had them generated before)
        if not self.progress["prediction_grids_started_editing"]:
            self.prediction_grids.generate()

        # Only edit if the user hasn't finished editing
        if not self.progress["prediction_grids_finished_editing"]:
            self.prediction_grids.edit()

    def get_stats(self):
        # Once we're sure the user's session is complete:
        if self.progress["prediction_grids_finished_editing"]:

            # Generate a CSV with raw counts of each classification on each image,
            #   with the percentages each classification takes up of the image,
            #   not including empty slide,
            #   and the number of type one lesions detected on each image.
            with open("../../Output Stats/{}_stats.csv".format(self.uid), "w") as f:
                # Write Header line
                f.write("Image,Healthy Tissue,Type I - Caseum,Type II,Type III,Type I - Rim,Unknown/Misc,\
                        ,Healthy Tissue,Type I - Caseum,Type II,Type III,Type I - Rim,Unknown/Misc,\
                        ,Number of Type One Lesions\n")

                # Iterate through predictions and detections
                for i, (prediction_grid, detections) in enumerate(
                        zip(self.prediction_grids.after_editing, self.type_one_detections.after_editing)):
                    sys.stdout.write("\rGenerating Stats on Image {}/{}...".format(i, len(self.imgs) - 1))

                    # Get counts of each classification type, excluding empty slide
                    prediction_counts = np.zeros((6))
                    classification_i = 0
                    for classification in range(7):
                        if classification != 3:
                            prediction_counts[classification_i] = np.sum(prediction_grid == classification)
                            classification_i += 1

                    # Get total number of classifications for this image
                    prediction_n = np.sum(prediction_counts)

                    # Get percentage each classification takes up of the total classifications
                    prediction_avgs = 100 * prediction_counts / prediction_n

                    # Get the number of Type One Lesions / Type One Detection Clusters in this image
                    detection_count = len(get_rect_clusters(detections))

                    # Write
                    f.write("{},{},,{},,{}\n".format(self.imgs.fnames[i], ",".join(map(str, list(prediction_counts))),
                                                     ",".join(map(str, list(prediction_avgs))), detection_count))

                sys.stdout.flush()
                print("")

            # Generate a displayable image of the predictions overlaid, for each image.
            resize_factor = 1 / 8
            color_key = [(255, 0, 255), (0, 0, 255), (0, 255, 0), (200, 200, 200), (0, 255, 255), (255, 0, 0),
                         (244, 66, 143)]
            alpha = 0.33
            for i, (img, prediction_grid) in enumerate(zip(self.imgs, self.prediction_grids.after_editing)):
                sys.stdout.write("\rGenerating Displayable Results for Image {}/{}...".format(i, len(self.imgs) - 1))

                # Since our image and predictions would be slightly misalgned from each other due to rounding,
                # We recompute the sub_h and sub_w and img resize factors to make them aligned.
                sub_h = int(resize_factor * self.prediction_grids.sub_h)
                sub_w = int(resize_factor * self.prediction_grids.sub_w)
                fy = (prediction_grid.shape[0] * sub_h) / img.shape[0]
                fx = (prediction_grid.shape[1] * sub_w) / img.shape[1]

                # Then resize the image with these new factors
                img = cv2.resize(img, (0, 0), fx=fx, fy=fy)

                # Make overlay to store prediction rectangles on before overlaying on top of image
                prediction_overlay = np.zeros_like(img)

                for row_i, row in enumerate(prediction_grid):
                    for col_i, col in enumerate(row):
                        color = color_key[col]
                        # draw rectangles of the resized sub_hxsub_w size on it
                        cv2.rectangle(prediction_overlay, (col_i * sub_w, row_i * sub_h),
                                      (col_i * sub_w + sub_w, row_i * sub_h + sub_h), color, -1)

                # Add overlay to image to get resulting image
                display_img = weighted_overlay(img, prediction_overlay, alpha)

                # Write img
                cv2.imwrite("../../Output Stats/{}_overlay_{}.png".format(self.uid, self.imgs.fnames[i]), display_img)

            sys.stdout.flush()
            print("")
