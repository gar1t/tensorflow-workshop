# pylint: disable=import-error

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import os

import amcrest

def main():
    args = _init_args()
    camera = init_camera(
        args.cam_host,
        args.cam_port,
        args.cam_user,
        args.cam_password)
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
    image_path = os.path.join(args.output_dir, "snapshot.jpg")
    print("Generating snapshot.jpg with camera at '%s'" % args.cam_host)
    snapshot(camera, image_path)

def _init_args():
    p = argparse.ArgumentParser()
    p.add_argument("--cam-host", default="192.168.1.108")
    p.add_argument("--cam-port", default=80, type=int)
    p.add_argument("--cam-user", default="admin")
    p.add_argument("--cam-password", default="admin")
    p.add_argument("--output-dir", default="images")
    return p.parse_args()

def init_camera(host, port, user, password):
    ac = amcrest.AmcrestCamera(host, port, user, password)
    return ac.camera

def snapshot(camera, image_path):
    camera.snapshot(0, image_path)

if __name__ == "__main__":
    main()
