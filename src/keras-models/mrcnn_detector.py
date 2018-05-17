# pylint: disable=import-error

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import csv
import os
import sys

import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt

import skimage.io

import mrcnn.model as modellib
from mrcnn import visualize

sys.path.insert(0, "samples")

from coco import coco

CLASS_NAMES = [
    'BG', 'person', 'bicycle', 'car', 'motorcycle', 'airplane',
    'bus', 'train', 'truck', 'boat', 'traffic light',
    'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird',
    'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear',
    'zebra', 'giraffe', 'backpack', 'umbrella', 'handbag', 'tie',
    'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball',
    'kite', 'baseball bat', 'baseball glove', 'skateboard',
    'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup',
    'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple',
    'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza',
    'donut', 'cake', 'chair', 'couch', 'potted plant', 'bed',
    'dining table', 'toilet', 'tv', 'laptop', 'mouse', 'remote',
    'keyboard', 'cell phone', 'microwave', 'oven', 'toaster',
    'sink', 'refrigerator', 'book', 'clock', 'vase', 'scissors',
    'teddy bear', 'hair drier', 'toothbrush']

def init():
    pass

def init_model(model_path):
    class InferenceConfig(coco.CocoConfig):
        GPU_COUNT = 1
        IMAGES_PER_GPU = 1
    config = InferenceConfig()
    model = modellib.MaskRCNN(
        mode="inference",
        model_dir="",
        config=config)
    model.load_weights(model_path, by_name=True)
    return model

def detect(input_path, model, object_class):
    image = skimage.io.imread(input_path)
    result = model.detect([image], verbose=1)[0]
    _write_result_csv(result, _result_csv_path(input_path))
    _write_detected_image(result, image, _detected_image_path(input_path))
    return _count_objects(result, object_class)

def _result_csv_path(input_path):
    output_base, _ = os.path.splitext(input_path)
    return output_base + "-result.csv"

def _write_result_csv(result, path):
    with open(path, "w") as f:
        out = csv.writer(f)
        out.writerow(["Class", "Score", "Region"])
        for class_id, score, roi in zip(
                result["class_ids"], result["scores"], result["rois"]):
            out.writerow([
                CLASS_NAMES[class_id],
                score,
                ",".join([str(i) for i in roi.tolist()])
            ])

def _detected_image_path(input_path):
    output_base, _ = os.path.splitext(input_path)
    return output_base + "-detected.png"

def _write_detected_image(result, image, path):
    plt.show = _write_image_fn(path)
    visualize.display_instances(
        image,
        result['rois'],
        result['masks'],
        result['class_ids'],
        CLASS_NAMES,
        result['scores'])

def _write_image_fn(path):
    return lambda: plt.savefig(
        path,
        bbox_inches="tight",
        pad_inches=0,
        transparent=True)

def _count_objects(result, object_class):
    return sum([
        CLASS_NAMES[class_id] == object_class
        for class_id in result["class_ids"]
    ])
