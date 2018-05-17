"""Support for workshop apps.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import errno
import json
import os
import subprocess
import sys
import tempfile
import threading
import time

import amcrest

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

class Camera3(CameraBase):
    """Camera that uses RTSP stream and ffmpeq to capture snapshots.

    This approach proves far more reliable than using HTTP via the
    amcrest/requests interface.

    The issue impacting snapshots via amcrest/requests is covered
    here: https://github.com/tchellomello/python-amcrest/issues/86

    """

    def __init__(self, key, config):
        super(Camera3, self).__init__(key, config)
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

class Camera2(object):
    """Camera that uses amcrest API and lazy connections."""

    def __init__(self, key, config):
        self.key = key
        self.config = config
        self.__camera = None

    def __str__(self):
        return "camera %s" % self.key

    def snapshot(self, path):
        self._camera.snapshot(0, path)

    @property
    def _camera(self):
        if self.__camera is None:
            host = self.config.get("host", "192.168.1.8")
            port = self.config.get("port", "80")
            user = self.config.get("user", "admin")
            pwd = self.config.get("password", "admin")
            try:
                ac = amcrest.AmcrestCamera(host, port, user, pwd)
            except Exception as e:
                raise CameraError(self.key, self.config, e)
            else:
                self.__camera = ac.camera
        return self.__camera

class Camera(object):
    """Original camera implementation, to be phased out.

    Camera3 uses a more reliable approach for snapshotting and doesn't
    rely on the amcrest/requests API. See docs in Camera3 above for
    details.

    """

    def __init__(self, key, config):
        self.key = key
        self.config = config
        self._camera = self._init_camera(config)
        self.enabled = self._camera is not None
        self._last_img = b""
        self._lock = threading.Lock()

    def __enter__(self):
        self._lock.acquire()

    def __exit__(self, *_args):
        self._lock.release()

    @staticmethod
    def _init_camera(config):
        host = config.get("host", "192.168.1.8")
        port = config.get("port", "80")
        user = config.get("user", "admin")
        password = config.get("password", "admin")
        sys.stderr.write("Connecting to camera at {}\n".format(host))
        try:
            ac = amcrest.AmcrestCamera(host, port, user, password)
        except Exception as e:
            sys.stderr.write("Error connecting to {}: {}".format(host, e))
            return None
        else:
            return ac.camera

    def snapshot(self):
        with tempfile.NamedTemporaryFile(prefix="collect-snashot-") as tmp:
            resp = self._camera.snapshot(0, tmp.name)
            if resp.status != 200:
                raise IOError(
                    "error getting snapshot from %s: %s"
                    % (self.key, resp.status))
            image_bytes = open(tmp.name, "rb").read()
        if not image_bytes:
            raise IOError("empty image")
        self._last_img = image_bytes
        return image_bytes

    def save(self, to_dir):
        ensure_dir(to_dir)
        with open(self._img_path(to_dir), "wb") as f:
            f.write(self._last_img)

    def _img_path(self, dir):
        timestamp = int(time.time() * 1000)
        return os.path.join(dir, "{}-{}.jpg".format(self.key, timestamp))

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
