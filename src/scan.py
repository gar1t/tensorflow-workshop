"""Run an image collection app to save images from one or more cameras.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import base64
import json
import logging
import os
import subprocess
import threading
import time

import flask

from guild import op_util

import app_util
import detect

log = logging.getLogger("scan")

HOME = os.path.abspath(os.path.dirname(__file__))

class DevServer(threading.Thread):

    def __init__(self, host, port, app_port):
        super(DevServer, self).__init__()
        self.host = host
        self.port = port
        self.app_port = app_port
        self._ready = False

    def run(self):
        server_bin = os.path.join(
            HOME, "collect/node_modules/.bin/webpack-dev-server")
        config = os.path.join(HOME, "collect/build/webpack.dev.conf.js")
        args = [
            server_bin,
            "--host", self.host,
            "--config", config,
            "--progress",
        ]
        env = {
            "HOST": self.host,
            "PORT": str(self.port),
            "APP_PORT": str(self.app_port),
            "PATH": os.environ["PATH"],
        }
        p = subprocess.Popen(args, env=env)
        p.wait()

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

@app.route("/detect")
def detect_():
    app = flask.current_app
    resp = {}
    stats = PerformanceStats()
    with app.detector as detector:
        step = detector.step
        detector.step = step + 1
    for camera in app.cameras:
        if not camera.enabled:
            continue
        log.info("Getting image from %s", camera.key)
        with camera:
            with stats.start("snapshot", camera.key):
                try:
                    image_bytes = camera.snapshot()
                except IOError as e:
                    log.error(
                        "error getting image from %s: %s",
                        camera.key, e)
                    continue
        with app.detector as detector:
            log.info("Detecting objects in image from %s", camera.key)
            with stats.start("detect", camera.key):
                _detect_result, detect_image = detector.detect(image_bytes)
        detect_image_bytes = detector.image_bytes(detect_image)
        detect_image_encoded = base64.b64encode(detect_image_bytes).decode()
        resp[camera.key] = {
            "image": "data:image/png;base64," + detect_image_encoded
        }
    app.log.add_scalars(stats.scalars(), step)
    app.log.flush()
    return flask.Response(
        json.dumps(resp),
        mimetype="application/json",
        headers=[("Access-Control-Allow-Origin", "*")])

def main():
    args = _parse_args()
    _init_app(args)
    if args.dev:
        app_port = args.port + 1
        _start_dev_server(args, app_port)
    else:
        app_port = args.port
    app.run(host=args.host, port=app_port)

def _init_app(args):
    app.cameras = _init_cameras(args)
    app.detector = _init_detector(args)
    app.log = _init_log(args)

def _init_cameras(args):
    config = app_util.load_config(args.config)
    return [
        app_util.Camera(key, val)
        for key, val in config.get("cameras", {}).items()
        if not val.get("disabled", False)
    ]

def _init_detector(args):
    d = detect.Detector(
        args.graph,
        args.labels,
        args.box_line_size)
    d.step = 0
    return d

def _init_log(args):
    app_util.ensure_dir(args.log_dir)
    return op_util.TFEvents(args.log_dir)

def _start_dev_server(args, app_port):
    app_home = os.path.join(HOME, "scan")
    server = app_util.DevServer(args.host, args.port, app_port, app_home)
    server.start()
    time.sleep(1)

def _parse_args():
    p = argparse.ArgumentParser()
    p.add_argument(
        "--config",
        default="config.json",
        help="App config (config.json)")
    p.add_argument(
        "--graph",
        default="frozen_inference_graph.pb",
        help="Path to frozen detection graph (frozen_inference_graph.pb)")
    p.add_argument(
        "--labels",
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
        "--log-dir",
        default="logs",
        help="Directory to write log in (logs)")
    p.add_argument(
        "--box-line-size",
        default=4,
        type=int,
        help="Bounding box line width (4)")
    p.add_argument(
        "--dev",
        action="store_true",
        help="Run in dev mode")
    return p.parse_args()

if __name__ == "__main__":
    main()
