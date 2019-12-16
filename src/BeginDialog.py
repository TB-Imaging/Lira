import tkinter as tk
from tkinter import messagebox
import os
import json
import glob

from base import *
from tktools import center_left_window

progress_dir = "../data/user_progress/"


def get_user_list():
    users = ['.'.join(f.split('.')[:-1]) for f in os.listdir(progress_dir) if f.endswith('.json')]
    return users


def inputFolderLoaded():
    img_dir = "../../Input Images/"
    return len([fname for fname in fnames(img_dir)]) > 0


class BeginDialog(tk.Toplevel):

    def __init__(self, parent):
        tk.Toplevel.__init__(self, parent)
        self.title = "Title"
        self.users = ['-'] + list(sorted(get_user_list(), key=lambda s: s.lower()))
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

    def update_model(self):
        uid = self.var_user.get()
        progress_file = os.path.join(progress_dir, "{}.json".format(uid))
        with open(progress_file, 'r') as f:
            progress = json.load(f)
            if "model" in progress:
                self.var_model.set(progress["model"])
            else:
                self.var_model.set("kramnik")


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
        elif not inputFolderLoaded() and (self.var_restart.get() or self.var_uid.get() not in self.userSet):
            messagebox.showwarning("Empty Input", "No files in the input directory!")
        else:
            self.return_uid = self.var_uid.get()
            self.return_restart = self.var_restart.get()
            self.return_model = self.var_model.get()
            self.destroy()

    def setUser(self, _):
        if self.var_user.get() == '-':
            self.var_uid.set('')
        else:
            self.var_uid.set(self.var_user.get())
            self.update_model()
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
        clear_dir(
            data_dir,
            lambda f:
                f.startswith(user_img_prefix) and
                f[len(user_img_prefix):-4].isnumeric(),
            recursive=True
        )
        os.remove(os.path.join(progress_dir, user_file))
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