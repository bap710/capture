#!/usr/bin/env python

from PIL import Image
from picamera import PiCamera
from time import sleep
import math
import operator
import sys
import os
import shutil
import datetime

# Based loosely upon the following:
# https://www.raspberrypi.org/documentation/usage/camera/python/README.md
# https://projects.raspberrypi.org/en/projects/timelapse-setup
# https://stackoverflow.com/questions/27868250/python-find-out-how-much-of-an-image-is-black
# etc

DIR='/media/piCam/pics'
TMPFILE=DIR + '/tmp/temp.jpg'
LASTIMG=DIR + '/tmp/last.jpg'

PALETTE = [
    0,   0,   0,  # black,  00
    0,   255, 0,  # green,  01
    255, 0,   0,  # red,    10
    0, 0, 255,  # blue
] + [0, ] * 252 * 3

if __name__ == '__main__':
    now = datetime.datetime.now()
    camera = PiCamera()
    camera.resolution = (2592, 1944)

    camera.capture(TMPFILE)

    image = Image.open(TMPFILE)
    if image == None:
        print "Unable to open image"
        sys.exit(0)

    # a palette image to use for quant
    pimage = Image.new("P", (1, 1), 0)
    pimage.putpalette(PALETTE)
    RGB=image.quantize(colors=256, palette=pimage)
    if RGB == None:
        print "Unable to convert to RGB"
        sys.exit(0)

    colors = RGB.getcolors()

    if colors == None:
        print "Unable to get colors"
        sys.exit(0)

    # Find number of black (0) pixels:
    black_pixels = 0
    for t in colors:
        if t[1] == 0:
            black_pixels = t[0]

    pixels = RGB.width * RGB.height

    percent = int(( float(black_pixels)/float(pixels) ) * 100)

    if percent >= 80:
        # Image is largely black, so ignore it
        os.remove(TMPFILE)
        sys.exit(0)

    if os.path.isfile(LASTIMG):
        h1 = Image.open(LASTIMG).histogram()
        h2 = Image.open(TMPFILE).histogram()
        diff = math.sqrt(reduce(operator.add, map(lambda a,b: (a-b)**2, h1, h2))/len(h1))

        if diff <= 750:
            # Image is very close to last captured image, so ignore it
            os.remove(TMPFILE)
            sys.exit(0)


    dest_path = now.strftime( DIR +"/%m/%d")

    try:
        os.makedirs(dest_path)
    except:
        pass

    dest_file = now.strftime(dest_path + '/%H%M.jpg' )

    try:
        os.remove(LASTIMG)
    except:
        pass
    shutil.copy(TMPFILE, LASTIMG)

    shutil.move(TMPFILE, dest_file)
