# pylint: disable=import-error

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import csv
import os

import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt

import cv2
import keras
import numpy as np
import tensorflow as tf

from keras_retinanet.models import resnet
from keras_retinanet.utils import image as image_util
from keras_retinanet.utils import colors as colors_util
from keras_retinanet.utils import visualization as vis_util

LABELS_TO_NAMES = {
    0: 'person',
    1: 'bicycle',
    2: 'car',
    3: 'motorcycle',
    4: 'airplane',
    5: 'bus',
    6: 'train',
    7: 'truck',
    8: 'boat',
    9: 'traffic light',
    10: 'fire hydrant',
    11: 'stop sign',
    12: 'parking meter',
    13: 'bench',
    14: 'bird',
    15: 'cat',
    16: 'dog',
    17: 'horse',
    18: 'sheep',
    19: 'cow',
    20: 'elephant',
    21: 'bear',
    22: 'zebra',
    23: 'giraffe',
    24: 'backpack',
    25: 'umbrella',
    26: 'handbag',
    27: 'tie',
    28: 'suitcase',
    29: 'frisbee',
    30: 'skis',
    31: 'snowboard',
    32: 'sports ball',
    33: 'kite',
    34: 'baseball bat',
    35: 'baseball glove',
    36: 'skateboard',
    37: 'surfboard',
    38: 'tennis racket',
    39: 'bottle',
    40: 'wine glass',
    41: 'cup',
    42: 'fork',
    43: 'knife',
    44: 'spoon',
    45: 'bowl',
    46: 'banana',
    47: 'apple',
    48: 'sandwich',
    49: 'orange',
    50: 'broccoli',
    51: 'carrot',
    52: 'hot dog',
    53: 'pizza',
    54: 'donut',
    55: 'cake',
    56: 'chair',
    57: 'couch',
    58: 'potted plant',
    59: 'bed',
    60: 'dining table',
    61: 'toilet',
    62: 'tv',
    63: 'laptop',
    64: 'mouse',
    65: 'remote',
    66: 'keyboard',
    67: 'cell phone',
    68: 'microwave',
    69: 'oven',
    70: 'toaster',
    71: 'sink',
    72: 'refrigerator',
    73: 'book',
    74: 'clock',
    75: 'vase',
    76: 'scissors',
    77: 'teddy bear',
    78: 'hair drier',
    79: 'toothbrush'}

def init():
    config = tf.ConfigProto()
    config.gpu_options.allow_growth = True
    sess = tf.Session(config=config)
    # use this environment flag to change which GPU to use
    #os.environ["CUDA_VISIBLE_DEVICES"] = "1"
    keras.backend.tensorflow_backend.set_session(sess)

def init_model(model_path):
    model = keras.models.load_model(
        model_path,
        custom_objects=resnet.custom_objects)
    return model

def detect(input_path, model, object_class):
    output_base, _ = os.path.splitext(input_path)
    detected_count = 0
    image = image_util.read_image_bgr(input_path)
    draw = image.copy()
    draw = cv2.cvtColor(draw, cv2.COLOR_BGR2RGB)
    image = image_util.preprocess_image(image)
    image, scale = image_util.resize_image(image)
    _, _, boxes, nms_classification = model.predict_on_batch(
        np.expand_dims(image, axis=0))
    predicted_labels = np.argmax(nms_classification[0, :, :], axis=1)
    scores = nms_classification[
        0,
        np.arange(nms_classification.shape[1]),
        predicted_labels]
    boxes /= scale
    with open(output_base + "-result.csv", "w") as csv_f:
        csv_out = csv.writer(csv_f)
        csv_out.writerow(["Class", "Score", "Region"])
        for idx, (label, score) in enumerate(zip(predicted_labels, scores)):
            if score < 0.5:
                continue
            color = colors_util.label_color(label)
            box = boxes[0, idx, :].astype(int)
            vis_util.draw_box(draw, box, color=color)
            label_name = LABELS_TO_NAMES[label]
            caption = "{} {:.3f}".format(label_name, score)
            vis_util.draw_caption(draw, box, caption)
            csv_out.writerow([
                label_name,
                score,
                ",".join([str(i) for i in box.tolist()])
            ])
            if label_name == object_class:
                detected_count += 1
    plt.figure(figsize=(15, 15))
    plt.axis('off')
    plt.imshow(draw)
    plt.savefig(
        output_base + "-detected.png",
        bbox_inches="tight",
        pad_inches=0,
        transparent=True)
    return detected_count
