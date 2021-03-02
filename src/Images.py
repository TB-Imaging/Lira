import sys
import cv2
import numpy as np
import os
from pathlib import Path
import json
import openslide
from tkinter import *
from tkinter import messagebox
import tkfilebrowser
from PIL import ImageTk, Image
import czifile as czf
from openslide_python_fix import _load_image_lessthan_2_29, _load_image_morethan_2_29

from convert_vsi import convert_vsi
from LiraExceptions import InputEmptyError
from base import *
from ProgressBar import ProgressRoot
from ImageResolutions import ImageResolutions

def q_key_press(event=None):
    if messagebox.askquestion(
        'Quit',
        'Would you like to quit?'
    ) == 'yes':
        sys.exit('Exiting...')

def read_openslide_img(img_file):
    """
    Opens img_file, converts to PIL image,
    and returns the image.
    Args:
                img_file : File name
              upper_left : the (x,y) coordinates of the .svs image_ext
    Output:
            Returns tuple of PIL images
    """
    img = openslide.open_slide(img_file)
    w_rec, h_rec = img.dimensions
    w_rec_half = w_rec // 2
    if (h_rec * w_rec) >= 2 ** 29:
        openslide.lowlevel._load_image = _load_image_morethan_2_29
    else:
        openslide.lowlevel._load_image = _load_image_lessthan_2_29
    if w_rec * h_rec >= 2 ** 29:
        try:
            region1 = img.read_region((0, 0),
                                      0, (w_rec_half, h_rec)).convert('RGB')

            region2 = img.read_region((w_rec_half,
                                       0),
                                      0, ((w_rec - w_rec_half), h_rec)).convert('RGB')
            return region1, region2

        except IOError:
            region1 = img.read_region((0, 0),
                                      0, (w_rec, h_rec)).convert('RGB')
            return region1,
    else:
        region1 = img.read_region((0, 0),
                                  0, (w_rec, h_rec)).convert('RGB')
        return region1,

class Images(object):
    """
    Since this class references hard disk files at directories set
        in the class initialization,, reading and writing to any instance
        of this class will read and write the exact same images
        as other instances.
    """

    def __init__(self, username, restart=False):
        self.vsi_img_dir = "../../Input Images/"  # where vsi image files are moved to
        self.archive_dir = "../data/images/"  # where we will create and store the .npy archive files
        fname_dir = "../data/filenames/"
        self.archives = []  # where we will store list of full filepaths for each archive in our archive_dir
        self.thumbnails = []  # where smaller thumbnail image filepaths will be stored
        username_prefix = "{}_img_".format(username)

        if restart:
            """
            Loop through all images in img_dir, create enumerated archives for them in archive_dir,
                and add each enumerated archive filepath to our archives list.
            """
            # Delete all files in the archive directory with the relevant username if restarting

            clear_dir(self.archive_dir,
                      lambda f:
                          f.split(os.sep)[-1].startswith(username_prefix) and
                          f.split(os.sep)[-1][len(username_prefix):-4].isnumeric()
            )
            openslide_image_types = {".svs", ".tif", ".vms", ".vmu", ".ndpi", ".scn",
                                ".mrxs", ".tiff", ".svslide"}
            root = Tk()
            root.title("")
            selection_filetypes = [
                ('Microscopy Images (svs, vsi, czi, png, etc...)',
                 '*.svs|*.tif|*.tiff|*.vms|*.vmu|*.ndpi|*.scn|*.mrxs|*.tiff|*.svslide|*.vsi|*.czi|*.png|*.jpg|'
                 '*.jpeg|*.gif'),
            ]

            img_names = list(tkfilebrowser.askopenfilenames(
                parent=root,
                title='Select Images to Scan',
                filetypes=selection_filetypes,
                initialdir=os.path.join(str(Path.home()), 'Pictures')
            ))
            root.destroy()

            # Name of every image after large images have been split into two
            # or three constituent images
            img_names_all = []
            vsi_images = []
            vsi_png_images = []
            for i, name in enumerate(img_names):
                if name.endswith(".vsi"):
                    vsi_images.append((name, path.join(self.vsi_img_dir, os.path.basename(name))))
                    img_names[i] = path.join(self.vsi_img_dir, os.path.basename(name)[:-3] + 'png')
                    vsi_png_images.append(img_names[i])
            for original_path, new_path in vsi_images:  # Move vsi files to the vsi image directory
                os.rename(original_path, new_path)
            if len(vsi_images) > 1:
                convert_vsi(".png")
                for original_path, current_path in vsi_images:  # Move vsi files back to their original directories
                    os.rename(current_path, original_path)
                # img_names = [name for name in fnames(self.vsi_img_dir, recursive=False)]

            # Define a callback to be passed to the Asynchronous Progress Bar

            def archive_callback(index):
                i = index
                src_fpath = img_names[i]
                fname = os.path.basename(src_fpath)
                sys.stdout.write("\rArchiving Image {}/{}...".format(
                    i + 1,
                    len(img_names))
                )
                # Read src, Check max shape, Create archive at dst, add dst to archive list
                dst_fpath = os.path.join(self.archive_dir, "{}{}.npy".format(username_prefix, len(self.archives)))
                thumb_fpath = os.path.join(self.archive_dir, "{}{}_thumbnail.npy".format(username_prefix, len(self.archives)))
                _, src_suffix = os.path.splitext(src_fpath)
                if src_suffix in openslide_image_types:
                    slides = read_openslide_img(src_fpath)
                    if len(slides) == 2:
                        dst_fpath_a = dst_fpath
                        thumb_fpath_a = thumb_fpath
                        self.archives.append(dst_fpath_a)
                        self.thumbnails.append(thumb_fpath_a)
                        img_names_all.append("{} (1)".format(fname))
                        dst_fpath_b = os.path.join(self.archive_dir, "{}{}.npy".format(username_prefix,
                                                                                           len(self.archives)))
                        thumb_fpath_b = os.path.join(self.archive_dir, "{}{}_thumbnail.npy".format(username_prefix,
                                                                                           len(self.archives)))
                        self.archives.append(dst_fpath_b)
                        self.thumbnails.append(thumb_fpath_b)
                        img_names_all.append("{} (2)".format(fname))
                        slide_npy_a = np.array(slides[0])
                        slide_npy_b = np.array(slides[1])
                        thumbnail_a = cv2.resize(slide_npy_a, (0, 0),
                                              fx=280 / slide_npy_a.shape[1],
                                              fy=280 / slide_npy_a.shape[0])
                        thumbnail_b = cv2.resize(slide_npy_b, (0, 0),
                                              fx=280 / slide_npy_b.shape[1],
                                              fy=280 / slide_npy_b.shape[0])
                        #THUMBNAIL img = cv2.resize(img, dsize=(newsize_y, newsize_x),interpolation=cv2.INTER_CUBIC)
                        np.save(dst_fpath_a, slide_npy_a)
                        np.save(dst_fpath_b, slide_npy_b)
                        np.save(thumb_fpath_a, thumbnail_a)
                        np.save(thumb_fpath_b, thumbnail_b)
                    else:
                        slide_npy = np.array(slides[0])
                        thumbnail = cv2.resize(slide_npy, (0, 0),
                                              fx=280 / slide_npy.shape[1],
                                              fy=280 / slide_npy.shape[0])
                        np.save(dst_fpath, slide_npy)
                        np.save(thumb_fpath, thumbnail)
                        self.archives.append(dst_fpath)
                        self.thumbnails.append(thumb_fpath)
                        img_names_all.append(fname)
                elif src_suffix == '.vsi':
                    # These should be converted to png before the code gets here
                    return
                elif src_suffix == '.czi':
                    image = czf.imread(src_fpath)
                    count = image.shape[0] * image.shape[1] * image.shape[2]
                    for i in range(image.shape[0]):
                        for j in range(image.shape[1]):
                            for k in range(image.shape[2]):
                                # resize_image = cv2.resize(image[i, j, k], dsize=(newsize_y, newsize_x),
                                #                           interpolation=cv2.INTER_CUBIC)
                                img_npy = np.array(image[i, j, k])
                                dst_fpath = os.path.join(self.archive_dir, "{}{}.npy".format(username_prefix, len(self.archives)))
                                thumb_fpath = os.path.join(self.archive_dir, "{}{}_thumbnail.npy".format(username_prefix, len(self.archives)))
                                thumbnail = cv2.resize(img_npy, (0, 0),
                                                      fx=280 / img_npy.shape[1],
                                                      fy=280 / img_npy.shape[0])
                                np.save(dst_fpath, img_npy)
                                np.save(thumb_fpath, thumbnail)
                                self.archives.append(dst_fpath)
                                self.thumbnails.append(thumb_fpath)
                                if count > 1:
                                    img_names_all.append("{} ({})".format(
                                        fname, i * image.shape[1] * image.shape[2] + j * image.shape[2] + k + 1)
                                    )
                                else:
                                    img_names_all.append(fname)
                    pass
                else:  # Primarily png and other images readable by numpy
                    img_npy = cv2.imread(src_fpath)
                    thumbnail = cv2.resize(img_npy, (0, 0),
                                          fx=280 / img_npy.shape[1],
                                          fy=280 / img_npy.shape[0])
                    np.save(dst_fpath, img_npy)
                    np.save(thumb_fpath, thumbnail)
                    self.archives.append(dst_fpath)
                    self.thumbnails.append(thumb_fpath)
                    img_names_all.append(fname)

            # The root process completes the callback's task while keeping track of progress
            print(len(img_names))
            root = ProgressRoot(
                len(img_names),
                "Archiving Images",
                archive_callback
            )
            root.mainloop()
            sys.stdout.flush()
            print("")

            # delete excess pngs from vsi conversion
            for image_file in vsi_png_images:
                os.remove(image_file)

            # This collects image resolutions for necessary resizing. This became necessary when
            # additional image resolutions were being used.

            root = Tk()
            root.title("Input Image Resolutions")
            root.withdraw()

            # save img names to use in stat output
            self.fnames = img_names_all
            with open(os.path.join(fname_dir, '{}_fnames.json'.format(username)), 'w') as f:
                json.dump(self.fnames, f)

            archives_with_pathnames = zip(self.thumbnails, img_names_all)

            ir = ImageResolutions(root, archives_with_pathnames)
            ir.resizable(False, False)
            img_resolutions = ir.show()
            root.destroy()

            def resize_callback(index):
                i = index
                dst_fpath = self.archives[i]
                img = np.load(dst_fpath)
                newsize_x = int(img.shape[0] / (0.41 / img_resolutions[i][0]))
                newsize_y = int(img.shape[1] / (0.41 / img_resolutions[i][1]))
                img = cv2.resize(img, dsize=(newsize_y, newsize_x),
                           interpolation=cv2.INTER_CUBIC)
                np.save(dst_fpath, img)


            root = ProgressRoot(
                len(self.archives),
                "Resizing Images",
                resize_callback
            )
            root.mainloop()
            sys.stdout.flush()
            print("")

        else:
            with open(os.path.join(fname_dir, '{}_fnames.json'.format(username)), 'r') as f:
                self.fnames = json.load(f)
            # use existing archive files
            for fname in fnames(self.archive_dir):
                fn = fname.split(os.sep)[-1]
                if fn.startswith(username + '_img_') and fn[len(username_prefix):-4].isnumeric():
                    self.archives.append(os.path.join(self.archive_dir, fname))

        # Regardless of this we sort the result, since it depends on the nondeterministic ordering of the os.walk
        # generator in fnames()
        # We have to get the filename integer number, since otherwise we will end up with stuff like 0, 10, 11,
        # 1 instead of 0, 1, 10, 11
        self.archives = sorted(self.archives, key=lambda x: int(x.split(os.sep)[-1][len(username_prefix):-4]))

    def __iter__(self):
        for archive in self.archives:
            img = np.load(archive)
            yield img

    def __getitem__(self, i):
        return np.load(self.archives[i])

    def __setitem__(self, i, img):
        np.save(self.archives[i], img)

    def __len__(self):
        return len(self.archives)

    def max_shape(self):
        max_shape = [0, 0, 0]  # maximum dimensions of all images

        # load with mmap mode so we can just get the shape
        for archive in self.archives:
            img = np.load(archive, mmap_mode='r')
            for i, dim in enumerate(img.shape):
                if dim > max_shape[i]:
                    max_shape[i] = dim
        return max_shape
