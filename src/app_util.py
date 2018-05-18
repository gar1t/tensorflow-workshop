"""Support for workshop apps.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import errno
import json
import logging
import os
import subprocess
import sys
import threading

class CameraError(Exception):
    pass

class CameraBase(object):

    def __init__(self, key, config):
        self.key = key
        self.config = config
        self.enabled = config.get("enabled", True)

class CameraProxy(CameraBase):
    """Camera proxy that uses rsync to obtain snapshot images."""

    DEFAULT_HOST = "localhost"
    DEFAULT_IMAGE_DIR = "/tmp/camera-images"

    def __init__(self, key, cam_config, proxy_config):
        super(CameraProxy, self).__init__(key, cam_config)
        self.src = self._init_src(key, proxy_config)

    def _init_src(self, key, proxy_config):
        host = proxy_config.get("host", self.DEFAULT_HOST)
        image_dir = proxy_config.get("image-dir", self.DEFAULT_IMAGE_DIR)
        return "{}:{}/{}.jpg".format(host, image_dir, key)

    def __str__(self):
        return self.key

    def snapshot(self, path, timeout=5):
        cmd = [
            "rsync", "-vL",
            "--timeout", str(timeout),
            "-e", "ssh -o StrictHostKeyChecking=no",
            self.src, path]
        p = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        if p.returncode != 0:
            raise CameraError(self.key, self.config, (p.returncode, out, err))
        return out, err

class Camera(CameraBase):
    """Camera that uses RTSP stream and ffmpeq to capture snapshots.

    This approach proves far more reliable than using HTTP via the
    amcrest/requests interface.

    The issue impacting snapshots via amcrest/requests is covered
    here: https://github.com/tchellomello/python-amcrest/issues/86

    """

    def __init__(self, key, config):
        super(Camera, self).__init__(key, config)
        self.src = self._init_src(config)

    def __str__(self):
        return self.key

    @staticmethod
    def _init_src(config):
        host = config.get("host", "192.168.1.8")
        user = config.get("user", "admin")
        password = config.get("password", "admin")
        return ("rtsp://{user}:{password}@{host}/"
                "cam/realmonitor?channel=1&subtype=0").format(
                    user=user,
                    password=password,
                    host=host)

    def snapshot(self, path, timeout=5):
        cmd = [
            "ffmpeg", "-y",
            "-i", self.src,
            "-timeout", str(timeout),
            "-vframes", "1", path
        ]
        p = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        if p.returncode != 0:
            raise CameraError(self.key, self.config, (p.returncode, out, err))
        return out, err

class DevServer(threading.Thread):

    def __init__(self, host, port, app_port, app_home):
        super(DevServer, self).__init__()
        self.host = host
        self.port = port
        self.app_port = app_port
        self.app_home = app_home
        self._ready = False

    def run(self):
        server_bin = os.path.join(
            self.app_home, "node_modules/.bin/webpack-dev-server")
        config = os.path.join(self.app_home, "build/webpack.dev.conf.js")
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

def ensure_dir(d):
    d = os.path.realpath(d)
    try:
        os.makedirs(d)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

def load_config(path):
    try:
        return json.load(open(path))
    except Exception as e:
        sys.stderr.write("Error reading {}: {}\n".format(path, e))
        sys.exit(1)

def init_camera(key, config, use_image_proxy=False):
    if use_image_proxy:
        camera = _init_camera_proxy(key, config)
    else:
        camera = _init_default_camera(key, config)
    return camera

def _init_camera_proxy(key, config):
    cam_config = config.get("cameras", {}).get(key, {})
    proxy_config = config.get("servers", {}).get("image-proxy", {})
    return CameraProxy(key, cam_config, proxy_config)

def _init_default_camera(key, config):
    cam_config = config.get("cameras", {}).get(key, {})
    return Camera(key, cam_config)

def init_logging(debug):
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S")
