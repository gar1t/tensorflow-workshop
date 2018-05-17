# pylint: disable=import-error

from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import argparse
import os
import shutil
import sys
import time

import yaml

from guild import op_util
from guild import util

import detect
import snapshot

class Context(object):

    def __init__(self, detector, model, object_class, cameras, events):
        self.detector = detector
        self.model = model
        self.object_class = object_class
        self.cameras = cameras
        self.events = events
        self.step = 0

def main():
    args = _init_args()
    _maybe_copy_config(args)
    config = _init_config(args)
    detector = detect.init_detector(config["detector"])
    model = detector.init_model(config["model"])
    cameras = _init_cameras(config["cameras"])
    events = _init_events()
    context = Context(
        detector,
        model,
        config["object-class"],
        cameras,
        events)
    util.loop(
        lambda: _scan_once(context),
        lambda seconds: _wait(seconds, context),
        config["interval"],
        0)

def _init_args():
    p = argparse.ArgumentParser()
    p.add_argument("-c", "--config", default="scan.yml.in")
    args = p.parse_args()
    return _find_config(args)

def _find_config(args):
    if os.getenv("CMD_DIR") and not os.path.isabs(args.config):
        args.config = os.path.join(os.getenv("CMD_DIR"), args.config)
    return args

def _maybe_copy_config(args):
    if os.getenv("GUILD_OP") and not os.path.exists("config.yml"):
        shutil.copyfile(args.config, "config.yml")

def _init_config(args):
    try:
        return yaml.load(open(args.config, "r"))
    except IOError as e:
        raise SystemExit(e)

def _init_cameras(config):
    return {
        name: _init_camera(config[name])
        for name in config
    }

def _init_camera(config):
    return snapshot.init_camera(
        config["host"],
        config["port"],
        config["user"],
        config["password"])

def _init_events():
    return op_util.TFEvents(os.getcwd())

def _scan_once(context):
    context.step += 1
    counts = {}
    scan_dir = os.path.join("scans", str(int(time.time())))
    sys.stderr.write("Scan #%i\n" % context.step)
    os.makedirs(scan_dir)
    for name in sorted(context.cameras):
        camera = context.cameras[name]
        snapshot_path = os.path.join(scan_dir, name + ".jpg")
        snapshot.snapshot(camera, snapshot_path)
        counts["scans/" + name] = context.detector.detect(
            snapshot_path,
            context.model,
            context.object_class)
    counts["scans/total"] = sum(counts.values())
    context.events.add_scalars(counts.items(), context.step)
    context.events.flush()

def _timestamp():
    return int(time.time())

def _wait(seconds, context):
    try:
        time.sleep(seconds)
    except KeyboardInterrupt:
        sys.stderr.write("Stopping")
        context.events.close()
        sys.stderr.write("\n")
        return True
    else:
        return False

if __name__ == "__main__":
    main()
