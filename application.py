import numpy as np
import math
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import cv2
import time
import sys
import requests
import os
import datetime
import tkFileDialog
import tkFont
import threading
import mutex
import itertools

from Tkinter import *
from PIL import Image
from PIL import ImageTk
from helpers import imshow
from conversions import *
from detector import *
from drawing import *
from random import randint
from part_division import *

#global constants
BASE_PATH = os.getcwd()
SESSION_PATH = BASE_PATH + "/sessions"
CANVAS_WIDTH = 1200
CANVAS_HEIGHT = 720
INTERP_DIST = 3
NUM_UNDO_STATES = 11 #number of undos will be one less than this
BLACK = (0,0,0)
GREY = (100,100,100) #unused in parent version
WHITE = (255,255,255)
LIGHT_YELLOW = (153,255,255)

#global variables
targetBinString = '11001101'#'1110010110110011001110101101101111' #Put your target encoding here!

#the rest of these variables should be left alone

targetEncoding = binaryStringToDec(targetBinString)[0]

tkRoot = Tk()
suggestionPoint1 = (5, 20)
suggestionPoint2 = (5, 40)
targetPoint = (5, CANVAS_HEIGHT - 3)

usingThreading = False #Do not set to True; this doesn't work
vTFontSize = 16
vTWidth = 13
redText = 'red'
greenText = '#00cc00'

plusMinusFont = tkFont.Font(family='Helvetica', size=40, weight='bold')
buttonTextFont = tkFont.Font(family='Helvetica', size=12)
visualTargetFont = tkFont.Font(family='Courier', size=vTFontSize)
sliderFont = tkFont.Font(family='Helvetica', size=10)

markerMode = 'new'  # 'new' only; 'dtouch' not functional in this version
expPhase = 3 # set to 3 for full markers (values 1 & 2 mimic conditions for corresponding experimental phases of the paper)
blobMode = 'number'
blobOrderMode = 'area'
partOrderMode = 'area'
mode = 'idle'  # 'idle', 'drawing', 'erasing'
tool = 'pen'
lastX = -1
lastY = -1
drawColour = (0, 0, 0)
drawRadius = 10
suggestions = [] #suggestions are not functional in this version
vTOffset = 2
vTTopLeft = (20, 720)#(1210, 450)
extraWidth = 600
targetExtras = []

drawEncodings = 0
drawCentroids = 0
drawAmbToggle = 0
suggestionIndex = 0
drawTargetToggle = 0
drawContoursToggle = 0

#reset global variables to initial values
def resetVars():
    global mode, drawColour, drawRadius, suggestions, targetEncoding, drawEncodings, drawCentroids, \
        drawAmbToggle, suggestionIndex, suggestionTopString

    mode = 'idle'
    drawColour = (0, 0, 0)
    drawRadius = 10
    suggestions = []
    drawEncodings = 0
    drawCentroids = 0
    drawAmbToggle = 0
    suggestionIndex = 0
    suggestionTopString = ""


#draw to the canvas on mouse events
#interpolate between this and the last event if the mouse was held down
#x: x-position of mouse
#y: y-position of mouse
def drawStuff(x, y):
    global mode, lastX, lastY, img, markedImg
    if mode == 'drawing':
        cv2.circle(img, (x, y), drawRadius, drawColour, -1)
        if lastX != -1 and lastY != -1:
            points = [[x,y],[lastX,lastY]]
            points.sort()
            pointDist = euclideanDist(points[0], points[1])
            numInterpPoints = int(math.floor(pointDist/INTERP_DIST)) - 1
            if numInterpPoints > 0:
                xSegmentLength = float(points[1][0]-points[0][0]) / (numInterpPoints+1)
                ySegmentLength = float(points[1][1]-points[0][1]) / (numInterpPoints+1)
                interpXList = [points[0][0] + (i+1)*xSegmentLength for i in range(numInterpPoints)]
                interpYList = [points[0][1] + (i+1)*ySegmentLength for i in range(numInterpPoints)]
                for i in range(numInterpPoints):
                    cv2.circle(img, (int(round(interpXList[i])), int(round(interpYList[i]))), drawRadius, drawColour, -1)

    lastX = x
    lastY = y
    updateEncodings()

#currently just calls the real updateEncodings function
#implementing threading went...badly


######### Code for adding a blob #############
def updateEncodings():
    global usingThreading
    if not usingThreading:
        updateEncodingsForReal()

def satisfy_check(level,x,y):
    global img
    for child in level.children:
        if not out_contour(x ,y , child.contour):
            print("Failed in satisfy_check")
            # cv2.circle(img,(x,y),1,(255,0,0),-1)
            return False

    return True

def out_contour(x, y, contour,radius_multiplier=3):
    global drawRadius
    ret = cv2.pointPolygonTest(contour, (y, x), True)
    if ret > -(radius_multiplier*drawRadius):
        return False

    return True

def in_contour( x, y, contour, radius_multiplier=3):
    ret = cv2.pointPolygonTest(contour, (y, x), True)
    if ret < (radius_multiplier*drawRadius):
        # print("Failed in in_contour")
        return False

    return True

def add_blob(part):
    global img,drawRadius,drawColour
    radius = 5
    colour = BLACK

    extreme_left = tuple(part.contour[part.contour[:, :, 0].argmin()][0]) # extreme_left
    extreme_right = tuple(part.contour[part.contour[:, :, 0].argmax()][0]) # extreme_right
    extreme_top = tuple(part.contour[part.contour[:, :, 1].argmin()][0]) # extreme_top
    extreme_bottom = tuple(part.contour[part.contour[:, :, 1].argmax()][0]) # extreme_bottom
    print(extreme_top,extreme_bottom,extreme_left,extreme_right)
    # cv2.circle(img,extreme_left,1,(255,0,0),-1)
    # cv2.circle(img,extreme_right,1,(0,0,255),-1)
    # cv2.circle(img,extreme_top,1,(0,255,0),-1)
    # cv2.circle(img,extreme_bottom,1,(255,0,255),-1)
    range_in_x = (extreme_top[1],extreme_bottom[1])
    range_in_y = (extreme_left[0],extreme_right[0])
    count = 0
    max_count = 100

    while count < max_count:
        sampled_x = int(np.random.uniform(range_in_x[0],range_in_x[1],1))
        sampled_y = int(np.random.uniform(range_in_y[0],range_in_y[1],1))

        if satisfy_check(part,sampled_x,sampled_y) and in_contour(sampled_x,sampled_y,part.contour):
            print("Drawing on %d %d" % (sampled_x,sampled_y))
            cv2.circle(img, (sampled_y, sampled_x), radius, colour, -1)
            # updateEncodings()
            break
        count += 1
        print(sampled_x,sampled_y,"No")
    if count >= max_count:
        print "ERROR: No valid location found for blob placement"

def increase_blob(source='button'):
    global undoStack, undoIndex, img, globalLevels
    exit_protect_mode()
    print(globalLevels)
    for part in globalLevels[1]:
        add_blob(part)
    updateEncodings()
    logEvent(source + 'increase')

#########################################


####### Code for Deleting a blob #######

def delete_blob(blob):
    global img
    cv2.fillPoly(img, pts =[blob.contour], color=(255,255,255))
    # updateEncodings()

def delete_first_blob(part):
    if not part.children:
        print "ERROR: Cannot delete blob because the given part contains no blobs"
    else:
        blob = part.children[0]
        delete_blob(blob)
        part.children = part.children[1:]

def decrease_blob(source='button'):
    global undoStack, undoIndex, img, globalLevels
    exit_protect_mode()
    print(globalLevels)
    for level in globalLevels[1]:
        if len(level.children) > 2:
            blob_with_min_area = min(level.children,key = lambda x: x.area)
            delete_blob(blob_with_min_area)
    updateEncodings()
    logEvent(source + 'decreases')

##########################################


##### Join a Blob to the nearest blob #######

def closest_pair_of_points_between_blobs(blob1,blob2):
    points1 = blob1.approx
    points2 = blob2.approx
    min_pair = None
    min_dist = np.linalg.norm(points1[0]-points2[0])
    for p1 in points1:
        for p2 in points2:
            dist = np.linalg.norm(p1[0]-p2[0]) 
            if dist < min_dist:
                min_pair = (p1,p2)
                min_dist = dist

    return [min_pair,min_dist]

def closest_pair_of_blobs_points(blobs):
    accumulator = []
    for pair in itertools.combinations(blobs,2):
        accumulator.append(closest_pair_of_points_between_blobs(*pair))

    return min(accumulator,key = lambda x : x[1])

def join_2_points(p1, p2):
    global img
    cv2.line(img,(p1[0][0],p1[0][1]),(p2[0][0],p2[0][1]),(0,0,0),drawRadius)
    updateEncodings()


def join_blobs(source='button'):
    global img,globalLevels
    exit_protect_mode()

    for level in globalLevels[1]:
        if len(level.children) > 1:
            pairs,_ = closest_pair_of_blobs_points(level.children)
            join_2_points(*pairs)
            # blob_with_min_area = min(level.children,key = lambda x: x.area)

###### Join a Blob to the nearest edge #####


def join_blob_to_edge(source='button'):
    exit_protect_mode()

    for level in globalLevels[1]:
        for blob in level.children:
            pairs,_ = closest_pair_of_points_between_blobs(blob,level)
            join_2_points(*pairs)

###### Split a blob #######

def split_blob(blob):
    pass





############################################


def set_target_dividers(posn_list):
    global targetDividers
    resetTargetDividers()
    for posn in posn_list:
        targetDividers = targetDividers[:posn] + '|' + targetDividers[posn+1:]

def auto_fix_blobs(prefVal=0.0):
    global mainRoot, targetBinString, targetDividers
    cost_base = 10
    protected_multiplier = 100

    if mainRoot is None or not mainRoot.children:
        print "Cannot fix blobs; No parts found"
        return

    img_part_vals = []
    sorted_parts = sortParts(mainRoot, 'area')
    multipliers = []
    for part in sorted_parts:
        img_part_vals.append(part.encoding)
        if part.protected:
            multipliers.append(protected_multiplier)
        else:
            multipliers.append(1)

    fixed_target = find_divisions(img_part_vals,targetBinString,exp_weight_cost_fun(cost_base, prefVal),multipliers)
    target_part_vals = fixed_target[1]
    set_target_dividers(fixed_target[2])

    for i in range(len(sorted_parts)):
        sorted_parts[i].children = sortBlobs(sorted_parts[i], 'area')
        counter = 0
        max_count = 100
        while img_part_vals[i] != target_part_vals[i] and counter < max_count:
            if img_part_vals[i] < target_part_vals[i]:
                add_blob(sorted_parts[i])
                img_part_vals[i] += 1
            else:
                delete_first_blob(sorted_parts[i])
                img_part_vals[i] -= 1
        if counter >= max_count:
            print "ERROR: Fix blobs failed with too many attempts"
    updateEncodings()

def auto_fix_blobs_btn(source='button'):
    global addRemovePrefScale
    exit_protect_mode()
    prefVal = addRemovePrefScale.get()
    prefVal = float(prefVal)/20.0
    auto_fix_blobs(prefVal)
    updateEncodings()
    logEvent(source + 'auto_fix_blobs')

def protect_btn(source='button'):
    global tool, protectBtn
    if tool == 'protect':
        exit_protect_mode()
    else:
        protectBtn.config(relief=SUNKEN)
        tool = 'protect'
    logEvent(source + 'protect_toggle')

def exit_protect_mode():
    global tool, protectBtn, protectImg, drawProtected
    protectBtn.config(relief=RAISED)
    tool = 'pen'
    protectImg = np.ones((CANVAS_HEIGHT, CANVAS_WIDTH, 3), np.uint8) * 255
    drawProtected = False

def toggle_blob_protection(x, y):
    global mainRoot
    if mainRoot is None:
        return
    selected = None
    for part in mainRoot.children:
        if in_contour(x, y, part.contour, 0):
            selected = part
            break
    if selected is not None:
        if selected.protected:
            selected.protected = False
        else:
            selected.protected = True
    colour_protected()

def colour_protected():
    global mainRoot, protectImg, drawProtected
    protectImg = np.ones((CANVAS_HEIGHT, CANVAS_WIDTH, 3), np.uint8) * 255
    drawProtected = False
    if mainRoot is not None:
        for part in mainRoot.children:
            if part.protected:
                cv2.drawContours(protectImg, [part.contour], -1, LIGHT_YELLOW, -1)
                drawProtected = True
    updateGuiImage()


####### Code for Reducing a part #######


def cut_part(part):
    global img
    print img.shape
    point = np.random.choice(range(len(part.contour)),1)
    #slope = inf
    y, x = part.contour[point][0][0]
    # cv2.circle(img, (y,x), 2 , (255,0,0), -1)
    centre_y,centre_x = part.centroid
    # cv2.circle(img, (centre_y,centre_x), 2 , (0,255,0), -1)
    # mcentre_x, mcentre_y = 2*centre[0] - x, 2*centre[1] - y
    slope = (centre_y - y) / float(centre_x - x)
    bw  = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # cv2.line(img,(y,x),(centre_y,centre_x),(255,0,255),5)
    # print slope,centre_y - y,centre_x - x
    distance = 15.0
    while True:
        new_x = (x + distance / (np.sqrt(1 + slope**2)))
        new_y = (y + slope*(new_x - x))
        new_x1 = (x - distance / (np.sqrt(1 + slope**2)))
        new_y1 = (y + slope*(new_x1 - x))
        if ((new_x1-centre_x)**2 + (new_y1-centre_y)**2) > ((new_x-centre_x)**2 + (new_y-centre_y)**2):
            final_x,final_y = int(new_x1),int(new_y1)
        else:
            final_x,final_y = int(new_x),int(new_y)
        # print x,y,centre_x,centre_y,new_x1,new_y1,new_x,new_y
        # cv2.circle(img, (int(new_y),int(new_x)), 3 , (0,0,255), -1)
        # cv2.circle(img, (int(new_y1),int(new_x1)), 3 , (0,0,255), -1)
        # cv2.circle(img, (final_y,final_x), 3 , (0,255,255), -1)
        # break
        val = bw[final_x,final_y]
        if val == 255:
            break
        distance = distance + 1
    cv2.line(img,(y,x),(final_y,final_x),(255,255,255),5)
    updateEncodings()

# def cut_part(part):
#     global img,drawRadius
#     point = np.random.choice(range(len(part.contour)),1)
#     print part.contour[point][0][0]
#     x, y = part.contour[point][0][0]
#     temp_part = part.contour
#     temp_part = np.delete(temp_part,point,0)
#     closest_point = min(temp_part,key = lambda v: (v[0][0] - x)**2 + (v[0][1] - y)**2)
#     print(closest_point)
#     c_x ,c_y = closest_point[0]
#     dv_x = x - c_x
#     dv_y = y - c_y
#     mag = np.sqrt(dv_x**2 + dv_y**2)
#     dv_x = dv_x/mag
#     dv_y = dv_y/mag
#     temp = dv_x 
#     dv_x = -dv_y 
#     dv_y = temp
#     length = 1
#     while True:
#         new_x = int(x + dv_x * length)
#         new_y = int(y + dv_y * length)
#         print(new_x,new_y)
#         b,g,r = img[new_x,new_y,:]
#         if b == 255 and g == 255 and r == 255:
#             break
#         length = length + 2
#     cv2.line(img,(x,y),(new_x,new_y),(255,0,0),4)
#     # cv2.circle(img, (x,y), drawRadius , (255,255,255), -1) # @todo : store the size of radius at each point
#     updateEncodings()

def bounding_box_check(part1, part2):
    max_dist = 20 #Maximum allowable distance between bounding boxes
    if part1.box is None:
        part1.box = cv2.boundingRect(part1.approx)
    if part2.box is None:
        part2.box = cv2.boundingRect(part2.approx)
    p1_left = part1.box[0]
    p1_right = part1.box[0] + part1.box[2]
    p1_top = part1.box[1]
    p1_bot = part1.box[1] + part1.box[3]
    p2_left = part2.box[0]
    p2_right = part2.box[0] + part2.box[2]
    p2_top = part2.box[1]
    p2_bot = part2.box[1] + part2.box[3]
    checks = [p1_right-p2_left,p2_right-p1_left,p1_bot-p2_top,p2_bot-p1_top]
    ans = True
    for check in checks:
        if check < -max_dist:
            ans = False
    return ans

def manhattan_dist(p1,p2):
    return abs(p1[0]-p2[0]) + abs(p1[1]-p2[1])

def choose_contour_points(contour):
    min_sep = 20 #minimum Manhattan distance between consecutive points
    if contour is None or len(contour) <= 0:
        return []
    selected = [contour[0][0]]
    print type(selected[0]), selected[0]
    for item in contour:
        if manhattan_dist(item[0], selected[-1]) >= min_sep:
            selected.append(item[0])
    return selected

def closest_point_pairs():
    global mainRoot, markedImg
    if mainRoot is None or len(mainRoot.children) <= 1:
        return
    print type(mainRoot.contour)
    print mainRoot.contour
    #check pairs of parts
    for i in range(len(mainRoot.children)):
        part1 = mainRoot.children[i]
        for j in range(i+1,len(mainRoot.children)):
            part2 = mainRoot.children[j]
            if bounding_box_check(part1,part2):
                if part1.select_points is None:
                    part1.select_points = choose_contour_points(part1.contour)
                if part2.select_points is None:
                    part2.select_points = choose_contour_points(part2.contour)
                cv2.line(markedImg,part1.centroid,part2.centroid,(0,0,255),2)
                for point in part1.contour:
                    cv2.circle(markedImg, tuple(point[0]), 4, (0,255,0), -1)
                for point in part1.select_points:
                    cv2.circle(markedImg, tuple(point), 2, (255,0,0), -1)
                

    updateGuiImage()

    #check parts to root

def reduce_part(source='button'):
    global undoStack, undoIndex, img, globalLevels
    closest_point_pairs()
    exit_protect_mode()
    # for level in globalLevels[1]:
    #     cut_part(level)
    logEvent(source + 'reduce_part')

##########################################



###### Determine adjacent point ########

def determine_adjacent(point1, point2):
    global img 
    bw  = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    slope = (point2[0] - point1[0]) / float(point2[1] - point2[1])
    angle = np.arctan2(point2[0] - point1[0],point2[1] - point2[1])
    distance = 1
    nw,nb = -1,0
    while True:
        new_x = distance*np.cos(angle) + point1[1]
        new_y = distance*np.sin(angle) + point1[0]
        val = bw[int(np.round(new_x)),int(np.round(new_y))]
        if  val == 255:
            if nb == 0:
                nw1 += 1
            else:
                nw2 += 1
        elif val == 0:
            if nw2 != 0:
                return False
            else:
                nb += 1

        distance += 1

    if nw > -1 and nb > 0 and nw2 > -1:
        return True
    
    return False

#######################################




#figures out the current encoding of the image and updates all overlays
def updateEncodingsForReal():
    global drawEncodings, drawCentroids, drawAmbToggle, suggestionIndex, suggestionImg, suggestions, \
        suggestionLocs, drawTargetToggle, img, markedImg, mainRoot, expPhase, blobMode, oldEncoding, \
        blobOrderMode, blobIconDict, oldPartNum, globalLevels, usingThreading, oldEncodingNum
    markedImg = img.copy()

    #find the region adjacency tree of the image
    if not usingThreading:
        determineMainRoot()
    levels = globalLevels

    #determine if the encoding has changed. If it has, update the target panel
    currEncoding = -1
    currPartNum = -1
    currEncodingNum = -1
    if mainRoot != None:
        if expPhase == 1 or expPhase == 2 or expPhase == 3:
            currEncoding = mainRoot.encChunks
        currPartNum = len(mainRoot.children)
        currEncodingNum = mainRoot.encoding
    if currPartNum != oldPartNum or oldEncodingNum != currEncodingNum or currEncoding != oldEncoding:
        updateVisualTargetPanel()
        oldEncoding = currEncoding
        oldPartNum = currPartNum
        oldEncodingNum = currEncodingNum

    #draw output of labeller tool
    if drawEncodings != 0:
        if blobMode == 'number':
            drawMarkerParts(levels, markedImg)
        else:
            drawMarkerPartsPictoral(levels, markedImg, blobIconDict, blobMode)

    #draw output of ordering tool
    if drawCentroids != 0:
        if expPhase == 2:
            if blobMode == 'number':
                pass
            elif blobOrderMode == 'distance':
                drawBlobCentroidCircles(levels, markedImg, blobOrderMode, partOrderMode)
            elif blobOrderMode == 'area':
                drawBlobAreas(levels, markedImg, blobOrderMode, partOrderMode)
        elif expPhase == 3:
            if blobMode == 'number' or drawCentroids == 1:
                if partOrderMode == 'distance':
                    drawPartCentroidCircles(levels, markedImg, partOrderMode)
                elif partOrderMode == 'area':
                    drawPartAreas(levels, markedImg, partOrderMode)
            else:
                if blobOrderMode == 'distance':
                    drawBlobCentroidCircles(levels, markedImg, blobOrderMode, partOrderMode)
                elif blobOrderMode == 'area':
                    drawBlobAreas(levels, markedImg, blobOrderMode, partOrderMode)

        #dtouch mode disabled for this version
        # if markerMode == 'dtouch':
        #     if drawCentroids == 1:
        #         drawDtouchOrdering(levels, markedImg)
        # else:
        #     if drawCentroids == 1:
        #         drawBlobCentroidCircles(levels, markedImg, blobOrderMode, partOrderMode)
        #     elif drawCentroids == 2:
        #         drawPartCentroidCircles(levels, markedImg, partOrderMode)

    #draw output of ambiguity tool
    if drawAmbToggle != 0:
        if drawAmbToggle == 1:
            drawAmbiguities(levels, markedImg, blobOrderMode, partOrderMode)

    #draw contours of region adjacency tree (hidden feature)
    if drawContoursToggle != 0:
        if len(levels) >= drawContoursToggle:
            for comp in levels[drawContoursToggle - 1]:
                cv2.drawContours(markedImg, comp.contour, -1, (0, 255, 0), 3)
                #optionally, draw all contours simultaneously
                # for i in range(3):
                #    for comp in levels[i]:
                #        cv2.drawContours(markedImg, comp.contour, -1, (0,255,0), 3)

    #suggestion feature not fully implemented in this version
    # if suggestionIndex < len(suggestions):
    # markedImg[suggestionLocs[0], suggestionLocs[1]] = suggestionImg[suggestionLocs[0], suggestionLocs[1]]
    # if levels == None:
    #    levels = genLevels(img, expPhase, blobMode, blobOrderMode, partOrderMode)
    # drawSuggestion(suggestionIndex+1, suggestions[suggestionIndex], levels, markedImg)

    updateGuiImage()


#suggestion feature not fully implemented in this version
def suggestionOutput():
    global suggestionIndex, suggestions, suggestionImg, suggestionLocs, suggestionPoint1, suggestionPoint2, \
        suggestionTopString, img, markedImg, mainRoot, expPhase, blobMode, blobOrderMode

    suggestionImg = np.ones((CANVAS_HEIGHT, CANVAS_WIDTH, 3), np.uint8) * 255
    cv2.putText(suggestionImg, suggestionTopString, suggestionPoint1, \
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
    if suggestions != None and suggestionIndex < len(suggestions):
        levels = genLevels(img, expPhase, blobMode, blobOrderMode, partOrderMode)
        # printSuggestion(suggestionIndex+1, suggestions[suggestionIndex], levels, markedImg)
        drawSuggestion(suggestionIndex + 1, suggestions[suggestionIndex], suggestionPoint2, levels, suggestionImg)
    suggestionLocs = np.where(suggestionImg != (255, 255, 255))


#apply colour and radius changes to the brush
def updateBrush():
    global mode, drawColour, drawRadius, brush
    brush = np.ones((100, 100, 3), np.uint8) * 255
    if drawColour != (255,255,255):
        cv2.circle(brush, (50, 50), drawRadius, drawColour, -1)
    else:
        cv2.circle(brush, (50, 50), drawRadius, (0,0,0), 1)
    updateGuiBrush()


#get the region adjacency tree, store it in globalLevels, find the largest root contour, and store it in mainRoot
def determineMainRoot():
    global img, expPhase, blobMode, blobOrderMode, globalLevels, mainRoot, levelsMutex

    levels = genLevels(img, expPhase, blobMode, blobOrderMode, partOrderMode)
    if levels == [] or levels[0] == []:
        clearRootAndLevels()
        return

    root = levels[0][0]
    for i in range(1, len(levels[0])):
        if levels[0][i].area > root.area:
            root = levels[0][i]

    #some failed threading stuff; nothing to see here...
    while not levelsMutex.testandset():
        pass

    globalLevels = levels
    mainRoot = root
    levelsMutex.unlock()
    # return root


#suggestion feature not fully implemented in this version
def resetSuggestions():
    global suggestions, suggestionIndex, suggestionImg, suggestionLocs, suggestionTopString, targetEncoding, mainRoot
    suggestionImg = np.ones((CANVAS_HEIGHT, CANVAS_WIDTH, 3), np.uint8) * 255
    suggestionLocs = np.where(suggestionImg != (255, 255, 255))
    suggestionIndex = 0
    suggestionOutput()
    updateEncodings()
    resetGuiImage()


#suggestion feature not fully implemented in this version
def genSuggestions():
    global suggestions, suggestionIndex, suggestionImg, suggestionLocs, suggestionTopString, targetEncoding, mainRoot
    determineMainRoot()
    suggestionImg = np.ones((CANVAS_HEIGHT, CANVAS_WIDTH, 3), np.uint8) * 255
    suggestionLocs = np.where(suggestionImg != (255, 255, 255))
    suggestionIndex = 0
    if mainRoot != None:
        if len(mainRoot.children) > 0:
            suggestions = findSuggestions(mainRoot, targetEncoding)
            suggestionIndex = 0
            if len(suggestions) > 0:
                suggestionTopString = str(len(suggestions)) + " step process generated."
            else:
                suggestionTopString = "No steps needed. You're done!"
        else:
            suggestionTopString = "Produce at least one closed part to enable suggestions."
    else:
        suggestionTopString = "No roots to generate suggestions for."
    suggestionOutput()
    updateEncodings()
    logEvent('genSuggestions')


#add the current canvas to the undo stack, making it available for future undos (undoes?)
def addUndoable():
    global undoStack, undoIndex, img
    if len(undoStack)-undoIndex+1 <= NUM_UNDO_STATES:
        undoStack = [np.copy(img)] + undoStack[undoIndex:]
    else:
        undoStack = [np.copy(img)] + undoStack[undoIndex:-1]
    undoIndex = 0


#perform one undo action on the canvas
def undo(source='button'):
    global undoStack, undoIndex, img
    exit_protect_mode()
    if undoIndex < len(undoStack)-1:
        img = np.copy(undoStack[undoIndex+1])
        undoIndex += 1
        updateEncodings()
    logEvent(source + 'Undo')


#perform one redo action on the canvas
def redo(source='button'):
    global undoStack, undoIndex, img
    exit_protect_mode()
    if undoIndex > 0:
        img = np.copy(undoStack[undoIndex-1])
        undoIndex -=1
        updateEncodings()
    logEvent(source + 'Redo')


#handles mouse clicks
def leftMouseDown(event):
    global mode, tool
    if tool == 'protect':
        toggle_blob_protection(event.x, event.y)
    else:
        mode = 'drawing'
        drawStuff(event.x, event.y)
    logEvent('leftMouseDown', event.x, event.y)


#handles mouse releases
def leftMouseUp(event):
    global lastX, lastY, tool
    if tool == 'protect':
        pass
    else:
        mode = 'idle'
        lastX = -1
        lastY = -1
        addUndoable()
    logEvent('leftMouseUp', event.x, event.y)


#handles mouse dragging while clicked
def leftMouseMove(event):
    global tool
    if tool == 'protect':
        pass
    else:
        drawStuff(event.x, event.y)
    logEvent('leftMouseMove', event.x, event.y)


#handles keyboard inputs
#escape - closes the program
#1 - changes draw colour to black
#2 - changes draw colour to white (i.e. erase)
#+ or > - increases size of brush
#- or < - decreases size of brush
#z - does one undo
#shift+z - does one redo
#shift+c - clears the canvas
#tab - toggles the labelling tool
#space - toggles the ordering tool
#a - toggles the ambiguity tool
#o - toggles the contour tool
#m - change encoding modes
#shift+s - saves the current canvas as a PNG
#shift+l - loads the last saved PNG (WILL CLEAR THE CURRENT CANVAS, but is undoable)
#shift+f - same as shift+s, but enters a 'failure' code in the log (used in study, but otherwise not needed)
#shift+p - same as shift+s, but enters a 'practice' code in the log (used in study, but otherwise not needed)
#shift+g - generate a random bitstring of length 10 (used in study, but otherwise not needed)
#shift+h - generate a random bitstring of length 20 (used in study, but otherwise not needed)
def keyPress(event):
    global timer, waitAmount, drawRadius, markerMode, drawCentroids, drawAmbToggle, drawTargetToggle, img, \
        markedImg, suggestionTopString, drawColour, drawContoursToggle, drawEncodings, suggestionIndex, tkRoot
    if event.char == '1':
        drawColour = BLACK
        updateBrush()
        logEvent('colorBlack')
    #grey not available in this version
    # elif event.char == '3':
    #     drawColour = GREY
    #     updateBrush()
    #     logEvent('colorGrey')
    elif event.char == '2':
        drawColour = WHITE
        updateBrush()
        logEvent('colorWhite')
    elif event.char == '+' or event.char == '.' or event.char == '=' or event.char == '>':
        growBrush('keyboard')
    elif event.char == '-' or event.char == ',' or event.char == '_' or event.char == '<':
        shrinkBrush('keyboard')
    elif event.char == ' ':
        toggleOrder('keyboard')
    elif event.char == 'S':
        saveCanvas(0)
    elif event.char == 'F':
        saveCanvas(1)
    elif event.char == 'P':
        saveCanvas(2)
    elif event.char == 'a':
        toggleAmb('keyboard')
    elif event.char == 'C':
        clearCanvas('keyboard')
    elif event.char == 'L':
        loadLast()
    #suggestions not fully implemented in this version
    # elif event.char == 'h':
    #     genSuggestions()
    elif event.char == 'o':
        toggleContours('keyboard')
    elif event.char == 'z':
        undo('keyboard')
    elif event.char == 'Z':
        redo('keyboard')
    elif event.char == 'm' or event.char == 'M':
        switchExpMode()
    elif event.char == 'G':
        genNewTarget(10)
    elif event.char == 'H':
        genNewTarget(20)
    elif event.keycode == 9:  # Tab
        toggleLabeller('keyboard')
    # suggestions not fully implemented in this version
    # elif event.keycode == 39:  # right arrow
    #     nextSuggestion()
    # elif event.keycode == 37:  # left arrow
    #     previousSuggestion()
    elif event.keycode == 27:  # Esc
        exitApp()


#change between encoding schemes depending on the experimental phase (default expPhase = 3)
def switchExpMode():
    global expPhase, blobMode, blobOrderMode, partOrderMode
    if expPhase == 1:
        if blobMode == 'number':
            blobMode = 'convexity'
        elif blobMode == 'convexity':
            blobMode = 'hollow'
        elif blobMode == 'hollow':
            blobMode = 'convexityHollow'
        else:
            blobMode = 'number'

    elif expPhase == 2:
        resetTargetDividers()
        if blobMode == 'number':
            blobMode = 'hollow'
            blobOrderMode = 'area'
        elif blobMode == 'hollow' and blobOrderMode == 'area':
            blobOrderMode = 'distance'
        elif blobMode == 'hollow' and blobOrderMode == 'distance':
            blobMode = 'convexityHollow'
            blobOrderMode = 'area'
        elif blobMode == 'convexityHollow' and blobOrderMode == 'area':
            blobOrderMode = 'distance'
        elif blobMode == 'convexityHollow' and blobOrderMode == 'distance':
            blobMode = 'number'

    elif expPhase == 3:
        resetTargetDividers()
        resetVTPartNums()
        if blobMode == 'number' and partOrderMode == 'area':
            partOrderMode = 'distance'
        elif blobMode == 'number' and partOrderMode == 'distance':
            blobMode = 'hollow'
            blobOrderMode = 'area'
            partOrderMode = 'area'
        elif blobMode == 'hollow' and partOrderMode == 'area':
            blobOrderMode = 'area'
            partOrderMode = 'distance'
        elif blobMode == 'hollow' and blobOrderMode == 'area' and partOrderMode == 'distance':
            blobOrderMode = 'distance'
        elif blobMode == 'hollow' and blobOrderMode == 'distance' and partOrderMode == 'distance':
            blobMode = 'convexityHollow'
            blobOrderMode = 'area'
            partOrderMode = 'area'
        elif blobMode == 'convexityHollow' and blobOrderMode == 'area' and partOrderMode == 'area':
            blobMode = 'convexityHollow'
            blobOrderMode = 'area'
            partOrderMode = 'distance'
        elif blobMode == 'convexityHollow' and blobOrderMode == 'area' and partOrderMode == 'distance':
            blobMode = 'convexityHollow'
            blobOrderMode = 'distance'
            partOrderMode = 'distance'
        elif blobMode == 'convexityHollow' and blobOrderMode == 'distance' and partOrderMode == 'distance':
            blobMode = 'number'
            partOrderMode = 'area'

    updateEncodings()
    updateMarkerModePanel()
    updateVisualTargetPanel()
    logEvent('switchExpMode')


#returns the condition number associated with the current encoding scheme
def getModeNum():
    global expPhase, blobMode, blobOrderMode
    returnVal = -1
    if expPhase == 1:
        if blobMode == 'number':
            returnVal = 0
        elif blobMode == 'convexity':
            returnVal = 1
        elif blobMode == 'hollow':
            returnVal = 2
        elif blobMode == 'convexityHollow':
            returnVal = 3
        else:
            print "ERROR: Unrecognized blobMode in getModeNum"

    elif expPhase == 2:
        if blobMode == 'number':
            returnVal = 0
        elif blobMode == 'hollow' and blobOrderMode == 'area':
            returnVal = 1
        elif blobMode == 'hollow' and blobOrderMode == 'distance':
            returnVal = 2
        elif blobMode == 'convexityHollow' and blobOrderMode == 'area':
            returnVal = 3
        elif blobMode == 'convexityHollow' and blobOrderMode == 'distance':
            returnVal = 4

    elif expPhase == 3:
        if blobMode == 'number' and partOrderMode == 'area':
            returnVal = 0
        elif blobMode == 'number' and partOrderMode == 'distance':
            returnVal = 1
        elif blobMode == 'hollow' and partOrderMode == 'area':
            returnVal = 2
        elif blobMode == 'hollow' and blobOrderMode == 'area' and partOrderMode == 'distance':
            returnVal = 3
        elif blobMode == 'hollow' and blobOrderMode == 'distance' and partOrderMode == 'distance':
            returnVal = 4
        elif blobMode == 'convexityHollow' and blobOrderMode == 'area' and partOrderMode == 'area':
            returnVal = 5
        elif blobMode == 'convexityHollow' and blobOrderMode == 'area' and partOrderMode == 'distance':
            returnVal = 6
        elif blobMode == 'convexityHollow' and blobOrderMode == 'distance' and partOrderMode == 'distance':
            returnVal = 7

    return returnVal


# suggestions not fully implemented in this version
def nextSuggestion():
    global suggestionIndex, suggestions
    suggestionIndex = (suggestionIndex + 1) % (len(suggestions) + 1)
    suggestionOutput()
    updateEncodings()
    logEvent('nextSuggestion')


# suggestions not fully implemented in this version
def previousSuggestion():
    global suggestionIndex, suggestions
    suggestionIndex = (suggestionIndex - 1) % (len(suggestions) + 1)
    suggestionOutput()
    updateEncodings()
    logEvent('previousSuggestion')


#saves the current canvas as a numbered PNG file
def saveCanvas(saveCode):
    global img, dirPath, imgPath
    imgPath = nextFileNum(dirPath, 'img', 'png')[1]
    cv2.imwrite(imgPath, img)
    logEvent('saveCanvas', saveCode, getModeNum())
    clearCanvas(source='save')
    startNewLog()


#loads the most recent saved image onto the canvas (replaces current canvas)
def loadLast():
    global img, markedImg, suggestionTopString, imgPath
    if imgPath != '':
        img = cv2.imread(imgPath)
        markedImg = img.copy()
        suggestionTopString = ""
        resetSuggestions()
        updateEncodings()
    logEvent('loadLast')


#toggles contour overlay between root, part, blob, and off
#source indicates where the command came from (UI button or keyboard) for the purpose of logging
def toggleContours(source='button'):
    global drawContoursToggle
    drawContoursToggle = (drawContoursToggle + 1) % 4
    updateEncodings()
    logEvent(source + 'ToggleContours')


#toggles the ambiguity overlay on and off
#source indicates where the command came from (UI button or keyboard) for the purpose of logging
def toggleAmb(source='button'):
    global drawAmbToggle
    drawAmbToggle = (drawAmbToggle + 1) % 2
    updateEncodings()
    logEvent(source + 'ToggleAmb')
    updateAmbPanel()


#toggles the ordering overlay beetween parts, blobs, and off
#source indicates where the command came from (UI button or keyboard) for the purpose of logging
def toggleOrder(source='button'):
    global markerMode, drawCentroids, expPhase, blobMode, blobOrderMode
    # dtouch mode disabled for this version
    # if markerMode == 'dtouch':
    #     drawCentroids = (drawCentroids + 1) % 2
    # else:
    #     drawCentroids = (drawCentroids + 1) % 3
    if expPhase == 2:
        drawCentroids = (drawCentroids + 1) % 2
    elif expPhase == 3:
        drawCentroids = (drawCentroids + 1) % 3
    updateEncodings()
    updateOrderPanel()
    logEvent(source + 'ToggleOrder')


#toggles the labelling overlay between parts, blobs, and off
#source indicates where the command came from (UI button or keyboard) for the purpose of logging
def toggleLabeller(source='button'):
    global markerMode, drawEncodings, expPhase
    #dtouch mode disabled in this version
    # if markerMode == 'dtouch':
    #     drawEncodings = (drawEncodings + 1) % 3
    # else:
    #     drawEncodings = (drawEncodings + 1) % 4
    if expPhase == 1 or expPhase == 2 or expPhase == 3:
        drawEncodings = (drawEncodings + 1) % 3
    updateEncodings()
    updateLabellerPanel()
    logEvent(source + 'ToggleLabeller')


#clears all knowledge of the region adjacency tree
def clearRootAndLevels():
    global mainRoot, globalLevels, levelsMutex
    while not levelsMutex.testandset():
        pass
    mainRoot = None
    globalLevels = [[]]
    levelsMutex.unlock()


#clears the current canvas (reset to white)
def clearCanvas(source='button'):
    global img, markedImg, suggestionTopString, globalLevels, mainRoot
    exit_protect_mode()
    img = np.ones((CANVAS_HEIGHT, CANVAS_WIDTH, 3), np.uint8) * 255
    markedImg = img.copy()
    suggestionTopString = ""
    resetSuggestions()
    clearRootAndLevels()
    updateEncodings()
    addUndoable()
    logEvent(source + 'Clear')


#makes the brush a little bigger, up to a maximum
def growBrush(source='button'):
    global drawRadius
    exit_protect_mode()
    growAmount = 2
    brushMax = 80
    if drawRadius+growAmount <= brushMax:
        drawRadius += growAmount
    else:
        drawRadius = brushMax
    updateBrush()
    logEvent(source + "GrowBrush")


#makes the brush a little smaller, down to a minimum
def shrinkBrush(source='button'):
    global drawRadius
    exit_protect_mode()
    shrinkAmount = 2
    brushMin = 5
    if drawRadius-shrinkAmount >= brushMin:
        drawRadius -= shrinkAmount
    else:
        drawRadius = brushMin
    updateBrush()
    logEvent(source + "ShrinkBrush")


#completely resets (or initializes) the canvas portion of the GUI
def resetGuiImage():
    global canvasPanel

    displayImg = np.ones((CANVAS_HEIGHT, CANVAS_WIDTH, 3), np.uint8) * 255
    displayImg = Image.fromarray(displayImg)
    displayImg = ImageTk.PhotoImage(displayImg)

    if canvasPanel is None:
        canvasPanel = Label(image=displayImg, cursor='tcross')
        canvasPanel.image = displayImg
        canvasPanel.place(x=1, y=1, width=CANVAS_WIDTH, height=CANVAS_HEIGHT)
    else:
        canvasPanel.configure(image=displayImg)
        canvasPanel.image = displayImg


#updates the canvas portion of the GUI to the current canvas
def updateGuiImage():
    global canvasPanel, markedImg, protectImg, drawProtected
    if drawProtected:
        combined = protectImg.copy()
        marked_posns = np.where(markedImg != WHITE)
        combined[marked_posns[0],marked_posns[1]] = markedImg[marked_posns[0],marked_posns[1]]
        displayImg = cv2.cvtColor(combined, cv2.COLOR_BGR2RGB)
    else:
        displayImg = cv2.cvtColor(markedImg, cv2.COLOR_BGR2RGB)
    displayImg = Image.fromarray(displayImg)
    displayImg = ImageTk.PhotoImage(displayImg)
    canvasPanel.configure(image=displayImg)
    canvasPanel.image = displayImg


#updates the brush portion of the GUI to the current canvas
def updateGuiBrush():
    global brushPanel, brush
    displayBrush = Image.fromarray(brush)
    displayBrush = ImageTk.PhotoImage(displayBrush)

    if brushPanel is None:
        brushPanel = Label(image=displayBrush)
        brushPanel.image = displayBrush
        brushPanel.place(x=1260, y=10, width=100, height=100)
    else:
        brushPanel.configure(image=displayBrush)
        brushPanel.image = displayBrush


#sets the brush to a preset colour/size combo
def smallBlackBrush():
    global drawRadius, drawColour
    exit_protect_mode()
    drawRadius = 5
    drawColour = BLACK
    updateBrush()
    logEvent('smallBlackBrush')


#sets the brush to a preset colour/size combo
def medBlackBrush():
    global drawRadius, drawColour
    exit_protect_mode()
    drawRadius = 12
    drawColour = BLACK
    updateBrush()
    logEvent('medBlackBrush')


#sets the brush to a preset colour/size combo
def largeBlackBrush():
    global drawRadius, drawColour
    exit_protect_mode()
    drawRadius = 25
    drawColour = BLACK
    updateBrush()
    logEvent('largeBlackBrush')


#sets the brush to a preset colour/size combo (unused)
def smallGreyBrush():
    global drawRadius, drawColour
    exit_protect_mode()
    drawRadius = 5
    drawColour = GREY
    updateBrush()
    logEvent('smallGreyBush')


#sets the brush to a preset colour/size combo (unused)
def medGreyBrush():
    global drawRadius, drawColour
    exit_protect_mode()
    drawRadius = 12
    drawColour = GREY
    updateBrush()
    logEvent('medGreyBrush')


#sets the brush to a preset colour/size combo (unused)
def largeGreyBrush():
    global drawRadius, drawColour
    exit_protect_mode()
    drawRadius = 25
    drawColour = GREY
    updateBrush()
    logEvent('largeGreyBrush')


#sets the brush to a preset colour/size combo
def smallWhiteBrush():
    global drawRadius, drawColour
    exit_protect_mode()
    drawRadius = 5
    drawColour = WHITE
    updateBrush()
    logEvent('smallWhiteBrush')


#sets the brush to a preset colour/size combo
def medWhiteBrush():
    global drawRadius, drawColour
    exit_protect_mode()
    drawRadius = 12
    drawColour = WHITE
    updateBrush()
    logEvent('medWhiteBrush')


#sets the brush to a preset colour/size combo
def largeWhiteBrush():
    global drawRadius, drawColour
    exit_protect_mode()
    drawRadius = 25
    drawColour = WHITE
    updateBrush()
    logEvent('largeWhiteBrush')


#adds an event to the text log
#events have a name and up to 2 numerical values
def logEvent(eventName, x=-1, y=-1):
    global logFile
    logString = str(datetime.datetime.now()) + ' ' + eventName + ' ' + str(x) + ' ' + str(y) + '\n'
    logFile.write(logString)


#creates a new random target binary string beginning with a 1 and updates target portions of GUI
#numBinDigits - length of the new binary string
def genNewTarget(numBinDigits = -1):
    global targetBinString, targetEncoding

    if numBinDigits == -1:
        numBinDigits = len(targetBinString)
    highVal = int(pow(2,numBinDigits)) - 1
    lowVal = int(pow(2,(numBinDigits-1)))
    newTarget = randint(lowVal,highVal)
    targetBinString = binaryString(newTarget, numBinDigits)

    targetEncoding = binaryStringToDec(targetBinString)[0]
    resetVTGuiElements()

    logEvent('genNewTarget' + str(numBinDigits), newTarget, getModeNum())
    resetTargetDividers()
    resetVTPartNums()
    updateVisualTargetPanel()
    updateEncodings()


#destroys and recreates all target GUI elements (necessary when changing encoding lengths)
def resetVTGuiElements():
    global targetBinString,  vTOffset, expPhase, extraTopLeft, visualTargetPanel, visualTargetDividerPanel,\
        visualTargetDisplayPanels, visualTargetPartNumPanel, visualTargetExtraWordPanel, visualTargetExtraValPanels

    extraTopLeft = (40 + vTWidth * len(targetBinString), 730)

    if visualTargetPanel != None:
        visualTargetPanel.destroy()
        visualTargetDividerPanel.destroy()
        for panel in visualTargetDisplayPanels:
            panel.destroy()
        if expPhase == 3:
            visualTargetPartNumPanel.destroy()
        visualTargetExtraWordPanel.destroy()
        for panel in visualTargetExtraValPanels:
            panel.destroy()

    visualTargetPanel = Label(text=targetBinString, font=visualTargetFont)
    visualTargetPanel.place(x=vTTopLeft[0], y=vTTopLeft[1], width=vTWidth * len(targetBinString), height=20)
    visualTargetDividerPanel = Label(text=targetDividers, font=visualTargetFont)
    visualTargetDividerPanel.place(x=vTTopLeft[0] + 1, y=vTTopLeft[1] + 20, width=vTWidth * len(targetBinString),
                                   height=20)
    visualTargetDisplayPanels = []
    for i in range(len(targetBinString)):
        visualTargetDisplayPanels.append(Label(text=targetBinString[i], font=visualTargetFont, fg=redText))
        visualTargetDisplayPanels[i].place(x=vTTopLeft[0] + vTOffset + vTWidth * i, y=vTTopLeft[1] + 40, width=vTWidth,
                                           height=20)
    if expPhase == 3:
        visualTargetPartNumPanel = Label(text=vtPartNums, font=visualTargetFont, fg=greenText)
        visualTargetPartNumPanel.place(x=vTTopLeft[0], y=vTTopLeft[1] + 60, width=vTWidth * len(targetBinString),
                                       height=20)
    visualTargetExtraWordPanel = Label(text='', font=buttonTextFont, fg=redText, anchor='w')
    visualTargetExtraWordPanel.place(x=extraTopLeft[0], y=extraTopLeft[1], width=extraWidth, height=20)
    visualTargetExtraValPanels = []
    for i in range(int(math.floor(float(extraWidth) / vTWidth))):
        visualTargetExtraValPanels.append(Label(text='', font=visualTargetFont, fg=redText))
        visualTargetExtraValPanels[i].place(x=extraTopLeft[0] + vTWidth * i, y=extraTopLeft[1] + 20, width=vTWidth,
                                            height=20)

    visualTargetPanel.bind("<Button-1>", vTLeftMouseDown)
    visualTargetDividerPanel.bind("<Button-1>", vTLeftMouseDown)


#finds the next file number for files created by the application (works for logs and saved images)
#path - path to the directory of interest
#prefix - naming prefix of the file (usually 'img' or 'log')
#suffix - file type (usually 'png' or 'txt')
def nextFileNum(path, prefix, suffix=''):
    allFiles = os.listdir(path)
    maxExisting = -1

    for fileName in allFiles:
        tokens = fileName.replace('.','_').split('_')
        if tokens[0] == prefix and len(tokens) >= 2:
            fileNum = int(tokens[1])
            if fileNum > maxExisting:
                maxExisting = fileNum

    nextNum = maxExisting + 1
    numString = str(nextNum)
    if nextNum >= 10000:
        print "ERROR: TOO MANY FILES"
        return

    while len(numString) < 4:
        numString = "0" + numString
    nextName = path + '/' + prefix + '_' + numString
    if suffix != '':
        nextName += '.' + suffix
    return (nextNum, nextName)


#end the current log and start a new one in the same session
#minimizes data loss in the event of failure
def startNewLog():
    global logPath, dirPath, logFile
    logFile.close()
    logPath = nextFileNum(dirPath, 'log', 'txt')[1]
    logFile = open(logPath, 'w')


#close the application
def exitApp():
    global tkRoot, appRunning
    logEvent('exit')
    appRunning = False
    tkRoot.destroy()


#updates the GUI element that displays the current encoding scheme
def updateMarkerModePanel():
    global markerModePanel, markerMode, expPhase, blobMode, blobOrderMode
    newText = "Mode: "
    #dtouch not available
    # if markerMode == 'dtouch':
    #     newText += 'dtouch'
    # else:
    #     newText += "Sketch'n'code"
    if expPhase == 1:
        if blobMode == 'number':
            newText += 'Number of blobs'
        elif blobMode == 'convexity':
            newText += 'Convexity of blobs'
        elif blobMode == 'hollow':
            newText +='Hollowness of blobs'
        else:
            newText += 'Convexity/Hollowness'

    elif expPhase == 2:
        if blobMode == 'number':
            newText += 'Number of blobs'
        elif blobMode == 'hollow' and blobOrderMode == 'area':
            newText += 'Hollowness, Area'
        elif blobMode == 'hollow' and blobOrderMode == 'distance':
            newText += 'Hollowness, Dist'
        elif blobMode == 'convexityHollow' and blobOrderMode == 'area':
            newText += 'Dual, Area'
        elif blobMode == 'convexityHollow' and blobOrderMode == 'distance':
            newText += 'Dual, Dist'

    elif expPhase == 3:
        if blobMode == 'number' and partOrderMode == 'area':
            newText += 'Number/Area'
        elif blobMode == 'number' and partOrderMode == 'distance':
            newText += 'Number/Dist'
        elif blobMode == 'hollow' and partOrderMode == 'area':
            newText += 'Hollow/Area/Area'
        elif blobMode == 'hollow' and blobOrderMode == 'area' and partOrderMode == 'distance':
            newText += 'Hollow/Area/Dist'
        elif blobMode == 'hollow' and blobOrderMode == 'distance' and partOrderMode == 'distance':
            newText += 'Hollow/Dist/Dist'
        elif blobMode == 'convexityHollow' and blobOrderMode == 'area' and partOrderMode == 'area':
            newText += 'Dual/Area/Area'
        elif blobMode == 'convexityHollow' and blobOrderMode == 'area' and partOrderMode == 'distance':
            newText += 'Dual/Area/Dist'
        elif blobMode == 'convexityHollow' and blobOrderMode == 'distance' and partOrderMode == 'distance':
            newText += 'Dual/Dist/Dist'
    markerModePanel.configure(text=newText)


#updates the GUI element that displays the state of the labelling overlay
def updateLabellerPanel():
    global labellerPanel, drawEncodings, expPhase

    if expPhase == 1:
        if drawEncodings == 0:
            newText = 'Off'
        elif drawEncodings == 1:
            newText = 'On'
    elif expPhase == 2 or expPhase == 3:
        if drawEncodings == 0:
            newText = 'Off'
        elif drawEncodings == 1:
            newText = 'Part'
        elif drawEncodings == 2:
            newText = 'Blob'
    labellerPanel.configure(text=newText)


#updates the GUI element that displays the state of the ordering overlay
def updateOrderPanel():
    global orderPanel, drawCentroids, markerMode, expPhase
    newText = 'Off'
    if drawCentroids != 0 and expPhase == 2:
        # if markerMode == 'dtouch' or drawCentroids == 2:
        newText = 'Blob'
    elif expPhase == 3:
        if drawCentroids == 1:
            newText = 'Part'
        elif drawCentroids == 2:
            newText = 'Blob'
    orderPanel.configure(text=newText)


#updates the GUI element that displays the state of the ambiguity overlay
def updateAmbPanel():
    global ambPanel, drawAmbToggle
    if drawAmbToggle == 0:
        newText = 'Off'
    else:
        newText = 'On'
    ambPanel.configure(text=newText)


#can be used to initialize target dividers to a non-empty state
#basically unused
#frequency - how often dividers should occur
def getStaticDivider(frequency):
    global expPhase
    dividers = ''

    if expPhase == 1:
        for i in range(len(targetBinString)-1):
            dividers += ' '
    else:
        for i in range(len(targetBinString)-1):
            if (i+1) % frequency == 0:
                dividers += '|'
            else:
                dividers += ' '
    return dividers


#produces a list of numbers to be displayed under the target tracker denoting the value of each division
#should only be used with a Number/X scheme
def dividerNumberDisplayVals():
    global targetBinString, targetDividers
    currString = ''
    outputVals = []
    for i in range(len(targetBinString)):
        currString += targetBinString[i]
        if i == len(targetBinString)-1 or targetDividers[i] == '|':
            if len(currString) == 1 or currString[0] != '0':
                outputVals.append(binaryStringToDec(currString)[0])
            else:
                outputVals.append(-1)
            currString = ''
    return outputVals


#produces a list of binary strings to be converted to images and displayed under the target tracker
# denoting the shape required for each blob
#should be used with Hollow/X, Convexity/X, or Dual/X encoding schemes
#dividerFrequency - number of bits per blob (i.e. 1 for Hollow/X and Convexity/X, 2 for Dual/X)
def dividerOtherDisplayVals(dividerFrequency):
    global targetBinString, targetDividers, expPhase

    outputVals = []
    if expPhase == 1:
        currPosn = len(targetBinString)
        while currPosn - dividerFrequency >= 0:
            outputVals = [binaryStringToDec(targetBinString[(currPosn-dividerFrequency):currPosn])[0]] + outputVals
            currPosn -= dividerFrequency
        numZeroes = dividerFrequency - currPosn

        if numZeroes < dividerFrequency:
            firstVal = targetBinString[:currPosn]
            outputVals = [binaryStringToDec(firstVal)[0]] + outputVals

    elif expPhase == 2 or expPhase == 3:
        currString = ''
        outputVals = []
        for i in range(len(targetBinString)):
            currString += targetBinString[i]
            if i == len(targetBinString) - 1 or targetDividers[i] == '|':
                outputVals.append(currString)
                currString = ''
    return outputVals


#produces a list of booleans, where each is true iff the corresponding entry in displayVals
# is matched in the drawing on the canvas
#also finds pieces of the drawing not corresponding to any displayVals and tags them as extras
#dispayVals - output of either dividerNumberDisplayVals or dividerOtherDisplayVals
def checkTargetEncodingMatch(displayVals):
    global mainRoot, targetExtras, expPhase, blobMode

    valMatches = [False for i in range(len(displayVals))]

    if mainRoot != None:
        encVals = mainRoot.encChunks[:]
    else:
        encVals = []
    for i in range(len(displayVals)):
        val = displayVals[i]
        if expPhase == 1 or expPhase == 2 or expPhase == 3:
            if val in encVals:
                valMatches[i] = True
                encVals.remove(val)
    targetExtras = encVals
    return valMatches


#given code, as a list, produces a list of blob images corresponding to the code
#isGreen - true produces green images; false produces red
#code - a list of the code values you want blob images for
#isArray - true produces images as arrays; false produces ImageTks
def getBlobImgList(isGreen, code, isArray=False):
    global expPhase, blobMode
    blobImgList = []
    workingCode = code[:]

    bitsPerBlob = 1
    if blobMode == 'convexityHollow':
        bitsPerBlob = 2
    while len(workingCode) >= bitsPerBlob:
        blobImgList.append(getBlobImg(isGreen, workingCode[:bitsPerBlob], isArray))
        workingCode = workingCode[bitsPerBlob:]

    return blobImgList


#given the code for a single blob, produces the image associated with that code
#isGreen - true produces green images; false produces red
#code - value of the code you want a blob image for
#isArray - true produces images as arrays; false produces an ImageTk
def getBlobImg(isGreen, code, isArray=False):
    global blobMode, expPhase, greenConvexSolidImg, greenConvexHollowImg, greenConcaveSolidImg, greenConcaveHollowImg, \
        redConvexSolidImg, redConvexHollowImg, redConcaveSolidImg, redConcaveHollowImg, blobIconDict
    currImg = None

    if blobMode == 'convexity':
        if isGreen and (code == '0' or code == 0):
            if isArray:
                currImg = blobIconDict['greenConvexSolid']
            else:
                currImg = greenConvexSolidImg
        elif isGreen:
            if isArray:
                currImg = blobIconDict['greenConcaveSolid']
            else:
                currImg = greenConcaveSolidImg
        elif code == '0' or code == 0:
            if isArray:
                currImg = blobIconDict['redConvexSolid']
            else:
                currImg = redConvexSolidImg
        else:
            if isArray:
                currImg = blobIconDict['redConcaveSolid']
            else:
                currImg = redConcaveSolidImg

    elif blobMode == 'hollow':
        if isGreen and (code == '0' or code == 0):
            if isArray:
                currImg = blobIconDict['greenConvexSolid']
            else:
                currImg = greenConvexSolidImg
        elif isGreen:
            if isArray:
                currImg = blobIconDict['greenConvexHollow']
            else:
                currImg = greenConvexHollowImg
        elif code == '0' or code == 0:
            if isArray:
                currImg = blobIconDict['redConvexSolid']
            else:
                currImg = redConvexSolidImg
        else:
            if isArray:
                currImg = blobIconDict['redConvexHollow']
            else:
                currImg = redConvexHollowImg

    elif blobMode == 'convexityHollow':
        if isGreen and (code == '0' or code == '00' or code == 0):
            if isArray:
                currImg = blobIconDict['greenConvexSolid']
            else:
                currImg = greenConvexSolidImg
        elif isGreen and (code == '1' or code == '01' or code == 1):
            if isArray:
                currImg = blobIconDict['greenConvexHollow']
            else:
                currImg = greenConvexHollowImg
        elif isGreen and (code == '2' or code == '10' or code == 2):
            if isArray:
                currImg = blobIconDict['greenConcaveSolid']
            else:
                currImg = greenConcaveSolidImg
        elif isGreen:
            if isArray:
                currImg = blobIconDict['greenConcaveHollow']
            else:
                currImg = greenConcaveHollowImg
        elif code == '0' or code == '00' or code == 0:
            if isArray:
                currImg = blobIconDict['redConvexSolid']
            else:
                currImg = redConvexSolidImg
        elif code == '1' or code == '01' or code == 1:
            if isArray:
                currImg = blobIconDict['redConvexHollow']
            else:
                currImg = redConvexHollowImg
        elif code == '2' or code == '10' or code == 2:
            if isArray:
                currImg = blobIconDict['redConcaveSolid']
            else:
                currImg = redConcaveSolidImg
        else:
            if isArray:
                currImg = blobIconDict['redConcaveHollow']
            else:
                currImg = redConcaveHollowImg
    else:
        print "ERROR: Unrecognized blobMode in getBlobImg"

    return currImg


#TODO: put this back in drawing. It's here because it needs getBlobImgList
#draw the labeller overlay for pictoral representations (i.e. everything but Number/X schemes)
#levels - region adjacency tree for the image
#displayImage - image to write on
#blobIconDict - dictionary containing blob images
#blobMode - string indicating blob type (e.g. "convexity")
def drawMarkerPartsPictoral(levels, displayImage, blobIconDict, blobMode):
    global drawEncodings
    if len(levels) >= 2:
        levelNum = 1
        if drawEncodings == 2:
            levelNum = 2
        if len(levels) > levelNum:
            for marker in levels[levelNum]:
                binString = binaryString(marker.encoding, marker.bitsRepresented)
                labelPosn = marker.centroid
                blobImgList = getBlobImgList(False, binString, True)

                for i in range(len(blobImgList)):
                    blobImg = blobImgList[i]
                    locs = np.where(blobImg != (240, 240, 240))
                    blobImgHeight = blobImg.shape[0]
                    blobImgWidth = blobImg.shape[1]
                    displayHeight = displayImage.shape[0]
                    displayWidth = displayImage.shape[1]
                    if labelPosn[1] + blobImgHeight < displayHeight and labelPosn[0] + blobImgWidth*(i+1) < displayWidth:
                        displayImage[locs[0] + labelPosn[1], locs[1] + labelPosn[0] + blobImgWidth*i] = blobImg[locs[0], locs[1]]
                # cv2.circle(displayImage,centroid,2,(255,0,0),-1)
                # cv2.putText(displayImage, binString, centroid, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)


#calculate where to put numbers in the target tracker based on divider locations
#also figure out if they should be displayed in green or red based on matches in the image
#should only be used with Number/X encoding schemes
#displayVals - list of numeric values to display
#valMatches - list of Booleans indicating which of the corresponding values in displayVals are matched in the image
def calcNumberVTDisplayPanels(displayVals, valMatches):
    global targetDividers, mainRoot
    panelVals = []
    panelColours = []
    distanceToDivider = getDividerDist()

    currBottom = 0
    for i in range(len(displayVals)):
        currVal = str(displayVals[i])
        currMatch = valMatches[i]
        if currVal == '-1':
            currVal = 'X'

        startPosn = currBottom + int(math.floor(((distanceToDivider[i] - len(currVal)) / 2.0)))
        for j in range(currBottom, currBottom+distanceToDivider[i]):
            if j >= startPosn and j < startPosn + len(currVal):
                panelVals.append(currVal[j-startPosn])
            else:
                panelVals.append('')

            if currMatch:
                panelColours.append(greenText)
            else:
                panelColours.append(redText)

        currBottom += distanceToDivider[i]

    return panelVals, panelColours


#assign blob images of the correct colour to the display panels
#should NOT be used with Number/X encoding schemes
#displayVals - list of numeric values to display
#valMatches - list of Booleans indicating which of the corresponding values in displayVals are matched in the image
def calcOtherVTDisplayPanels(displayVals, valMatches):
    global targetDividers, mainRoot, expPhase, blobMode, partOrderMode
    panelVals = []
    dividerFrequency = 1
    if blobMode == 'convexityHollow':
        dividerFrequency = 2

    if expPhase == 1:
        for i in range(len(displayVals)):
            currVal = str(displayVals[i])
            currMatch = valMatches[i]
            currImg = getBlobImg(currMatch, currVal)
            panelVals.append(currImg)
            for j in range(dividerFrequency-1):
                panelVals.append('')

    elif expPhase == 2 or expPhase == 3:
        for i in range(len(displayVals)):
            currVal = str(displayVals[i])
            currMatch = valMatches[i]
            currImgList = getBlobImgList(currMatch, currVal)
            for currImg in currImgList:
                panelVals.append(currImg)
                for j in range(dividerFrequency-1):
                    panelVals.append('')

    return panelVals


#updates the Extra part of the target tracker with appropriate visuals
def updateVTExtraPanels():
    global targetExtras, visualTargetExtraValPanels, expPhase, blobMode, ellipsisImg
    numSlots = len(visualTargetExtraValPanels)

    if expPhase == 1 or ((expPhase == 2 or expPhase == 3) and blobMode == 'number'):
        finished = False
        addEllipsis = False

        if blobMode == 'number':
            displayString = ''
            if len(targetExtras) > 0:
                i = 0
                currAddition = str(targetExtras[i])
                if len(currAddition) > numSlots or (len(currAddition)+1 > numSlots and i >= len(targetExtras)-1):
                    addEllipsis = True
                    finished = True
                else:
                    displayString += currAddition
                    i += 1

                while i < len(targetExtras) and not finished:
                    currAddition = ',' + str(targetExtras[i])
                    if len(displayString) + len(currAddition) > numSlots or \
                            (len(displayString) + len(currAddition) + 1 > numSlots and i <= len(targetExtras) - 1):
                        addEllipsis = True
                        finished = True
                    else:
                        displayString += currAddition
                    i += 1

            for i in range(numSlots):
                if i < len(displayString):
                    visualTargetExtraValPanels[i].configure(text=displayString[i], image='')
                else:
                    visualTargetExtraValPanels[i].configure(text='', image='')

            if addEllipsis:
                ellipsisPosn = len(displayString)
                visualTargetExtraValPanels[ellipsisPosn].configure(text='', image=ellipsisImg)
        else:
            displayList = []
            if len(targetExtras) > 0:
                i = 0
                currAddition = targetExtras[i]
                if 1 > numSlots or (2 > numSlots and i >= len(targetExtras) - 1):
                    addEllipsis = True
                    finished = True
                else:
                    displayList.append(getBlobImg(False, currAddition))
                    i += 1

                while i < len(targetExtras) and not finished:
                    currAddition = targetExtras[i]
                    if len(displayList) + 1 > numSlots or (len(displayList) + 2 > numSlots and i <= len(targetExtras) - 1):
                        addEllipsis = True
                        finished = True
                    else:
                        displayList.append(getBlobImg(False, currAddition))
                    i += 1

            for i in range(numSlots):
                if i < len(displayList):
                    visualTargetExtraValPanels[i].configure(text='', image=displayList[i])
                else:
                    visualTargetExtraValPanels[i].configure(text='', image='')

            if addEllipsis:
                ellipsisPosn = len(displayList)
                visualTargetExtraValPanels[ellipsisPosn].configure(text='', image=ellipsisImg)

    elif expPhase == 2 or expPhase == 3:
        finished = False
        addEllipsis = False

        displayList = []
        if len(targetExtras) > 0:
            i = 0
            currAddition = targetExtras[i]
            lengthDivider = 1
            if blobMode == 'convexityHollow':
                lengthDivider = 2

            if len(currAddition)/lengthDivider > numSlots or (len(currAddition)/lengthDivider + 1 > numSlots and i >= len(targetExtras) - 1):
                addEllipsis = True
                finished = True
            else:
                blobImgList = getBlobImgList(False, currAddition)
                for blobImg in blobImgList:
                    displayList.append(blobImg)
                i += 1

            while i < len(targetExtras) and not finished:
                currAddition = targetExtras[i]
                if len(displayList) + len(currAddition)/lengthDivider + 1 > numSlots or \
                        (len(displayList) + len(currAddition)/lengthDivider + 2 > numSlots and i <= len(targetExtras) - 1):
                    addEllipsis = True
                    finished = True
                else:
                    blobImgList = getBlobImgList(False, currAddition)
                    displayList.append(',')
                    for blobImg in blobImgList:
                        displayList.append(blobImg)
                i += 1

        for i in range(numSlots):
            if i < len(displayList):
                if displayList[i] == ',':
                    visualTargetExtraValPanels[i].configure(text=displayList[i], image='')
                else:
                    visualTargetExtraValPanels[i].configure(text='', image=displayList[i])
            else:
                visualTargetExtraValPanels[i].configure(text='', image='')

        if addEllipsis:
            ellipsisPosn = len(displayList)
            visualTargetExtraValPanels[ellipsisPosn].configure(text='', image=ellipsisImg)


#produces the list of distances (number of spaces) between dividers
def getDividerDist():
    global targetDividers
    distanceToDivider = []
    currDist = 0
    for i in range(len(targetDividers) + 1):
        currDist += 1
        if i >= len(targetDividers) or targetDividers[i] == '|':
            distanceToDivider.append(currDist)
            currDist = 0
    return distanceToDivider


#determines how numbers should be displayed in the target tracker, including colour
#should only be used with Number/X schemes
#displayVals - list of numeric values to display
#valMatches - list of Booleans indicating which of the corresponding values in displayVals are matched in the image
def calcVTPartNums(displayVals, valMatches):
    global vtPartNums, targetDividers, mainRoot, expPhase, partOrderMode, blobMode

    vtPartNums = ''
    textColour = greenText
    if expPhase == 3 and mainRoot != None:
        sortedChildren = sortParts(mainRoot, partOrderMode)
        partTaken = [False for i in range(len(sortedChildren))]
        nums = [-1 for i in range(len(valMatches))]
        for i in range(len(valMatches)):
            if valMatches[i]:
                for j in range(len(sortedChildren)):
                    if blobMode == 'number':
                        childEncoding = sortedChildren[j].encoding
                    else:
                        childEncoding = binaryString(sortedChildren[j].encoding, sortedChildren[j].bitsRepresented)
                    if not partTaken[j] and childEncoding == displayVals[i]:
                        partTaken[j] = True
                        nums[i] = j + 1
                        break

        largestNum = -1
        for i in range(len(nums)):
            num = nums[i]
            if num != -1 and num < largestNum:
                textColour = redText
                break
            else:
                if num != -1:
                    largestNum = num

        distanceToDivider = getDividerDist()
        currBottom = 0
        for i in range(len(nums)):
            currVal = str(nums[i])
            if currVal == '-1':
                currVal = ' '
            if len(currVal) > 1 and distanceToDivider[i] <= 1:
                currVal = chr(ord('a')+int(currVal)-10)
            startPosn = currBottom + int(math.floor(((distanceToDivider[i] - len(currVal)) / 2.0)))
            for j in range(currBottom, currBottom + distanceToDivider[i]):
                if j >= startPosn and j < startPosn + len(currVal):
                    vtPartNums += currVal[j - startPosn]
                else:
                    vtPartNums += ' '
            currBottom += distanceToDivider[i]

    return textColour


#recalculate and update the display of the target tracker
def updateVisualTargetPanel():
    global visualTargetPanel, visualTargetDividerPanel, visualTargetDisplayPanels, \
        expPhase, blobMode, targetBinString, targetDividers, staticDividers, targetExtras, \
        vtPartNums, visualTargetPartNumPanel

    if blobMode == 'number':
        displayVals = dividerNumberDisplayVals()
        valMatches = checkTargetEncodingMatch(displayVals)
    else:
        dividerFrequency = 1
        if blobMode == 'convexityHollow':
            dividerFrequency = 2
        displayVals = dividerOtherDisplayVals(dividerFrequency)
        valMatches = checkTargetEncodingMatch(displayVals)

    if expPhase == 1:
        if blobMode == 'number':
            visualTargetPanel.configure(text=targetBinString)
            visualTargetDividerPanel.configure(text=targetDividers)
            panelVals, panelColours = calcNumberVTDisplayPanels(displayVals, valMatches)
            for i in range(len(visualTargetDisplayPanels)):
                visualTargetDisplayPanels[i].configure(text=panelVals[i], fg=panelColours[i], image='')
        else:
            visualTargetPanel.configure(text=targetBinString)
            if blobMode == 'convexity' or blobMode == 'hollow':
                visualTargetDividerPanel.configure(text=staticDividers[0])
            else:
                visualTargetDividerPanel.configure(text=staticDividers[1])
            panelVals = calcOtherVTDisplayPanels(displayVals, valMatches)
            for i in range(len(visualTargetDisplayPanels)):
                visualTargetDisplayPanels[i].configure(image=panelVals[i], text='')

        if len(targetExtras) > 0:
            visualTargetExtraWordPanel.configure(text='Extra:')
        else:
            visualTargetExtraWordPanel.configure(text='')
        updateVTExtraPanels()

    elif expPhase == 2 or expPhase == 3:
        if blobMode == 'number':
            visualTargetPanel.configure(text=targetBinString)
            visualTargetDividerPanel.configure(text=targetDividers)
            panelVals, panelColours = calcNumberVTDisplayPanels(displayVals, valMatches)
            for i in range(len(visualTargetDisplayPanels)):
                visualTargetDisplayPanels[i].configure(text=panelVals[i], fg=panelColours[i], image='')
        else:
            visualTargetPanel.configure(text=targetBinString)
            visualTargetDividerPanel.configure(text=targetDividers)
            panelVals = calcOtherVTDisplayPanels(displayVals, valMatches)
            for i in range(len(visualTargetDisplayPanels)):
                visualTargetDisplayPanels[i].configure(image=panelVals[i], text='')

        if expPhase == 3:
            partNumColour = calcVTPartNums(displayVals, valMatches)
            visualTargetPartNumPanel.configure(text=vtPartNums, fg=partNumColour)

        if len(targetExtras) > 0:
            visualTargetExtraWordPanel.configure(text='Extra:')
        else:
            visualTargetExtraWordPanel.configure(text='')
        updateVTExtraPanels()


#handle clicks in the target tracker area (set or remove dividers)
#event - the mouse click event
def vTLeftMouseDown(event):
    global targetDividers, vTOffset, vTWidth, expPhase, blobMode
    logEvent('vTLeftMouseDown', event.x, event.y)
    if (expPhase == 1 and blobMode == 'number') or expPhase == 2 or expPhase == 3:
        minX = vTOffset + int(math.ceil(vTWidth/2.0))
        maxX = minX + vTWidth*len(targetDividers)
        if event.x >= minX and event.x < maxX:
            posn = int(math.floor((event.x - minX) / float(vTWidth)))

            if (expPhase == 2 or expPhase == 3) and blobMode == 'convexityHollow' and posn % 2 == 0:
                posn += 1

            newChar = ' '
            if posn < len(targetDividers):
                if targetDividers[posn] == ' ':
                    newChar = '|'
                targetDividers = targetDividers[:posn] + newChar + targetDividers[(posn+1):]
                logEvent('vTDividerToggle', posn)
                updateVisualTargetPanel()


#remove all target dividers
def resetTargetDividers():
    global targetDividers
    targetDividers = ''
    for i in range(len(targetBinString) - 1):
        targetDividers += ' '


#reset the numeric display values of the target tracker
def resetVTPartNums():
    global vtPartNums
    vtPartNums = ''
    for i in range(len(targetBinString)):
        vtPartNums += ' '


#unused function intended for threading
def updateEncodingThread():
    global appRunning
    while appRunning:
        updateEncodingsForReal()


#unused class intended for threading
class UpdateThread (threading.Thread):
    def __init__(self, threadID):
        threading.Thread.__init__(self)
        self.threadID = threadID
    def run(self):
        global appRunning
        while appRunning:
            determineMainRoot()
            updateEncodingsForReal()


#check the encoding given by command line arguments
#print an error if the encoding is invalid
def checkCommandLineEncoding():
    global targetBinString

    if len(sys.argv) == 1:
        pass
    elif len(sys.argv) == 2:
        if validBase2String(str(sys.argv[1])):
            targetBinString = str(sys.argv[1])
        else:
            print "ERROR: Invalid base 2 string"
    elif len(sys.argv) == 3:
        if str(sys.argv[1]) == '-2':
            if validBase2String(str(sys.argv[2])):
                targetBinString = str(sys.argv[2])
            else:
                print "ERROR: Invalid base 2 string"
        elif str(sys.argv[1]) == '-10':
            if validBase10String(str(sys.argv[2])):
                targetBinString = binaryString(int(sys.argv[2]))
            else:
                print "ERROR: Invalid base 10 string"
        elif str(sys.argv[1]) == '-36':
            if validBase36String(str(sys.argv[2])):
                targetBinString = binaryString(base36StringToDec(str(sys.argv[2]))[0])
            else:
                print "ERROR: Invalid base 36 string"
    else:
        print "ERROR: Unrecognized command line arguments"


#initialize everything, run tkRoot.mainloop, and exit cleanly when finished
if __name__ == "__main__":
    #initialize globals
    resetVars()
    checkCommandLineEncoding()
    img = np.ones((CANVAS_HEIGHT, CANVAS_WIDTH, 3), np.uint8) * 255 #the canvas
    protectImg = img.copy() #only contains colour for protected parts
    markedImg = img.copy() #the canvas with tool overlays
    suggestionImg = np.ones((CANVAS_HEIGHT, CANVAS_WIDTH, 3), np.uint8) * 255
    suggestionLocs = np.where(suggestionImg != WHITE)
    mainRoot = None
    globalLevels = [[]]
    oldEncoding = -1
    oldPartNum = -1
    oldEncodingNum = -1
    suggestionTopString = ""
    brush = np.ones((100, 100, 3), np.uint8) * 255
    undoStack = []
    targetDividers = ''
    vtPartNums = ''
    resetVTPartNums()
    resetTargetDividers()
    staticDividers = [getStaticDivider(1), getStaticDivider(2)]
    # for i in range(NUM_UNDO_STATES):
    #     undoStack.append(np.ones((CANVAS_HEIGHT, CANVAS_WIDTH, 3), np.uint8) * 255)
    undoIndex = 0
    addUndoable()
    # cv2.namedWindow('Canvas')
    # cv2.setMouseCallback('Canvas', drawCanvas)
    # cv2.namedWindow('Brush')
    timer = 0
    waitAmount = 10
    appRunning = True
    levelsMutex = mutex.mutex()
    drawProtected = False

    ellipsisImg = cv2.imread('ellipsis.png')
    ellipsisImg = Image.fromarray(ellipsisImg)
    ellipsisImg = ImageTk.PhotoImage(ellipsisImg)

    #create tk images for all the blob icons
    blobIconDict = {}

    greenConvexSolidImg = cv2.imread('greenConvexSolid.png')
    blobIconDict['greenConvexSolid'] = greenConvexSolidImg.copy()
    greenConvexSolidImg = cv2.cvtColor(greenConvexSolidImg, cv2.COLOR_RGB2BGR)
    greenConvexSolidImg = Image.fromarray(greenConvexSolidImg)
    greenConvexSolidImg = ImageTk.PhotoImage(greenConvexSolidImg)

    greenConvexHollowImg = cv2.imread('greenConvexHollow.png')
    blobIconDict['greenConvexHollow'] = greenConvexHollowImg.copy()
    greenConvexHollowImg = cv2.cvtColor(greenConvexHollowImg, cv2.COLOR_RGB2BGR)
    greenConvexHollowImg = Image.fromarray(greenConvexHollowImg)
    greenConvexHollowImg = ImageTk.PhotoImage(greenConvexHollowImg)

    greenConcaveSolidImg = cv2.imread('greenConcaveSolid.png')
    blobIconDict['greenConcaveSolid'] = greenConcaveSolidImg.copy()
    greenConcaveSolidImg = cv2.cvtColor(greenConcaveSolidImg, cv2.COLOR_RGB2BGR)
    greenConcaveSolidImg = Image.fromarray(greenConcaveSolidImg)
    greenConcaveSolidImg = ImageTk.PhotoImage(greenConcaveSolidImg)

    greenConcaveHollowImg = cv2.imread('greenConcaveHollow.png')
    blobIconDict['greenConcaveHollow'] = greenConcaveHollowImg.copy()
    greenConcaveHollowImg = cv2.cvtColor(greenConcaveHollowImg, cv2.COLOR_RGB2BGR)
    greenConcaveHollowImg = Image.fromarray(greenConcaveHollowImg)
    greenConcaveHollowImg = ImageTk.PhotoImage(greenConcaveHollowImg)

    redConvexSolidImg = cv2.imread('redConvexSolid.png')
    blobIconDict['redConvexSolid'] = redConvexSolidImg.copy()
    redConvexSolidImg = cv2.cvtColor(redConvexSolidImg, cv2.COLOR_RGB2BGR)
    redConvexSolidImg = Image.fromarray(redConvexSolidImg)
    redConvexSolidImg = ImageTk.PhotoImage(redConvexSolidImg)

    redConvexHollowImg = cv2.imread('redConvexHollow.png')
    blobIconDict['redConvexHollow'] = redConvexHollowImg.copy()
    redConvexHollowImg = cv2.cvtColor(redConvexHollowImg, cv2.COLOR_RGB2BGR)
    redConvexHollowImg = Image.fromarray(redConvexHollowImg)
    redConvexHollowImg = ImageTk.PhotoImage(redConvexHollowImg)

    redConcaveSolidImg = cv2.imread('redConcaveSolid.png')
    blobIconDict['redConcaveSolid'] = redConcaveSolidImg.copy()
    redConcaveSolidImg = cv2.cvtColor(redConcaveSolidImg, cv2.COLOR_RGB2BGR)
    redConcaveSolidImg = Image.fromarray(redConcaveSolidImg)
    redConcaveSolidImg = ImageTk.PhotoImage(redConcaveSolidImg)

    redConcaveHollowImg = cv2.imread('redConcaveHollow.png')
    blobIconDict['redConcaveHollow'] = redConcaveHollowImg.copy()
    redConcaveHollowImg = cv2.cvtColor(redConcaveHollowImg, cv2.COLOR_RGB2BGR)
    redConcaveHollowImg = Image.fromarray(redConcaveHollowImg)
    redConcaveHollowImg = ImageTk.PhotoImage(redConcaveHollowImg)

    # blobIconDict['convexSolidMask'] = np.where(blobIconDict['greenConvexSolid'] != WHITE)
    # print blobIconDict['convexSolidMask']
    # print type(blobIconDict['convexSolidMask'])
    # while True:
    #     pass
    # cv2.imshow('Mask', np.array(blobIconDict['convexSolidMask']))
    # locs = np.where(blobIconDict['redConcaveHollow'] != (240,240,240))

    #setup the application window
    tkRoot.geometry("1600x800") #+30+30
    canvasPanel = None
    brushPanel = None
    updateBrush()
    resetGuiImage()

    allDirFiles = os.listdir(BASE_PATH)
    if 'sessions' not in allDirFiles:
        os.makedirs(SESSION_PATH)
    dirPath = nextFileNum(SESSION_PATH, 'session')[1]
    os.makedirs(dirPath)
    logPath = nextFileNum(dirPath, 'log','txt')[1]
    logFile = open(logPath, 'w')
    imgPath = ''

    brushMinusBtn = Button(tkRoot, text="-", font=plusMinusFont, command=shrinkBrush)
    brushMinusBtn.place(x=1370, y=35, width=50, height=50)
    brushPlusBtn = Button(tkRoot, text="+", font=plusMinusFont, command=growBrush)
    brushPlusBtn.place(x=1430, y=35, width=50, height=50)

    smallBlackBrushIcon = np.ones((49, 49, 3), np.uint8) * 255
    cv2.circle(smallBlackBrushIcon, (24, 24), 3, BLACK, -1)
    smallBlackBrushIcon = Image.fromarray(smallBlackBrushIcon)
    smallBlackBrushIcon = ImageTk.PhotoImage(smallBlackBrushIcon)
    smallBlackBtn = Button(tkRoot, image=smallBlackBrushIcon, command=smallBlackBrush)
    smallBlackBtn.place(x=1285, y=120, width=50, height=50)
    medBlackBrushIcon = np.ones((49, 49, 3), np.uint8) * 255
    cv2.circle(medBlackBrushIcon, (24, 24), 8, BLACK, -1)
    medBlackBrushIcon = Image.fromarray(medBlackBrushIcon)
    medBlackBrushIcon = ImageTk.PhotoImage(medBlackBrushIcon)
    medBlackBtn = Button(tkRoot, image=medBlackBrushIcon, command=medBlackBrush)
    medBlackBtn.place(x=1345, y=120, width=50, height=50)
    largeBlackBrushIcon = np.ones((49, 49, 3), np.uint8) * 255
    cv2.circle(largeBlackBrushIcon, (24, 24), 12, BLACK, -1)
    largeBlackBrushIcon = Image.fromarray(largeBlackBrushIcon)
    largeBlackBrushIcon = ImageTk.PhotoImage(largeBlackBrushIcon)
    largeBlackBtn = Button(tkRoot, image=largeBlackBrushIcon, command=largeBlackBrush)
    largeBlackBtn.place(x=1405, y=120, width=50, height=50)

    # smallGreyBrushIcon = np.ones((49, 49, 3), np.uint8) * 255
    # cv2.circle(smallGreyBrushIcon, (24, 24), 3, GREY, -1)
    # smallGreyBrushIcon = Image.fromarray(smallGreyBrushIcon)
    # smallGreyBrushIcon = ImageTk.PhotoImage(smallGreyBrushIcon)
    # smallGreyBtn = Button(tkRoot, image=smallGreyBrushIcon, command=smallGreyBrush)
    # smallGreyBtn.place(x=1325, y=180, width=50, height=50)
    # medGreyBrushIcon = np.ones((49, 49, 3), np.uint8) * 255
    # cv2.circle(medGreyBrushIcon, (24, 24), 8, GREY, -1)
    # medGreyBrushIcon = Image.fromarray(medGreyBrushIcon)
    # medGreyBrushIcon = ImageTk.PhotoImage(medGreyBrushIcon)
    # medGreyBtn = Button(tkRoot, image=medGreyBrushIcon, command=medGreyBrush)
    # medGreyBtn.place(x=1385, y=180, width=50, height=50)
    # largeGreyBrushIcon = np.ones((49, 49, 3), np.uint8) * 255
    # cv2.circle(largeGreyBrushIcon, (24, 24), 12, GREY, -1)
    # largeGreyBrushIcon = Image.fromarray(largeGreyBrushIcon)
    # largeGreyBrushIcon = ImageTk.PhotoImage(largeGreyBrushIcon)
    # largeGreyBtn = Button(tkRoot, image=largeGreyBrushIcon, command=largeGreyBrush)
    # largeGreyBtn.place(x=1445, y=180, width=50, height=50)

    smallWhiteBrushIcon = np.ones((49, 49, 3), np.uint8) * 255
    cv2.circle(smallWhiteBrushIcon, (24, 24), 3, BLACK, 1)
    smallWhiteBrushIcon = Image.fromarray(smallWhiteBrushIcon)
    smallWhiteBrushIcon = ImageTk.PhotoImage(smallWhiteBrushIcon)
    smallWhiteBtn = Button(tkRoot, image=smallWhiteBrushIcon, command=smallWhiteBrush)
    smallWhiteBtn.place(x=1285, y=180, width=50, height=50)
    medWhiteBrushIcon = np.ones((49, 49, 3), np.uint8) * 255
    cv2.circle(medWhiteBrushIcon, (24, 24), 8, BLACK, 1)
    medWhiteBrushIcon = Image.fromarray(medWhiteBrushIcon)
    medWhiteBrushIcon = ImageTk.PhotoImage(medWhiteBrushIcon)
    medWhiteBtn = Button(tkRoot, image=medWhiteBrushIcon, command=medWhiteBrush)
    medWhiteBtn.place(x=1345, y=180, width=50, height=50)
    largeWhiteBrushIcon = np.ones((49, 49, 3), np.uint8) * 255
    cv2.circle(largeWhiteBrushIcon, (24, 24), 12, BLACK, 1)
    largeWhiteBrushIcon = Image.fromarray(largeWhiteBrushIcon)
    largeWhiteBrushIcon = ImageTk.PhotoImage(largeWhiteBrushIcon)
    largeWhiteBtn = Button(tkRoot, image=largeWhiteBrushIcon, command=largeWhiteBrush)
    largeWhiteBtn.place(x=1405, y=180, width=50, height=50)

    undoBtn = Button(tkRoot, text="Undo", font=buttonTextFont, command=undo)
    undoBtn.place(x=1285, y=240, width=50, height=50)
    redoBtn = Button(tkRoot, text="Redo", font=buttonTextFont, command=redo)
    redoBtn.place(x=1345, y=240, width=50, height=50)
    clearBtn = Button(tkRoot, text="Clear", font=buttonTextFont, command=clearCanvas)
    clearBtn.place(x=1405, y=240, width=50, height=50)

    ########## Rahul's code ###############
    incBtn = Button(tkRoot, text="Inc", font=buttonTextFont, command=increase_blob)
    incBtn.place(x=1285, y=300, width=50, height=50)

    decBtn = Button(tkRoot, text="Dec", font=buttonTextFont, command=join_blob_to_edge)
    decBtn.place(x=1345, y=300, width=50, height=50)

    redprtBtn = Button(tkRoot, text="RedPart", font=buttonTextFont, command=reduce_part)
    redprtBtn.place(x=1285, y=360, width=50, height=50)

    #and also some not Rahul's code
    fixBlobBtn = Button(tkRoot, text="Fix", font=buttonTextFont, command=auto_fix_blobs_btn)
    fixBlobBtn.place(x=1285, y=420, width=50, height=50)

    protectBtn = Button(tkRoot, text="Prot.", font=buttonTextFont, command=protect_btn)
    protectBtn.place(x=1345, y=420, width=50, height=50)

    addRemovePrefScale = Scale(tkRoot, from_=-20, to=20, orient=HORIZONTAL, label='Prefer Removing or Adding Blobs')
    addRemovePrefScale.place(x=1270, y=480, width=200)
    ambPanel = Label(text="Removing           Neutral              Adding", font=sliderFont)
    ambPanel.place(x=1250, y=540, width=240, height=20)

    ######################################
    visualTargetPanel = None
    resetVTGuiElements()
    updateVisualTargetPanel()

    markerModePanel = Label(text="Mode: Sketch'n'code", font=buttonTextFont, anchor='w')
    markerModePanel.place(x=1260, y=650, width=200, height=40)
    updateMarkerModePanel()

    labellerPanel = Label(text="Off", font=buttonTextFont)
    labellerPanel.place(x=1285, y=695, width=50, height=30)
    updateLabellerPanel()

    orderPanel = Label(text="Off", font=buttonTextFont)
    orderPanel.place(x=1345, y=695, width=50, height=30)
    updateOrderPanel()

    ambPanel = Label(text="Off", font=buttonTextFont)
    ambPanel.place(x=1405, y=695, width=50, height=30)
    updateAmbPanel()

    labellerBtn = Button(tkRoot, text="Label", font=buttonTextFont, command=toggleLabeller, bg="red")
    labellerBtn.place(x=1285, y=730, width=50, height=50)
    orderingBtn = Button(tkRoot, text="Order", font=buttonTextFont, command=toggleOrder, bg="cyan")
    orderingBtn.place(x=1345, y=730, width=50, height=50)
    ambBtn = Button(tkRoot, text="Ambig", font=buttonTextFont, command=toggleAmb, bg="orange")
    ambBtn.place(x=1405, y=730, width=50, height=50)

    #set event handlers
    canvasPanel.bind("<Button-1>", leftMouseDown)
    canvasPanel.bind("<ButtonRelease-1>", leftMouseUp)
    canvasPanel.bind("<B1-Motion>", leftMouseMove)
    visualTargetPanel.bind("<Button-1>", vTLeftMouseDown)
    visualTargetDividerPanel.bind("<Button-1>", vTLeftMouseDown)
    tkRoot.bind("<Key>", keyPress)

    tkRoot.protocol("WM_DELETE_WINDOW", exitApp)

    #unused threading stuff
    if usingThreading:
        updateThread = UpdateThread('update')
        updateThread.start()

    #run the application
    tkRoot.mainloop()

    if usingThreading:
        updateThread.join()

    #exit everything properly
    logFile.close()
    cv2.destroyAllWindows()