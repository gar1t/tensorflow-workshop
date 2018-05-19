"""Detect objects in camera images.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import base64
import json
import logging
import os
import shutil
import signal
import subprocess
import sys
import threading
import time

import flask

from guild import op_util

import app_util
import detect

log = logging.getLogger("scan")

HOME = os.path.abspath(os.path.dirname(__file__))

class PerformanceStats(object):

    def __init__(self, root_key="performance"):
        self.root_key = root_key
        self._start = None
        self._stats = {}

    def start(self, category, key):
        self._start = category, key, time.time()
        return self

    def __enter__(self):
        pass

    def __exit__(self, *_args):
        self.stop()

    def stop(self):
        assert self._start is not None
        category, key, start = self._start
        stop = time.time()
        self._stats.setdefault(category, {})[key] = stop - start

    def scalars(self):
        scalars = []
        for cat in self._stats:
            cat_total = 0
            cat_n = 0
            for key, val in self._stats[cat].items():
                scalars.append((self._scalar_key(cat, key), val))
                cat_total += val
                cat_n += 1
            scalars.append((self._scalar_key(cat, "all"), cat_total / cat_n))
        return scalars

    def _scalar_key(self, cat, key):
        return "{}/{}/{}".format(self.root_key, cat, key)

class StatsLog(object):

    def __init__(self, log_dir):
        self._log = op_util.TFEvents(log_dir)
        self._lock = threading.Lock()

    def scalars(self, scalars):
        with self._lock:
            self.log.scalars(scalars)

class Worker(threading.Thread):

    def __init__(self, camera, detector, log, working_dir, interval,
                 archive_steps=0):
        super(Worker, self).__init__()
        self.key = camera.key
        self.camera = camera
        self.detector = detector
        self.log = log
        self.working_dir = working_dir
        self.interval = interval
        self.archive_steps = archive_steps
        self._stats = PerformanceStats()
        self._stop_event = threading.Event()
        self._image_path = os.path.join(
            working_dir, "%s.jpg" % camera.key)
        self._detect_image_path = os.path.join(
            working_dir, "%s-detect.png" % camera.key)
        self._detect_image_lock = threading.Lock()
        self._step = 0

    def run(self):
        while True:
            start = time.time()
            self._snapshot_and_detect()
            self._step += 1
            to_wait = max(0, self.interval - (time.time() - start))
            if self._stop_event.wait(to_wait):
                break

    def _snapshot_and_detect(self):
        log.info("detecting from %s", self.camera)
        try:
            self._snapshot()
        except Exception as e:
            self._handle_camera_error(e)
        else:
            try:
                self._detect()
            except Exception as e:
                self._handle_detect_error(e)

    def _snapshot(self):
        self.camera.snapshot(self._image_path)
        self._maybe_archive(self._image_path, "-orig")

    def _maybe_archive(self, path, suffix):
        if self.archive_steps > 0 and (self._step % self.archive_steps) == 0:
            self._archive(path, suffix)

    def _archive(self, path, suffix):
        path_dir = os.path.dirname(path)
        _, ext = os.path.splitext(path)
        dest_name = (
            "archive-{}-{:06d}{}{}".format(
            self.key, self._step, suffix, ext))
        dest = os.path.join(path_dir, dest_name)
        shutil.copy(path, dest)

    def _handle_camera_error(self, e):
        if self._stop_event.is_set():
            return
        if log.getEffectiveLevel() <= logging.DEBUG:
            log.exception("from %s", self.camera)
        if isinstance(e, app_util.CameraError):
            _code, _out, msg = e.args[2]
        else:
            msg = str(e)
        log.error("camera %s: %s", self.camera, msg)

    def _detect(self):
        with open(self._image_path, "rb") as f:
            image_bytes = f.read()
        _result, detect_image = self.detector.detect(image_bytes)
        with self._detect_image_lock:
            self.detector.write_image(detect_image, self._detect_image_path)
        self._maybe_archive(self._detect_image_path, "-detected")

    def read_detect_image(self):
        with self._detect_image_lock:
            return open(self._detect_image_path, "rb").read()

    def _handle_detect_error(self, e):
        if self._stop_event.is_set():
            return
        if log.getEffectiveLevel() <= logging.DEBUG:
            log.exception("detect")
        log.error("detector: %s", e)

    def stop(self):
        self._stop_event.set()

app = flask.Flask(
    __name__,
    static_url_path="",
    static_folder="",
    root_path=os.path.join(HOME, "scan/dist"))

@app.route("/")
def index():
    return app.send_static_file("index.html")

@app.route("/cameras")
def cameras():
    cameras = sorted([cam.key for cam in flask.current_app.cameras])
    return flask.Response(
        json.dumps(cameras),
        mimetype="application/json",
        headers=[("Access-Control-Allow-Origin", "*")])

@app.route("/detected/<key>.png")
def detected(key):
    worker = _find_worker(key)
    try:
        image_bytes = worker.read_detect_image()
    except IOError as e:
        if e.errno != 2:
            raise
        flask.abort(404)
    else:
        return flask.Response(image_bytes, mimetype="image/png")

def _find_worker(key):
    for worker in flask.current_app.workers:
        if worker.key == key:
            return worker
    flask.abort(404)

def main():
    args = _parse_args()
    _init_logging(args)
    cameras = _init_cameras(args)
    detector = _init_detector(args)
    log = _init_log(args)
    workers = _start_workers(cameras, detector, log, args)
    _init_signal_handlers(workers)
    _start_app(cameras, workers, args)

def _init_logging(args):
    app_util.init_logging(args.debug)

def _init_cameras(args):
    config = app_util.load_config(args.config)
    return [
        _init_camera(key, config, args)
        for key in config.get("cameras", {})
    ]

def _init_camera(key, config, args):
    camera = app_util.init_camera(key, config, args.use_image_proxy)
    log.debug("camera %s config: %s", key, camera.config)
    print(
        " * Camera %s configured to read from %s"
        % (key, camera.src))
    return camera

def _init_detector(args):
    d = detect.Detector(
        args.graph,
        args.labels,
        args.box_line_size)
    d.step = 0
    return d

def _init_log(args):
    app_util.ensure_dir(args.log_dir)
    return StatsLog(args.log_dir)

def _start_workers(cameras, detector, log, args):
    workers = []
    app_util.ensure_dir(args.image_dir)
    for camera in cameras:
        worker = Worker(
            camera,
            detector,
            log,
            args.image_dir,
            args.interval,
            args.archive_steps)
        worker.start()
        workers.append(worker)
    return workers

def _init_signal_handlers(workers):
    stop = lambda *_args: _stop(workers)
    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

def _stop(workers):
    print("\b\bStopping")
    for w in workers:
        w.stop()
    for w in workers:
        w.join()
    sys.exit(0)

def _start_app(cameras, workers, args):
    app.cameras = cameras
    app.workers = workers
    app.image_dir = os.path.abspath(args.image_dir)
    if args.dev:
        app_port = args.port + 1
        _start_dev_server(args, app_port)
    else:
        app_port = args.port
    app.run(host=args.host, port=app_port)

def _start_dev_server(args, app_port):
    app_home = os.path.join(HOME, "scan")
    server = app_util.DevServer(args.host, args.port, app_port, app_home)
    server.start()
    time.sleep(1)

def _parse_args():
    p = argparse.ArgumentParser()
    p.add_argument(
        "--config", metavar="PATH",
        default="config.json",
        help="App config (config.json)")
    p.add_argument(
        "--use-image-proxy",
        action="store_true",
        help="Use image-proxy to obtain images")
    p.add_argument(
        "--archive-steps", metavar="N",
        default=0,
        type=int,
        help="Archive at every Nth scan step; 0 disables archives (0)")
    p.add_argument(
        "--graph", metavar="PATH",
        default="frozen_inference_graph.pb",
        help="Path to frozen detection graph (frozen_inference_graph.pb)")
    p.add_argument(
        "--labels", metavar="PATH",
        default="labels.pbtxt",
        help="Path to label proto")
    p.add_argument(
        "--host",
        default="0.0.0.0",
        help="App host (0.0.0.0)")
    p.add_argument(
        "--port",
        default=8004,
        type=int,
        help="App port (8004)")
    p.add_argument(
        "--image-dir", metavar="PATH",
        default="images",
        help="Directory to write images in (images)")
    p.add_argument(
        "--log-dir", metavar="PATH",
        default="logs",
        help="Directory to write log in (logs)")
    p.add_argument(
        "--interval", metavar="SECONDS",
        default=5.0,
        type=float,
        help="Seconds between detections (5)")
    p.add_argument(
        "--box-line-size", metavar="N",
        default=4,
        type=int,
        help="Bounding box line width (4)")
    p.add_argument(
        "--debug",
        action="store_true",
        help="Print debug info")
    p.add_argument(
        "--dev",
        action="store_true",
        help="Run in dev mode")
    return p.parse_args()

if __name__ == "__main__":
    main()
