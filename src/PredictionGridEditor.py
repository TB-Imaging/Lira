import sys

import cv2
import numpy as np
import os
from tkinter import *
from tkinter import messagebox
from PIL import ImageTk, Image

from Tooltip import createTooltip
from gui_base import *
from base import *
from tktools import center_left_window


class GetResizeTransparencyDialog(Toplevel):

    def __init__(self, parent):
        Toplevel.__init__(self, parent)
        self.parent = parent
        self.title = "Title"
        Label(self, text="Transparency Factor").grid(row=0, column=0, columnspan=2, padx=10, pady=5)
        Label(self, text="Resize Factor").grid(row=2, column=0, columnspan=2, padx=10, pady=5)
        self.resizeVar = DoubleVar()
        self.transparencyVar = DoubleVar()
        self.resizeVar.set(1.0)
        self.transparencyVar.set(1.0)
        self.transparencyScale = Scale(
            self,
            from_=0,
            to=1,
            resolution=0.01,
            variable=self.transparencyVar,
            orient=HORIZONTAL
        )
        self.resizeScale = Scale(
            self,
            from_=0,
            to=1,
            resolution=0.01,
            variable=self.resizeVar,
            orient=HORIZONTAL
        )
        self.transparencyScale.grid(row=1, column=0, columnspan=2, sticky=E + W, padx=10, pady=5)
        self.resizeScale.grid(row=3, column=0, columnspan=2, sticky=E + W, padx=10, pady=5)
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        acceptButton = Button(self, text="Accept", command=self.accept)
        cancelButton = Button(self, text="Cancel", command=self.cancel)
        acceptButton.grid(row=4, column=1, sticky=E, pady=5, padx=5)
        cancelButton.grid(row=4, column=0, sticky=W, padx=5)

    def show(self):
        self.wm_deiconify()
        self.wait_window()
        return self.resizeVar.get(), self.transparencyVar.get()

    def accept(self):
        self.destroy()

    def cancel(self):
        self.transparencyVar.set(-1)
        self.resizeVar.set(-1)
        self.destroy()


class PredictionGridEditor(object):
    def __init__(self, dataset):
        # Initialize our editor on this user's last edited image
        self.dataset = dataset
        root = Tk()
        root.title("L.I.R.A.")
        root.withdraw()
        center_left_window(root, 0, 0)
        # Ask them if they want to change the current values for resize and transparency if
        if messagebox.askyesno("Change Values",
                               "Would you like to change the transparency and resize factors from their current "
                               "values? (These are the default values if you have not started editing)"):
            dialog = GetResizeTransparencyDialog(root)
            center_left_window(dialog, 158, 193)
            dialog.resizable(False, False)
            self.editor_resize_factor, self.editor_transparency_factor = dialog.show()
            if self.editor_transparency_factor < 0.01 or self.editor_transparency_factor < 0.01:
                self.editor_resize_factor = self.dataset.progress["prediction_grids_resize_factor"]
                self.editor_transparency_factor = self.dataset.progress["prediction_grids_transparency_factor"]
            root.destroy()
        else:
            # Just use the current values
            self.editor_resize_factor = self.dataset.progress["prediction_grids_resize_factor"]
            self.editor_transparency_factor = self.dataset.progress["prediction_grids_transparency_factor"]
            root.destroy()

        # Parameters
        self.classification_key = ["Healthy Tissue", "Type I - Caseum", "Type II", "Empty Slide", "Type III",
                                   "Type I - Rim", "Unknown/Misc."]
        self.color_key = [(255, 0, 255), (0, 0, 255), (0, 255, 0), (200, 200, 200), (0, 255, 255), (255, 0, 0),
                          (244, 66, 143)]
        self.color_index = 3
        self.title = "L.I.R.A. Prediction Grid Editing"

        self.tools = ["pencil", "draw-square", "paint-bucket", "zoom"]
        self.tool_cursors = ["pencil", "crosshair", "coffee_mug", "target"]
        self.tool_icons = ["pencil-alt-solid.png", "edit-solid.png", "fill-drip-solid.png", "search-plus-solid.png"]
        tool_tips = ["Pencil tool", "Color selected rectangle", "Fill tool", "Zoom in on selected area"]
        self.tool_index = -1
        base_dir = os.path.dirname(os.getcwd())
        icon_dir = os.path.join(base_dir, 'icons')
        # Img + Predictions
        self.reload_img_and_predictions()

        # Window + Frame
        self.window = Tk()
        self.window.protocol("WM_DELETE_WINDOW", self.q_key_press)
        self.frame = Frame(self.window, bd=5, relief=SUNKEN)
        self.frame.grid(row=0, column=0)
        self.main_canvas_frame = Frame(self.frame)
        self.main_canvas_frame.pack()
        # Hard-code choice of resolution for main canvas, and hard-set scroll region as maximum shape of images
        self.main_canvas = Canvas(
            self.main_canvas_frame,
            bg="#000000",
            width=1366,
            height=700,
            scrollregion=(0, 0, self.dataset.imgs.max_shape()[1], self.dataset.imgs.max_shape()[0]),
        )

        # Create palette and toolbar
        self.toolbar = Frame(self.frame)
        self.toolbar.pack(side=LEFT)
        self.palette = Frame(self.frame)
        self.palette.pack(side=LEFT)

        # Scrollbars
        hbar = Scrollbar(self.main_canvas_frame, orient=HORIZONTAL)
        hbar.pack(side=BOTTOM, fill=X)
        hbar.config(command=self.main_canvas.xview)
        vbar = Scrollbar(self.main_canvas_frame, orient=VERTICAL)
        vbar.pack(side=RIGHT, fill=Y)
        vbar.config(command=self.main_canvas.yview)
        self.main_canvas.config(xscrollcommand=hbar.set, yscrollcommand=vbar.set)
        buttonFrame = Frame(self.window, bd=5)
        finishButton = Button(buttonFrame, text="Continue", command=self.finish_button_press)
        quitButton = Button(buttonFrame, text="Quit", command=self.q_key_press)

        leftrightFrame = Frame(buttonFrame)
        self.leftButton = Button(leftrightFrame, text="◀", command=self.left_arrow_key_press)
        self.rightButton = Button(leftrightFrame, text="▶", command=self.right_arrow_key_press)
        self.updating_img = False

        buttonFrame.grid(row=1, column=0, sticky=W + E)
        quitButton.pack(side=LEFT)
        finishButton.pack(side=RIGHT)
        leftrightFrame.pack()
        # begin with the leftButton hidden, and only show the rightButton if there are multiple
        # images
        if len(self.dataset.imgs) > 1 and self.dataset.progress["prediction_grids_image"] > 0:
            self.leftButton.pack(side=LEFT)
        if len(self.dataset.imgs) > 1 and self.dataset.progress["prediction_grids_image"] < len(self.dataset.imgs) - 1:
            self.rightButton.pack(side=RIGHT)

        # Title
        self.window.title("{} - Image {}/{}".format(self.title, self.dataset.progress["prediction_grids_image"] + 1,
                                                    len(self.dataset.prediction_grids.before_editing)))

        # Img + Event listeners
        self.main_canvas.image = ImageTk.PhotoImage(
            Image.fromarray(self.img))  # Literally because tkinter can't handle references properly and needs this.
        self.main_canvas.config(scrollregion=(0, 0, self.main_canvas.image.width(), self.main_canvas.image.height()))
        self.main_canvas_image_config = self.main_canvas.create_image(0, 0, image=self.main_canvas.image,
                                                                      anchor="nw")  # So we can change the image later
        self.main_canvas.focus_set()
        self.main_canvas.bind_all("<Button-4>", self.mouse_scroll)  # Scrollwheel for entire editor
        self.main_canvas.bind_all("<Button-5>", self.mouse_scroll)  # Scrollwheel for entire editor
        self.main_canvas.bind("<Left>", self.left_arrow_key_press)
        self.main_canvas.bind("<Right>", self.right_arrow_key_press)
        self.main_canvas.bind("<Key>", self.key_press)
        self.main_canvas.pack(side=TOP)

        self.toolButtons = []
        self.iconImages = []
        icon_color_str = "#%02x%02x%02x" % (180, 180, 180)

        self.buttonFrame = Frame(self.frame)

        self.buttonFrame.pack(side=LEFT)

        self.undo_img = Image.open(os.path.join(icon_dir, "undo-solid.png"))
        self.undo_img = self.undo_img.resize((20, 20), Image.ANTIALIAS)
        self.undo_img = ImageTk.PhotoImage(self.undo_img)
        self.undoButton = Button(
            self.buttonFrame,
            relief=SUNKEN,
            state=DISABLED,
            command=self.undo,
            bg=icon_color_str,
            image=self.undo_img
        )
        self.undoButton.pack()
        self.undos = []

        self.clear_img = Image.open(os.path.join(icon_dir, "eye-slash-solid.png"))
        self.clear_img = self.clear_img.resize((20, 20), Image.ANTIALIAS)
        self.clear_img = ImageTk.PhotoImage(self.clear_img)
        self.clearButton = Button(
            self.buttonFrame,
            relief=FLAT,
            command=self.clear_predictions,
            bg=icon_color_str,
            image=self.clear_img
        )
        self.clearButton.pack()
        createTooltip(self.undoButton, 'Undo last edit')
        createTooltip(self.clearButton, 'Set all classifications to Healthy Tissue')

        def change_tool(index):
            return lambda: self.changeTool(index)

        for i, icon in enumerate(self.tool_icons):
            icon_path = os.path.join(icon_dir, icon)
            icon_img = Image.open(icon_path)
            icon_img = icon_img.resize((20, 20), Image.ANTIALIAS)
            icon_img = ImageTk.PhotoImage(icon_img)
            self.iconImages.append(icon_img)
            tool_cmd = change_tool(i)
            self.toolButtons.append(
                Button(self.toolbar, relief=FLAT, command=tool_cmd, bg=icon_color_str, image=self.iconImages[i])
            )
            if i == self.tool_index:
                self.toolButtons[i].config(relief=SUNKEN, state=DISABLED)
            self.toolButtons[i].pack()
            createTooltip(self.toolButtons[i], tool_tips[i])

        self.paletteButtons = []

        def change_color(index):
            return lambda: self.changeColor(index)

        # Side Canvas
        for i, (classification, color) in enumerate(zip(self.classification_key, self.color_key)):
            # Since our colors are in BGR, and tkinter only accepts hex, we have to create a hex string for them,
            # in RGB order.
            b, g, r = color
            hex_color_str = "#%02x%02x%02x" % (r, g, b)

            # We then check get the color's brightness using the relative luminance algorithm
            # https://en.wikipedia.org/wiki/Relative_luminance
            color_brightness = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255
            if color_brightness < 0.5:
                # Dark color, bright font.
                text_color = "white"
            else:
                # Bright color, dark font.
                text_color = "black"

            # Then we generate our colored label string to include the keyboard shortcut for this classification
            color_cmd = change_color(i)

            button_str = "{}: {}".format(i, classification)
            self.paletteButtons.append(
                Button(self.palette, text=button_str, bg=hex_color_str, fg=text_color, relief=FLAT,
                       command=color_cmd)
            )
            if i == self.color_index:
                self.paletteButtons[i].config(relief=SUNKEN, state=DISABLED)
            if i < 4:
                self.paletteButtons[i].grid(sticky=W + E, row=i, column=0)
            else:
                self.paletteButtons[i].grid(sticky=W + E, row=i - 4, column=1)

        # Add left mouse and right mouse

        # Keeping track of which mouse button is currently held down
        self.left_mouse = False

        # So that if the user tries to insert classifications before they've selected any we will not do anything
        self.prediction_rect_x1 = 0
        self.prediction_rect_y1 = 0
        self.prediction_rect_x2 = 0
        self.prediction_rect_y2 = 0

        # Predictions and start
        self.window.mainloop()

    def clear_predictions(self):
        self.add_undo()

        self.prediction_grid[self.prediction_grid != 3] = 0

        # Save updated predictions
        self.dataset.prediction_grids.after_editing[
            self.dataset.progress["prediction_grids_image"]] = self.prediction_grid

        # Load the resized image section (without any overlay) referenced by our current classification_selection
        # rectangle (no need to cast to int b/c int*int = int)
        self.img_section = self.resized_img[:, :]

        # Create new overlay on this resized image section with the prediction grid section
        self.prediction_overlay_section = np.zeros_like(self.img_section)
        for row_i, row in enumerate(self.prediction_grid):
            for col_i, col in enumerate(row):
                color = self.color_key[col]
                # draw rectangles of the resized sub_hxsub_w size on it
                cv2.rectangle(self.prediction_overlay_section, (col_i * self.sub_w, row_i * self.sub_h),
                              (col_i * self.sub_w + self.sub_w, row_i * self.sub_h + self.sub_h), color, -1)

        # Combine the overlay section and the image section
        before_img_section = self.img_section
        self.img_section = weighted_overlay(self.img_section, self.prediction_overlay_section,
                                            self.editor_transparency_factor)
        self.img_section = cv2.cvtColor(self.img_section,
                                        cv2.COLOR_BGR2RGB)  # We need to convert so it will display the proper colors

        # Insert the now-updated image section back into the full image
        self.img[:, :] = self.img_section

        # And finally update the canvas
        self.main_canvas.image = ImageTk.PhotoImage(
            Image.fromarray(self.img))  # Literally because tkinter can't handle references properly and needs this.
        self.main_canvas.itemconfig(self.main_canvas_image_config, image=self.main_canvas.image)

    def undo(self):
        if len(self.undos) == 0:
            return
        self.prediction_grid, self.img = self.undos.pop()
        self.dataset.prediction_grids.after_editing[
            self.dataset.progress["prediction_grids_image"]] = self.prediction_grid
        self.main_canvas.image = ImageTk.PhotoImage(
            Image.fromarray(self.img))  # Literally because tkinter can't handle references properly and needs this.
        self.main_canvas.itemconfig(self.main_canvas_image_config, image=self.main_canvas.image)
        if len(self.undos) == 0:
            self.undoButton.config(state=DISABLED, relief=SUNKEN)

    def add_undo(self):
        if len(self.undos) == 0:
            self.undoButton.config(state=NORMAL, relief=FLAT)
        self.undos.append((np.copy(self.prediction_grid), np.copy(self.img)))
        if len(self.undos) > 20:
            self.undos = self.undos[1:]

    def clear_undos(self):
        self.undos = []
        self.undoButton.config(state=DISABLED, relief=SUNKEN)

    def changeColor(self, index):
        if index >= len(self.paletteButtons):
            return
        if self.color_index > -1:
            self.paletteButtons[self.color_index].config(relief=FLAT, state=NORMAL)
        self.paletteButtons[index].config(relief=SUNKEN, state=DISABLED)
        self.color_index = index

    def changeTool(self, index):
        if self.tool_index > -1:
            self.toolButtons[self.tool_index].config(relief=FLAT, state=NORMAL)
        self.toolButtons[index].config(relief=SUNKEN, state=DISABLED)
        self.tool_index = index
        self.main_canvas.config(cursor=self.tool_cursors[index])
        # "pencil", "draw-square", "paint-bucket", "zoom"
        if self.tools[index] == "pencil":
            self.main_canvas.bind("<Button 1>", self.pencil_click)  # mouse_click
            self.main_canvas.bind("<B1-Motion>", self.pencil_move)  # mouse_move
            self.main_canvas.unbind("<ButtonRelease-1>")
        elif self.tools[index] == "draw-square":
            self.main_canvas.bind("<Button 1>", self.draw_square_click)  # mouse_click
            self.main_canvas.bind("<B1-Motion>", self.draw_square_move)  # mouse_move
            self.main_canvas.bind("<ButtonRelease-1>", self.draw_square_release)  # mouse_left_release
        elif self.tools[index] == "paint-bucket":
            self.main_canvas.bind("<Button 1>", self.paint_bucket_click)  # mouse_click
            self.main_canvas.unbind("<B1-Motion>")
            self.main_canvas.unbind("<ButtonRelease-1>")
        elif self.tools[index] == "zoom":
            self.main_canvas.bind("<Button 1>", self.zoom_click)  # mouse_click
            self.main_canvas.bind("<B1-Motion>", self.zoom_move)  # mouse_move
            self.main_canvas.bind("<ButtonRelease-1>", self.zoom_release)  # mouse_left_release

    # The following functions are event handlers for our editing window.
    def pencil_click(self, event):
        self.add_undo()
        self.pencil_move(event)

    def pencil_move(self, event):

        self.selection_x1, self.selection_y1 = get_canvas_coordinates(
            event)  # Get rectangle coordinates from our initial mouse click point to this point
        rect_x1, rect_y1, rect_x2, rect_y2 = get_rectangle_coordinates(
            self.selection_x1, self.selection_y1,
            self.selection_x1, self.selection_y1
        )

        # Get coordinates for a new rectangle outline with this new rectangle
        outline_rect_x1, outline_rect_y1, outline_rect_x2, outline_rect_y2 = get_outline_rectangle_coordinates(
            rect_x1,
            rect_y1,
            rect_x2,
            rect_y2,
            self.sub_h,
            self.sub_w
        )
        self.prediction_rect_x1 = int(outline_rect_x1 / self.sub_w)
        self.prediction_rect_y1 = int(outline_rect_y1 / self.sub_h)
        self.prediction_rect_x2 = int(outline_rect_x2 / self.sub_w)
        self.prediction_rect_y2 = int(outline_rect_y2 / self.sub_h)

        self.fill_selected_area()

    def draw_square_click(self, event):
        # Start a selection rect.
        # Our rectangle selections can only be made up of small rectangles of size sub_h*sub_w, so that we lock on to areas in these step sizes to allow easier rectangle selection.

        # Get coordinates on canvas for beginning of this selection, (x1, y1)
        self.selection_x1, self.selection_y1 = get_canvas_coordinates(event)

        # Get coordinates for a rectangle outline with this point as both top-left and bot-right of the rectangle and draw it
        outline_rect_x1, outline_rect_y1, outline_rect_x2, outline_rect_y2 = get_outline_rectangle_coordinates(
            self.selection_x1, self.selection_y1, self.selection_x1, self.selection_y1, self.sub_h, self.sub_w)
        self.main_canvas.create_rectangle(outline_rect_x1, outline_rect_y1, outline_rect_x2, outline_rect_y2,
                                          fill='', outline="darkRed", width=2, tags="classification_selection")

    def draw_square_move(self, event):
        # Move the selection rect. Our rectangle selections can only be made up of small rectangles of size
        # sub_h*sub_w, so that we lock on to areas in these step sizes to allow easier rectangle selection.

        # Get coordinates on canvas for the current end of this selection, (x2, y2)
        self.selection_x2, self.selection_y2 = get_canvas_coordinates(event)

        # Get rectangle coordinates from our initial mouse click point to this point
        rect_x1, rect_y1, rect_x2, rect_y2 = get_rectangle_coordinates(
            self.selection_x1, self.selection_y1,
            self.selection_x2, self.selection_y2
        )

        # Get coordinates for a new rectangle outline with this new rectangle
        outline_rect_x1, outline_rect_y1, outline_rect_x2, outline_rect_y2 = get_outline_rectangle_coordinates(
            rect_x1,
            rect_y1,
            rect_x2,
            rect_y2,
            self.sub_h,
            self.sub_w
        )

        # Delete old selection rectangle and draw new one with this new rectangle outline
        # Left Mouse Move
        self.main_canvas.delete("classification_selection")
        self.main_canvas.create_rectangle(outline_rect_x1, outline_rect_y1, outline_rect_x2, outline_rect_y2,
                                          fill='', outline="darkRed", width=2, tags="classification_selection")

    def draw_square_release(self, event):
        # Set the selection rect and save its location for referencing our prediction grid. Our rectangle selections
        # can only be made up of small rectangles of size sub_h*sub_w, so that we lock on to areas in these step
        # sizes to allow easier rectangle selection.

        # Get coordinates on canvas for the end of this selection, (x2, y2)
        self.selection_x2, self.selection_y2 = get_canvas_coordinates(event)

        # Get rectangle coordinates from our initial mouse click point to this point
        rect_x1, rect_y1, rect_x2, rect_y2 = get_rectangle_coordinates(self.selection_x1, self.selection_y1,
                                                                       self.selection_x2, self.selection_y2)

        # Get coordinates for a new rectangle outline with this new rectangle
        outline_rect_x1, outline_rect_y1, outline_rect_x2, outline_rect_y2 = get_outline_rectangle_coordinates(
            rect_x1,
            rect_y1,
            rect_x2,
            rect_y2,
            self.sub_h,
            self.sub_w
        )

        # Delete old selection rectangle and draw new finalized selection rectangle at this position
        self.main_canvas.delete("classification_selection")
        self.main_canvas.create_rectangle(outline_rect_x1, outline_rect_y1, outline_rect_x2, outline_rect_y2, fill='',
                                          outline="red", width=2, tags="classification_selection")

        # Save the location of this outline rectangle relative to predictions so we can later update classifications
        # in this area
        self.prediction_rect_x1 = int(outline_rect_x1 / self.sub_w)
        self.prediction_rect_y1 = int(outline_rect_y1 / self.sub_h)
        self.prediction_rect_x2 = int(outline_rect_x2 / self.sub_w)
        self.prediction_rect_y2 = int(outline_rect_y2 / self.sub_h)

        self.add_undo()
        self.fill_selected_area()
        self.main_canvas.delete("classification_selection")

    def paint_bucket_click(self, event):
        self.add_undo()
        # Get coordinates on canvas for beginning of this selection, (x1, y1)
        self.selection_x1, self.selection_y1 = get_canvas_coordinates(event)
        outline_rect_x1, outline_rect_y1, outline_rect_x2, outline_rect_y2 = get_outline_rectangle_coordinates(
            self.selection_x1, self.selection_y1, self.selection_x1, self.selection_y1, self.sub_h, self.sub_w)

        self.prediction_rect_x1 = int(outline_rect_x1 / self.sub_w)
        self.prediction_rect_y1 = int(outline_rect_y1 / self.sub_h)
        self.prediction_rect_x2 = int(outline_rect_x2 / self.sub_w)
        self.prediction_rect_y2 = int(outline_rect_y2 / self.sub_h)
        if self.prediction_rect_x1 == self.prediction_rect_x2:
            self.prediction_rect_x2 += 1
        if self.prediction_rect_y1 == self.prediction_rect_y2:
            self.prediction_rect_y2 += 1
        i = self.color_index
        square_color_i = self.prediction_grid[self.prediction_rect_y1:self.prediction_rect_y2,
                         self.prediction_rect_x1:self.prediction_rect_x2][0][0]

        # Save updated predictions
        fill_bound_x1 = self.prediction_rect_x1
        fill_bound_x2 = self.prediction_rect_x2
        fill_bound_y1 = self.prediction_rect_y1
        fill_bound_y2 = self.prediction_rect_y2

        # take care of filling adjacent squares with an iterative implementation
        # of recursion, using a stack because Python is scared of normal recursion

        rect_stack = [(self.prediction_rect_x1, self.prediction_rect_x2,
                       self.prediction_rect_y1, self.prediction_rect_y2)]
        while len(rect_stack) > 0:
            rect_x1, rect_x2, rect_y1, rect_y2 = rect_stack.pop()
            new_i = self.color_index
            if new_i == square_color_i:
                continue
            if rect_x1 < 0 or rect_y1 < 0 or \
                    rect_x2 > self.prediction_grid.shape[1] or rect_y2 > self.prediction_grid.shape[0]:
                continue
            if fill_bound_x1 > rect_x1:
                fill_bound_x1 = rect_x1
            if fill_bound_x2 < rect_x2:
                fill_bound_x2 = rect_x2
            if fill_bound_y1 > rect_y1:
                fill_bound_y1 = rect_y1
            if fill_bound_y2 < rect_y2:
                fill_bound_y2 = rect_y2
            self.prediction_grid[rect_y1:rect_y2, rect_x1:rect_x2] = new_i
            if rect_x2 + 1 <= self.prediction_grid.shape[1] and \
                    self.prediction_grid[rect_y1:rect_y2, rect_x1 + 1:rect_x2 + 1][0][
                        0] == square_color_i:
                rect_stack.append((rect_x1 + 1, rect_x2 + 1, rect_y1, rect_y2))
            if rect_x1 - 1 >= 0 and \
                    self.prediction_grid[rect_y1:rect_y2, rect_x1 - 1:rect_x2 - 1][0][0].item() == square_color_i:
                rect_stack.append((rect_x1 - 1, rect_x2 - 1, rect_y1, rect_y2))
            if rect_y2 + 1 <= self.prediction_grid.shape[0] and \
                    self.prediction_grid[rect_y1 + 1:rect_y2 + 1, rect_x1:rect_x2][0][0].item() == square_color_i:
                rect_stack.append((rect_x1, rect_x2, rect_y1 + 1, rect_y2 + 1))
            if rect_y1 - 1 >= 0 and \
                    self.prediction_grid[rect_y1 - 1:rect_y2 - 1, rect_x1:rect_x2][0][0].item() == square_color_i:
                rect_stack.append((rect_x1, rect_x2, rect_y1 - 1, rect_y2 - 1))

        self.dataset.prediction_grids.after_editing[
            self.dataset.progress["prediction_grids_image"]] = self.prediction_grid
        img_section = self.resized_img[
                      fill_bound_y1 * self.sub_h:fill_bound_y2 * self.sub_h,
                      fill_bound_x1 * self.sub_w:fill_bound_x2 * self.sub_w
                      ]
        prediction_grid_section = self.prediction_grid[
                                  fill_bound_y1:fill_bound_y2,
                                  fill_bound_x1:fill_bound_x2
                                  ]
        prediction_overlay_section = np.zeros_like(img_section)
        for row_i, row in enumerate(prediction_grid_section):
            for col_i, col in enumerate(row):
                color = self.color_key[col]
                # draw rectangles of the resized sub_hxsub_w size on it
                cv2.rectangle(
                    prediction_overlay_section,
                    (col_i * self.sub_w, row_i * self.sub_h),
                    (col_i * self.sub_w + self.sub_w, row_i * self.sub_h + self.sub_h),
                    color,
                    -1
                )

        img_section = weighted_overlay(img_section, prediction_overlay_section,
                                       self.editor_transparency_factor)
        img_section = cv2.cvtColor(img_section,
                                   cv2.COLOR_BGR2RGB)
        self.img[fill_bound_y1 * self.sub_h:fill_bound_y2 * self.sub_h,
                 fill_bound_x1 * self.sub_w:fill_bound_x2 * self.sub_w] = img_section

        # And finally update the canvas
        self.main_canvas.image = ImageTk.PhotoImage(
            Image.fromarray(self.img))  # Literally because tkinter can't handle references properly and needs this.
        self.main_canvas.itemconfig(self.main_canvas_image_config, image=self.main_canvas.image)

    def zoom_click(self, event):
        # Start a selection rect. Our rectangle selections can only be made up of small rectangles of size
        # sub_h*sub_w, so that we lock on to areas in these step sizes to allow easier rectangle selection.

        # Get coordinates on canvas for beginning of this selection, (x1, y1)
        self.selection_x1, self.selection_y1 = get_canvas_coordinates(event)

        # Get coordinates for a rectangle outline with this point as both top-left and bot-right of the rectangle and
        # draw it
        outline_rect_x1, outline_rect_y1, outline_rect_x2, outline_rect_y2 = get_outline_rectangle_coordinates(
            self.selection_x1, self.selection_y1, self.selection_x1, self.selection_y1, self.sub_h, self.sub_w)
        # Right Mouse Click
        self.main_canvas.create_rectangle(outline_rect_x1, outline_rect_y1, outline_rect_x2, outline_rect_y2,
                                          fill='', outline="darkBlue", width=2, tags="view_selection")

    def zoom_move(self, event):
        # Move the selection rect. Our rectangle selections can only be made up of small rectangles of size
        # sub_h*sub_w, so that we lock on to areas in these step sizes to allow easier rectangle selection.

        # Get coordinates on canvas for the current end of this selection, (x2, y2)
        self.selection_x2, self.selection_y2 = get_canvas_coordinates(event)

        # Get rectangle coordinates from our initial mouse click point to this point
        rect_x1, rect_y1, rect_x2, rect_y2 = get_rectangle_coordinates(self.selection_x1, self.selection_y1,
                                                                       self.selection_x2, self.selection_y2)

        # Get coordinates for a new rectangle outline with this new rectangle
        outline_rect_x1, outline_rect_y1, outline_rect_x2, outline_rect_y2 = get_outline_rectangle_coordinates(
            rect_x1,
            rect_y1,
            rect_x2,
            rect_y2,
            self.sub_h,
            self.sub_w
        )

        # Delete old selection rectangle and draw new one with this new rectangle outline
        # Left Mouse Move
        self.main_canvas.delete("view_selection")
        self.main_canvas.create_rectangle(outline_rect_x1, outline_rect_y1, outline_rect_x2, outline_rect_y2,
                                          fill='', outline="darkBlue", width=2, tags="view_selection")

    def zoom_release(self, event):
        # Set the selection rect and open up the selected area in a separate window at full resolution. Our rectangle
        # selections can only be made up of small rectangles of size sub_h*sub_w, so that we lock on to areas in
        # these step sizes to allow easier rectangle selection.

        # Get coordinates on canvas for the end of this selection, (x2, y2)
        self.selection_x2, self.selection_y2 = get_canvas_coordinates(event)

        # Get rectangle coordinates from our initial mouse click point to this point
        rect_x1, rect_y1, rect_x2, rect_y2 = get_rectangle_coordinates(self.selection_x1, self.selection_y1,
                                                                       self.selection_x2, self.selection_y2)

        # Get coordinates for a new rectangle outline with this new rectangle
        outline_rect_x1, outline_rect_y1, outline_rect_x2, outline_rect_y2 = get_outline_rectangle_coordinates(rect_x1,
                                                                                                               rect_y1,
                                                                                                               rect_x2,
                                                                                                               rect_y2,
                                                                                                               self.sub_h,
                                                                                                               self.sub_w)

        # Delete old selection rectangle and draw new finalized selection rectangle at this position
        self.main_canvas.delete("view_selection")
        self.main_canvas.create_rectangle(outline_rect_x1, outline_rect_y1, outline_rect_x2, outline_rect_y2, fill='',
                                          outline="blue", width=2, tags="view_selection")

        # Open up a separate window and display the full-resolution version of the selection
        self.display_image_section(outline_rect_x1, outline_rect_y1, outline_rect_x2, outline_rect_y2)
        self.main_canvas.delete("view_selection")

    def mouse_scroll(self, event):
        if event.num == 4:
            # scroll down
            self.main_canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            # scroll up
            self.main_canvas.yview_scroll(1, "units")

    def update_img(self):
        self.window.title(
            "{} - Image {}/{} - Loading...".format(self.title, self.dataset.progress["prediction_grids_image"] + 1,
                                                   len(self.dataset.prediction_grids.before_editing)))
        self.window.update()

        # Reload self.img and self.prediction_grid
        self.reload_img_and_predictions()

        # Reload image displayed on canvas and predictions displayed on canvas with self.img and
        # self.prediction_grids
        self.main_canvas.image = ImageTk.PhotoImage(
            Image.fromarray(self.img))  # Literally because tkinter can't handle references properly and needs this.
        self.main_canvas.itemconfig(self.main_canvas_image_config, image=self.main_canvas.image)
        self.main_canvas.delete("view_selection")
        self.main_canvas.delete("classification_selection")

        # Indicate finished loading
        self.window.title("{} - Image {}/{}".format(self.title, self.dataset.progress["prediction_grids_image"] + 1,
                                                    len(self.dataset.prediction_grids.before_editing)))
        self.main_canvas.config(scrollregion=(0, 0, self.main_canvas.image.width(), self.main_canvas.image.height()))
        self.main_canvas.yview_moveto(0)
        self.main_canvas.xview_moveto(0)

    def left_arrow_key_press(self, event=None):
        # prevent multiple simultaneous calls
        if self.updating_img:
            return
        # Move to the image with index i-1, unless i = 0, in which case we do nothing. AKA the previous image.
        if self.dataset.progress["prediction_grids_image"] > 0:
            self.updating_img = True
            self.clear_undos()
            # Save current predictions
            self.dataset.prediction_grids.after_editing[
                self.dataset.progress["prediction_grids_image"]] = self.prediction_grid

            # Change current editing image
            self.dataset.progress["prediction_grids_image"] -= 1
            if self.dataset.progress["prediction_grids_image"] == 0:
                self.leftButton.pack_forget()
            if self.dataset.progress["prediction_grids_image"] == len(self.dataset.imgs) - 2:
                self.rightButton.pack(side=RIGHT)
            self.update_img()
            self.updating_img = False

    def right_arrow_key_press(self, event=None):
        # prevent multiple simultaneous calls
        if self.updating_img:
            return
        # Move to the image with index i+1, unless i = img #-1, in which case we do nothing. AKA the next image.
        if self.dataset.progress["prediction_grids_image"] < len(self.dataset.imgs) - 1:
            self.updating_img = True
            self.clear_undos()
            # Save current predictions
            self.dataset.prediction_grids.after_editing[
                self.dataset.progress["prediction_grids_image"]] = self.prediction_grid

            # Change current editing image
            self.dataset.progress["prediction_grids_image"] += 1
            if self.dataset.progress["prediction_grids_image"] == len(self.dataset.imgs) - 1:
                self.rightButton.pack_forget()
            if self.dataset.progress["prediction_grids_image"] == 1:
                self.leftButton.pack(side=LEFT)
            self.update_img()
            self.updating_img = False


    def fill_selected_area(self):
        # Change currently selected area to this classification. We update the prediction grid, but we also update
        # the display by extracting the selected section and updating the overlay of only that section,
        # because updating the entire image is very expensive and should be avoided. First get the classification index
        i = self.color_index
        # Update predictions referenced by our current classification_selection rectangle to this index and get the
        # prediction grid section that was updated
        self.prediction_grid[
            self.prediction_rect_y1:self.prediction_rect_y2,
            self.prediction_rect_x1:self.prediction_rect_x2
        ] = i
        self.prediction_grid_section = self.prediction_grid[self.prediction_rect_y1:self.prediction_rect_y2,
                                       self.prediction_rect_x1:self.prediction_rect_x2]

        # Save updated predictions
        self.dataset.prediction_grids.after_editing[
            self.dataset.progress["prediction_grids_image"]] = self.prediction_grid

        # if the rectangle is flat in either dimension, nothing should happen.
        if self.prediction_rect_y2 == self.prediction_rect_y1 or self.prediction_rect_x2 == self.prediction_rect_x1:
            return

        # Load the resized image section (without any overlay) referenced by our current classification_selection
        # rectangle (no need to cast to int b/c int*int = int)
        self.img_section = self.resized_img[self.prediction_rect_y1 * self.sub_h:self.prediction_rect_y2 * self.sub_h,
                           self.prediction_rect_x1 * self.sub_w:self.prediction_rect_x2 * self.sub_w]

        # Create new overlay on this resized image section with the prediction grid section
        self.prediction_overlay_section = np.zeros_like(self.img_section)
        for row_i, row in enumerate(self.prediction_grid_section):
            for col_i, col in enumerate(row):
                color = self.color_key[col]
                # draw rectangles of the resized sub_hxsub_w size on it
                cv2.rectangle(self.prediction_overlay_section, (col_i * self.sub_w, row_i * self.sub_h),
                              (col_i * self.sub_w + self.sub_w, row_i * self.sub_h + self.sub_h), color, -1)

        # Combine the overlay section and the image section
        before_img_section = self.img_section
        self.img_section = weighted_overlay(self.img_section, self.prediction_overlay_section,
                                            self.editor_transparency_factor)
        self.img_section = cv2.cvtColor(self.img_section,
                                        cv2.COLOR_BGR2RGB)  # We need to convert so it will display the proper colors

        # Insert the now-updated image section back into the full image
        self.img[self.prediction_rect_y1 * self.sub_h:self.prediction_rect_y2 * self.sub_h,
        self.prediction_rect_x1 * self.sub_w:self.prediction_rect_x2 * self.sub_w] = self.img_section

        # And finally update the canvas
        self.main_canvas.image = ImageTk.PhotoImage(
            Image.fromarray(self.img))  # Literally because tkinter can't handle references properly and needs this.
        self.main_canvas.itemconfig(self.main_canvas_image_config, image=self.main_canvas.image)

    def q_key_press(self, event=None):
        if messagebox.askquestion(
                'Quit',
                'Would you like to quit?'
        ) == 'yes':
            sys.exit("Exiting...")

    def finish_button_press(self, event=None):
        if messagebox.askokcancel(
                "Save and Continue",
                "Would you like to save and generate displayable results? Once you continue, your edits can not be "
                "undone."):
            self.window.destroy()
            self.dataset.progress["prediction_grids_finished_editing"] = True

    def key_press(self, event):
        # Hub for all key press events.
        c = event.char.upper()
        if c == "Q":
            self.q_key_press(event)
        elif c.isnumeric():
            i = int(c)
            self.changeColor(i)

    # The following functions are helper functions specific to this editor. All other GUI helpers are in the gui_base.py file.
    def reload_img_and_predictions(self):
        # Updates the self.img and self.predictions attributes.

        # Also updates sub_h and sub_w since the prediction overlay depends on these
        self.sub_h = int(self.dataset.prediction_grids.sub_h * self.editor_resize_factor)
        self.sub_w = int(self.dataset.prediction_grids.sub_w * self.editor_resize_factor)

        self.img = self.dataset.imgs[self.dataset.progress["prediction_grids_image"]]  # Load img
        self.prediction_grid = self.dataset.prediction_grids.after_editing[
            self.dataset.progress["prediction_grids_image"]]  # Load prediction grid

        # Since our image and predictions would be slightly misalgned from each other due to rounding,
        # We compute the fx and fy img resize factors according to sub_h and sub_w to make them aligned.
        self.fy = (self.prediction_grid.shape[0] * self.sub_h) / self.img.shape[0]
        self.fx = (self.prediction_grid.shape[1] * self.sub_w) / self.img.shape[1]

        self.img = cv2.resize(self.img, (0, 0), fx=self.fx, fy=self.fy)  # Resize img
        self.resized_img = self.img  # Save this so we don't have to resize later

        # Make overlay to store prediction rectangles on before overlaying on top of image
        self.prediction_overlay = np.zeros_like(self.img)

        for row_i, row in enumerate(self.prediction_grid):
            for col_i, col in enumerate(row):
                color = self.color_key[col]
                # draw rectangles of the resized sub_hxsub_w size on it
                cv2.rectangle(self.prediction_overlay, (col_i * self.sub_w, row_i * self.sub_h),
                              (col_i * self.sub_w + self.sub_w, row_i * self.sub_h + self.sub_h), color, -1)

        self.img = weighted_overlay(self.img, self.prediction_overlay,
                                    self.editor_transparency_factor)  # Overlay prediction grid onto image
        self.img = cv2.cvtColor(self.img, cv2.COLOR_BGR2RGB)  # We need to convert so it will display the proper colors

    def display_image_section(self, x1, y1, x2, y2):
        # Given coordinates for an image section on the current resized image, get the coordinates for an image section on the full-resolution / non-resized image,
        # Then get this section on the full resolution image and display it on a new window.

        # Get updated coordinates
        x1 = int(x1 / self.fx)
        y1 = int(y1 / self.fy)
        x2 = int(x2 / self.fx)
        y2 = int(y2 / self.fy)

        # Get image section
        self.img_section = self.dataset.imgs[self.dataset.progress["prediction_grids_image"]][y1:y2, x1:x2]

        # Display image section on a new tkinter window
        top = Toplevel()
        top.title("Full Resolution Image Section")
        frame = Frame(top, bd=5, relief=SUNKEN)
        frame.grid(row=0, column=0)
        canvas = Canvas(frame, bg="#000000", width=self.img_section.shape[1], height=self.img_section.shape[0])
        canvas.image = ImageTk.PhotoImage(Image.fromarray(
            self.img_section))  # Literally because tkinter can't handle references properly and needs this.
        canvas.create_image(0, 0, image=canvas.image, anchor="nw")
        canvas.pack()
