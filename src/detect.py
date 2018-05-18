"""Generate predictions from a set of images.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import os
import threading

import numpy as np
import PIL
import six

import tensorflow as tf

from object_detection.utils import label_map_util
from object_detection.utils import ops as utils_ops
from object_detection.utils import visualization_utils as vis_util

# Mask support is currently not working and this flag is used to
# disable it.
#
MASK_SUPPORT = False

class Detector(object):

    detect_ops = (
        "num_detections",
        "detection_boxes",
        "detection_scores",
        "detection_classes",
    )

    def __init__(self, graph_path, labels_path, box_line_size=3):
        self._sess = tf.Session()
        self._load_graph_def(graph_path)
        self._init_tensors()
        self._category_index = self._init_category_index(labels_path)
        self._box_line_size = box_line_size
        self._lock = threading.Lock()

    def _init_tensors(self):
        self._detect_tensors = {
            name: self._graph_tensor(name + ":0")
            for name in self.detect_ops
        }
        self._image_width_tensor = tf.placeholder(tf.int32)
        self._image_height_tensor = tf.placeholder(tf.int32)
        self._image_tensor = self._graph_tensor("image_tensor:0")
        self._maybe_apply_detect_masks()

    def _graph_tensor(self, name):
        return self._sess.graph.get_tensor_by_name(name)

    def _maybe_apply_detect_masks(self):
        if not MASK_SUPPORT:
            return
        try:
            t = self._graph_tensor("detection_masks:0")
        except KeyError:
            return
        else:
            self._apply_detect_masks(t)

    def _apply_detect_masks(self, detect_masks_tensor):
        ts = self._detect_tensors
        masks = tf.squeeze(detect_masks_tensor, [0])
        boxes = tf.squeeze(ts["detection_boxes"], [0])
        num_detections = tf.cast(ts["num_detections"][0], tf.int32)
        masks = tf.slice(masks, [0, 0, 0], [num_detections, -1, -1])
        boxes = tf.slice(boxes, [0, 0], [num_detections, -1])
        masks_reframed = utils_ops.reframe_box_masks_to_image_masks(
            masks, boxes,
            self._image_height_tensor,
            self._image_width_tensor)
        masks_reframed = tf.cast(tf.greater(masks_reframed, 0.5), tf.uint8)
        ts["detection_masks"] = tf.expand_dims(masks_reframed, 0)

    def __enter__(self):
        self._lock.acquire()
        return self

    def __exit__(self, *_args):
        self._lock.release()

    @staticmethod
    def _load_graph_def(graph_path):
        graph_def = tf.GraphDef()
        graph_def.ParseFromString(open(graph_path, "rb").read())
        tf.import_graph_def(graph_def, name="")

    @staticmethod
    def _init_category_index(labels_path):
        label_map = label_map_util.load_labelmap(labels_path)
        categories = [
            {"id": item.id, "name": item.display_name or item.name}
            for item in label_map.item
        ]
        return label_map_util.create_category_index(categories)

    def detect(self, image_bytes):
        image = self._init_image(image_bytes)
        detect_result = self._run_detect(image)
        self._apply_detect_result(detect_result, image)
        return detect_result, image

    @staticmethod
    def _init_image(image_bytes):
        image = PIL.Image.open(six.BytesIO(image_bytes))
        width, height = image.size
        image_np = np.array(image.getdata())
        return image_np.reshape((height, width, 3)).astype(np.uint8)

    def _run_detect(self, image):
        inputs = {
            self._image_tensor: np.expand_dims(image, axis=0),
            self._image_height_tensor: image.shape[0],
            self._image_width_tensor: image.shape[1],
        }
        outputs = self._sess.run(self._detect_tensors, feed_dict=inputs)
        return self._format_result(outputs)

    @staticmethod
    def _format_result(result):
        val = lambda name: result[name][0]
        formatted = {
            "num_detections": int(val("num_detections")),
            "detection_classes": val("detection_classes").astype(np.uint8),
            "detection_boxes": val("detection_boxes"),
            "detection_scores": val("detection_scores"),
        }
        if "detection_masks" in result:
            formatted["detection_masks"] = val("detection_masks")[0]
        return formatted

    def _apply_detect_result(self, detect_result, image):
        vis_util.visualize_boxes_and_labels_on_image_array(
            image,
            detect_result["detection_boxes"],
            detect_result["detection_classes"],
            detect_result["detection_scores"],
            self._category_index,
            instance_masks=detect_result.get("detection_masks"),
            use_normalized_coordinates=True,
            line_thickness=self._box_line_size)

    def write_image(self, image, path):
        image = PIL.Image.fromarray(image)
        self._ensure_dir(os.path.dirname(path))
        image.save(path)

    @staticmethod
    def image_bytes(image, format="PNG"):
        image = PIL.Image.fromarray(image)
        out = six.BytesIO()
        image.save(out, format)
        return out.getvalue()

    @staticmethod
    def _ensure_dir(d):
        try:
            os.makedirs(d)
        except OSError as e:
            if e.errno != 17: # exists
                raise

def main():
    args = _init_args()
    detector = Detector(args.graph, args.labels)
    for image_path in _image_paths(args):
        detect_image_path = _detect_image_path_for_input(image_path, args)
        if args.skip_existing and os.path.exists(detect_image_path):
            print("%s exists, skipping" % detect_image_path)
            continue
        print("Detecting objects in {}".format(image_path))
        _detect_objects(image_path, detect_image_path, detector)

def _image_paths(args):
    src = args.images_dir
    return [os.path.join(src, name) for name in os.listdir(src)]

def _detect_image_path_for_input(input_path, args):
    name, _ = os.path.splitext(os.path.basename(input_path))
    return os.path.join(args.output_dir, name + ".png")

def _detect_objects(image_path, detect_image_path, detector):
    with open(image_path, "rb") as f:
        image_bytes = f.read()
    _result, detect_image = detector.detect(image_bytes)
    detector.write_image(detect_image, detect_image_path)

def _init_args():
    p = argparse.ArgumentParser()
    p.add_argument(
        "--images-dir",
        default="images",
        help="Directory containing images to detect (images)")
    p.add_argument(
        "--graph",
        default="frozen_inference_graph.pb",
        help="Path to frozen detection graph (frozen_inference_graph.pb)")
    p.add_argument(
        "--labels",
        default="labels.pbtxt",
        help="Path to label proto")
    p.add_argument(
        "--output-dir",
        default="detected",
        help="Directory to write detection results (detected)")
    p.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip detection if detect image already exists")
    return p.parse_args()

if __name__ == "__main__":
    main()
