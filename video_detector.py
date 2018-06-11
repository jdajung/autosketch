import numpy as np
import math
import matplotlib.pyplot as plt
import cv2
import time
import sys
import requests
import webbrowser

from helpers import imshow
from conversions import *
from detector import *
from drawing import *



camera = cv2.VideoCapture(0)

# reduce frame size to speed it up
w = 640
camera.set(3, w)
camera.set(4, w * 3 / 4)

background = None
difFrame = None
still = None
webToggle = False

# capture loop
while True:
    # get frame
    ret, frame = camera.read()
    frame = cv2.flip(frame, 1)

    cv2.imshow('Frame', frame)

    still = frame
    levels = genLevels(still, 'new')
    if len(levels) > 0 and len(levels[0]) > 0:
        root = levels[0][0]
        for i in range(1, len(levels[0])):
            if levels[0][i].area > root.area:
                root = levels[0][i]

        if root != None and webToggle == True:
            b36String = decToBase36String(root.encoding)
            if len(b36String) > 0:
                urlString = 'http://tinyurl.com/' + decToBase36String(root.encoding)
                request = requests.get(urlString, allow_redirects=True)
                if request.status_code == 200:
                    webToggle = False
                    print('Web site exists')
                    webbrowser.open_new_tab(request.url)
                    print request.url
                else:
                    print('Web site does not exist')

        drawMarkers(levels, still)
    cv2.imshow('Markers', still)

    # exit on ESC press
    k = cv2.waitKey(5)
    if k == 27:
        break
    elif k == ord(' '):
        webToggle = not webToggle

cv2.destroyAllWindows()
camera.release()