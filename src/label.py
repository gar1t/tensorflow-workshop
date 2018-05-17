"""Run image annotation app to generate VOC formatted annotations for images.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import errno
import logging
import os
import signal
import subprocess
import sys
import threading

log = logging.getLogger()

from guild import _api as gapi

import app_util

class ImageWatcher(threading.Thread):

    def __init__(self, src_dir, dest_dir):
        super(ImageWatcher, self).__init__()
        self.src_dir = src_dir
        self.dest_dir = dest_dir
        self._stop_event = threading.Event()

    def start(self):
        self._link()
        super(ImageWatcher, self).start()

    def run(self):
        while True:
            if self._stop_event.wait(2.0):
                break
            self._link()

    def stop(self):
        self._stop_event.set()
        self.join()

    def _link(self):
        for name in _safe_listdir(self.src_dir):
            src = os.path.join(self.src_dir, name)
            dest = os.path.join(self.dest_dir, name)
            _safe_link(src, dest)

def _safe_listdir(d):
    try:
        return os.listdir(d)
    except IOError as e:
        if e.errno != errno.ENOENT:
            raise
        return []

def _safe_link(src, dest):
    dest_dir = os.path.dirname(dest)
    try:
        os.symlink(os.path.relpath(src, dest_dir), dest)
    except IOError as e:
        if e.errno != errno.EEXIST:
            raise
    else:
        sys.stderr.write("Linked {}\n".format(os.path.basename(src)))

def main():
    args = _init_args()
    _maybe_collect_op_images(args)
    watcher = _init_watcher(args)
    watcher.start()
    sys.stderr.write(
        "Running labeling app at http://{}:{}\n".format(
            args.host, args.port))
    proc = subprocess.Popen(
        ["php", "-S", "{}:{}".format(args.host, args.port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=args.app_dir)
    def _stop(_sig, _frame):
        sys.stderr.write("Received SIGTERM - stopping\n")
        proc.terminate()
    signal.signal(signal.SIGTERM, _stop)
    while proc.poll() is None:
        try:
            out = proc.stdout.readline()
        except KeyboardInterrupt:
            break
        else:
            sys.stderr.write(out.decode())
    exit_code = proc.wait()
    watcher.stop()
    sys.exit(exit_code)

def _init_watcher(args):
    src_dir = args.image_dir
    dest_dir = os.path.join(args.app_dir, "data/images")
    return ImageWatcher(src_dir, dest_dir)

def _maybe_collect_op_images(args):
    if not args.image_op:
        return
    for run in gapi.runs_list(
            ops=[args.image_op],
            status=["running", "completed", "terminated"]):
        _link_to_images(run.path, args.image_dir)

def _link_to_images(src, dest):
    for name, path in _iter_images(src):
        app_util.ensure_dir(dest)
        _safe_link(path, os.path.join(dest, name))

def _iter_images(src):
    for root, dirs, files in os.walk(src):
        try:
            dirs.remove(".guild")
        except ValueError:
            pass
        for name in files:
            _, ext = os.path.splitext(name)
            if ext.lower() in (".jpg", ".jpeg"):
                yield name, os.path.join(root, name)

def _init_args():
    p = argparse.ArgumentParser()
    p.add_argument(
        "--host",
        default="0.0.0.0",
        help="App host (0.0.0.0)")
    p.add_argument(
        "--port",
        default=8003,
        type=int,
        help="App port (8003)")
    p.add_argument(
        "--image-dir",
        default="images",
        help="Location of images (images)")
    p.add_argument(
        "--image-op",
        help="Use images from IMAGE_OP runs")
    p.add_argument(
        "--app-dir",
        default="app",
        help="Label app dir (app)")
    return p.parse_args()

if __name__ == "__main__":
    main()
