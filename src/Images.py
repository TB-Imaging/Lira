import sys
import cv2
import numpy as np
import os
import openslide
from openslide_python_fix import _load_image_lessthan_2_29, _load_image_morethan_2_29

from LiraExceptions import InputEmptyError
from base import *
from ProgressBar import ProgressRoot


def read_openslide_img(img_file, upper_left):
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
            region1 = img.read_region((upper_left[0],
                                       upper_left[1]),
                                      0, (w_rec_half, h_rec)).convert('RGB')

            region2 = img.read_region((w_rec_half,
                                       0),
                                      0, ((w_rec - w_rec_half), h_rec)).convert('RGB')
            return region1, region2

        except IOError:
            region1 = img.read_region((upper_left[0],
                                       upper_left[1]),
                                      0, (w_rec, h_rec)).convert('RGB')
            return region1,
    else:
        region1 = img.read_region((upper_left[0],
                                   upper_left[1]),
                                  0, (w_rec, h_rec)).convert('RGB')
        return region1,

class Images(object):
    """
    Since this class references hard disk files at directories set
        in the class initialization,, reading and writing to any instance
        of this class will read and write the exact same images
        as other instances.
    """

    def __init__(self, restart=False):
        self.img_dir = "../../Input Images/"  # where image files are stored
        self.archive_dir = "../data/images/"  # where we will create and store the .npy archive files
        self.archives = []  # where we will store list of full filepaths for each archive in our archive_dir

        if restart:
            """
            Loop through all images in img_dir, create enumerated archives for them in archive_dir,
                and add each enumerated archive filepath to our archives list.
            """
            # Delete all files in the archive directory if restarting
            clear_dir(self.archive_dir)
            img_names = [name for name in fnames(self.img_dir)]
            openslide_image_types = {".svs", ".tif", ".vms", ".vmu", ".ndpi", ".scn",
                                ".mrxs", ".tiff", ".svslide"}
            # Define a callback to be passed to the Asynchronous Progress Bar
            def archive_callback(index):
                i = index
                fname = img_names[i]
                sys.stdout.write("\rArchiving Image {}/{}...".format(
                    i + 1,
                    len(img_names))
                )
                # Read src, Check max shape, Create archive at dst, add dst to archive list
                src_fpath = os.path.join(self.img_dir, fname)
                dst_fpath = os.path.join(self.archive_dir, "{}.npy".format(len(self.archives)))
                _, src_suffix = os.path.splitext(src_fpath)
                if src_suffix in openslide_image_types:
                    slides = read_openslide_img(src_fpath, upper_left=(0, 0))
                    if len(slides) == 2:
                        dst_fpath_a = dst_fpath
                        self.archives.append(dst_fpath_a)
                        dst_fpath_b = os.path.join(self.archive_dir, "{}.npy".format(len(self.archives)))
                        self.archives.append(dst_fpath_b)
                        slide_npy_a = np.array(slides[0])
                        slide_npy_b = np.array(slides[1])
                        np.save(dst_fpath_a, slide_npy_a)
                        np.save(dst_fpath_b, slide_npy_b)
                    else:
                        slide_npy = np.array(slides[0])
                        np.save(dst_fpath, slide_npy)
                        self.archives.append(dst_fpath)
                elif src_suffix == '.vsi':
                    # These should be converted to png before the code gets here
                    return
                else:
                    np.save(dst_fpath, cv2.imread(src_fpath))
                    self.archives.append(dst_fpath)

            # The root process completes the callback's task while keeping track of progress
            print(len(img_names))
            root = ProgressRoot(
                # root,
                len(img_names),
                "Archiving Image",
                archive_callback
            )
            root.mainloop()
            sys.stdout.flush()
            print("")
        else:
            # use existing archive files
            for fname in fnames(self.archive_dir):
                self.archives.append(os.path.join(self.archive_dir, fname))

        # Initialize to the original list of images ordered in the input images folder
        self.fnames = [fname for fname in fnames(self.img_dir)]
        if len(self.fnames) == 0:
            raise InputEmptyError('Input directory is empty.')

        # Regardless of this we sort the result, since it depends on the nondeterministic ordering of the os.walk
        # generator in fnames()
        # We have to get the filename integer number, since otherwise we will end up with stuff like 0, 10, 11,
        # 1 instead of 0, 1, 10, 11
        self.archives = sorted(self.archives, key=lambda x: int(x.split(os.sep)[-1][:-4]))

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
