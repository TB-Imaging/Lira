import sys, time
import cv2, h5py
import numpy as np
from keras.models import load_model

from base import *
from gui_base import get_outline_rectangle_coordinates
from EditingDataset import EditingDataset
from TypeOneDetectionEditor import TypeOneDetectionEditor
from ProgressBar import ProgressRoot

from keras_retinanet.utils.image import read_image_bgr, preprocess_image, resize_image
from keras_retinanet import models

class TypeOneDetections(object):
    def __init__(self, dataset, uid, restart=False):
        self.dataset = dataset  # for reference, do not modify
        self.imgs = self.dataset.imgs
        self.uid = uid
        self.restart = restart

        # Our two attributes for detections before and after editing.
        self.archive_dir_before_editing = "../data/type_one_detections_before_editing/"  # Where we'll store the .npy
        # files for our detections before editing
        self.archive_dir_after_editing = "../data/type_one_detections_after_editing/"  # Where we'll store the .npy
        # files for our detections after editing
        self.before_editing = EditingDataset(self.dataset, self.uid, self.archive_dir_before_editing,
                                             restart=self.restart)
        self.after_editing = EditingDataset(self.dataset, self.uid, self.archive_dir_after_editing,
                                            restart=self.restart)

        self.model = None

        # Detection parameters and classifier
        self.detection = True
        if self.dataset.progress["model"] == "balbc":
            self.detection = False

        # Size of each side of the cross
        self.side_size = 2000

        # Stride to move the cross each iteration
        self.cross_stride = 500

        # Size of each lengthwise segment
        self.segment_size = 200

        # Stride of our segment blocks for each check
        self.segment_stride = 100

        # Scalar to weight our standard deviations by before applying operations to them.
        self.stdw = 0.5

        # Threshold to ensure we don't scan segments across empty slide
        self.empty_slide_threshold = 210

        # Threshold for how high the mean of a detection is allowed to be
        self.intensity_threshold = 140

        # Kernel for our Gaussian Blur
        self.gaussian_kernel = (7, 7)
        self.rect_h = 64  # Height of each rectangle when displayed
        self.rect_w = 64  # Width of each rectangle when displayed

    def generate(self):
        # Generates detections for each image, saving each detection array to self.before_editing.

        # Quick lambda for use later
        dist = lambda a, b: abs(a - b)

        if self.detection:
            self.model = models.load_model('../classifiers/type_one_detection_classifier_resnet50.h5',
                                           backbone_name='resnet50')
            self.model = models.convert_model(self.model)


        # Generate for each image
        def generate_callback(index):  # img_i, img in enumerate(self.imgs):
            img_i = index
            img = self.imgs[img_i]
            # Progress indicator
            sys.stdout.write("\rGenerating Type One Detections on Image {}/{}...".format(img_i, len(self.imgs) - 1))

            # final detections for img, will be archived after detection and suppression
            detections = []

            if self.detection:
                imscan = cv2.resize(img, (0, 0), fx=0.025, fy=0.025)
                imscan = cv2.cvtColor(imscan, cv2.COLOR_RGB2BGR)
                imscan = preprocess_image(imscan.copy())
                imscan, scale = resize_image(imscan)

                boxes, scores, labels = self.model.predict(np.expand_dims(imscan, axis=0))
                boxes /= scale
                boxes /= 0.025
                for box, score, label in zip(boxes[0], scores[0], labels[0]):
                    if score < 0.4: continue
                    box = get_outline_rectangle_coordinates(box[0], box[1], box[2], box[3], self.rect_h, self.rect_w)
                    detections.append(box)

            # Save these detections to both the before and after editing datasets, since we initialize them to be the
            # same.
            self.before_editing[img_i] = detections
            self.after_editing[img_i] = detections

        # img_i, img in enumerate(self.imgs):
        root = ProgressRoot(
            len(self.imgs),
            "Generating Type Ones",
            generate_callback
        )
        root.mainloop()

        # Now that we've finished generating, we've started editing, so we update user progress.
        self.dataset.progress["type_ones_started_editing"] = True
        if self.dataset.progress["model"] == "balbc":
            self.dataset.progress["type_ones_finished_editing"] = True

        sys.stdout.flush()
        print("")

    def edit(self):
        # Displays detections on all images and allows the user to edit them until they are finished. The editor
        # handles the saving of edits.
        editor = TypeOneDetectionEditor(self.dataset)
        # editor.start_editing()
