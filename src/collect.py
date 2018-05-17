"""Run an image collection app to save images from one or more cameras.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import json
import logging
import os
import shutil
import sys
import tempfile
import time

import flask

import app_util

log = logging.getLogger("collect")

HOME = os.path.abspath(os.path.dirname(__file__))

app = flask.Flask(
    __name__,
    static_url_path="",
    static_folder="",
    root_path=os.path.join(HOME, "collect/dist"))

latest_images = {}

@app.route("/")
def index():
    return app.send_static_file("index.html")

@app.route("/cameras")
def cameras():
    cameras = sorted([cam.key for cam in flask.current_app.cameras])
    return flask.Response(
        json.dumps(cameras),
        headers=[("Access-Control-Allow-Origin", "*")])

@app.route("/cameras/<key>/img.jpg")
def image(key):
    camera = _camera(key)
    latest_images[key] = img_bytes = _snapshot(camera)
    return flask.Response(img_bytes, mimetype="image/jpeg")

def _snapshot(camera):
    with tempfile.NamedTemporaryFile(
                prefix="collect-snashot-",
                suffix=".jpg") as tmp:
        try:
            camera.snapshot(tmp.name)
        except Exception:
            log.exception("snapshot from %s", camera.key)
            flask.abort(500)
        else:
            return open(tmp.name, "rb").read()

@app.route("/cameras/<key>/save", methods=["POST"])
def save_image(key):
    try:
        img_bytes = latest_images[key]
    except KeyError:
        flask.abort(404)
    else:
        _save_image(key, img_bytes)
        return flask.Response(
            "",
            status=201,
            headers=[("Access-Control-Allow-Origin", "*")])

def _save_image(key, img_bytes):
    path, path_dir = _image_path(key)
    app_util.ensure_dir(path_dir)
    with open(path, "wb") as f:
        f.write(img_bytes)

def _image_path(key):
    path_dir = flask.current_app.save_dir
    timestamp = int(time.time() * 1000)
    path = os.path.join(path_dir, "{}-{}.jpg".format(key, timestamp))
    return path, path_dir

def _camera(key):
    for cam in flask.current_app.cameras:
        if cam.enabled and cam.key == key:
            return cam
    flask.abort(404)

def main():
    args = _parse_args()
    if args.from_dir:
        _copy_images_and_exit(args.from_dir, args.save_dir)
    _init_app(args)
    if args.dev:
        app_port = args.port + 1
        _start_dev_server(args, app_port)
    else:
        app_port = args.port
    app.run(host=args.host, port=app_port)

def _copy_images_and_exit(src, dest):
    app_util.ensure_dir(dest)
    for name in os.listdir(src):
        print("Copying {}".format(name))
        src_path = os.path.join(src, name)
        shutil.copy(src_path, dest)
    sys.exit(0)

def _init_app(args):
    try:
        config = json.load(open(args.config))
    except Exception as e:
        sys.stderr.write(
            "Error reading {}: {}\n".format(args.config, e))
        sys.exit(1)
    else:
        app.cameras = [
            _init_camera(key, config, args)
            for key in config.get("cameras", {})
        ]
        app.save_dir = args.save_dir

def _init_camera(key, config, args):
    if args.use_image_proxy:
        camera = _init_camera_proxy(key, config)
    else:
        camera = _init_default_camera(key, config)
    print(
        " * Camera %s configured to read from %s"
        % (key, camera.src))
    return camera

def _init_camera_proxy(key, config):
    cam_config = config.get("cameras", {}).get(key, {})
    proxy_config = config.get("servers", {}).get("image-proxy", {})
    return app_util.CameraProxy(key, cam_config, proxy_config)

def _init_default_camera(key, config):
    cam_config = config.get("cameras", {}).get(key, {})
    return app_util.Camera3(key, cam_config)

def _start_dev_server(args, app_port):
    app_home = os.path.join(HOME, "collect")
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
        "--use-image-proxy",
        action="store_true",
        help="Use image-proxy to obtain images")
    p.add_argument(
        "--host",
        default="0.0.0.0",
        help="App host (0.0.0.0)")
    p.add_argument(
        "--port",
        default=8002,
        type=int,
        help="App port (8002)")
    p.add_argument(
        "--save-dir",
        default="images",
        help="Directory to save images (images)")
    p.add_argument(
        "--dev",
        action="store_true",
        help="Run in dev mode")
    p.add_argument(
        "--from-dir",
        help="Copy images in FROM_DIR to SAVE_DIR and exit")
    return p.parse_args()

if __name__ == "__main__":
    main()
