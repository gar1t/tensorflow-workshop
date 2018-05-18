"""Pump images from cameras to image-proxy server.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import logging
import os
import signal
import subprocess
import sys
import tempfile
import threading
import time

import app_util

log = logging.getLogger("pump")

DEFAULT_HOST = "localhost"
DEFAULT_IMAGE_DIR = "/tmp/pump-images"

class ImageProxyError(Exception):
    pass

class ImageProxy(object):

    def __init__(self, config, host=None, image_path=None):
        proxy_config = config.get("servers", {}).get("image-proxy", {})
        self._host = host or proxy_config.get("host", DEFAULT_HOST)
        self._path = (
            image_path or proxy_config.get("image-dir", DEFAULT_IMAGE_DIR)
        )
        connect_timeout = proxy_config.get("connect-timeout", 10)
        self._rsync_cmd_base = [
            "rsync", "-e",
            ("ssh -o ConnectTimeout=%s -o StrictHostKeyChecking=no"
             % connect_timeout),
        ]
        log.info("writing images to %s:%s", self._host, self._path)

    def __str__(self):
        return "image proxy %s" % self._host

    def copy(self, name, src):
        _, ext = os.path.splitext(src)
        dest = "{}:{}/{}{}".format(self._host, self._path, name, ext)
        cmd = self._rsync_cmd_base + [src, dest]
        p = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        if p.returncode != 0:
            raise ImageProxyError(self._host, (p.returncode, out, err))

class CameraPump(threading.Thread):

    def __init__(self, camera, proxy, interval):
        super(CameraPump, self).__init__()
        self.camera = camera
        self.proxy = proxy
        self.interval = interval
        self._stop_event = threading.Event()

    def run(self):
        while True:
            start = time.time()
            self._snapshot_and_copy()
            to_wait = max(0, self.interval - (time.time() - start))
            if self._stop_event.wait(to_wait):
                break

    def _snapshot_and_copy(self):
        with tempfile.NamedTemporaryFile(
                prefix="pump-snashot-",
                suffix=".jpg") as tmp:
            log.info("snapshot from %s", self.camera)
            try:
                self.camera.snapshot(tmp.name)
            except Exception as e:
                self._handle_camera_error(e)
            else:
                try:
                    self.proxy.copy(self.camera.key, tmp.name)
                except Exception as e:
                    self._handle_proxy_error(e)

    def _handle_camera_error(self, e):
        if self._stop_event.is_set():
            return
        if log.getEffectiveLevel() <= logging.DEBUG:
            log.exception("from %s", self.camera)
        if isinstance(e, app_util.CameraError):
            _code, _out, msg = e.args[2]
        else:
            msg = str(e)
        log.error("snapshotting %s: %s", self.camera, msg)

    def _handle_proxy_error(self, e):
        if self._stop_event.is_set():
            return
        if log.getEffectiveLevel() <= logging.DEBUG:
            log.exception("from %s", self.proxy)
        if isinstance(e, ImageProxyError):
            _code, _out, msg = e.args[1]
        else:
            msg = str(e)
        log.error("copying image to %s: %s", self.proxy, msg)

    def stop(self):
        self._stop_event.set()

def main():
    args = _init_args()
    app_util.init_logging(args.debug)
    config = app_util.load_config(args.config)
    if args.test:
        print("Testing %s" % args.test)
        _test_image(args.test, config)
    else:
        print("Running image pump (press Ctrl-C to stop)")
        pumps = _start_pumps(
            config,
            args.interval,
            args.host,
            args.image_path)
        _init_signal_handlers(pumps)
        signal.pause()

def _test_image(key, config):
    if config.get("cameras", {}).get(key) is None:
        print("No such camera: %s" % key)
        sys.exit(1)
    cam = app_util.init_camera(key, config)
    snapshot_path = os.path.join(tempfile.gettempdir(), key + ".jpg")
    print("Snapshotting %s to %s" % (key, snapshot_path))
    cam.snapshot(snapshot_path)

def _start_pumps(config, interval, host, image_path):
    pumps = []
    proxy = ImageProxy(config, host, image_path)
    for key in config.get("cameras", {}):
        camera = app_util.init_camera(key, config)
        log.debug("camera %s config: %s", key, camera.config)
        pump = CameraPump(camera, proxy, interval)
        pump.start()
        pumps.append(pump)
    return pumps

def _init_signal_handlers(pumps):
    stop = lambda *_args: _stop(pumps)
    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

def _stop(cameras):
    print("\b\bStopping")
    for c in cameras:
        c.stop()

def _init_args():
    p = argparse.ArgumentParser()
    p.add_argument(
        "--config",
        default="config.json",
        help="App config (config.json)")
    p.add_argument(
        "--host",
        help="Override host in config")
    p.add_argument(
        "--image-path",
        help="Override image-path in config")
    p.add_argument(
        "--interval",
        default=5.0,
        type=float,
        help="Seconds between snapshots (5)")
    p.add_argument(
        "--test",
        help="Test a camera and exit")
    p.add_argument(
        "--debug",
        action="store_true",
        help="Print debug info")
    return p.parse_args()

if __name__ == "__main__":
    main()
