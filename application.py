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
import heapq

from Tkinter import *
from PIL import Image
from PIL import ImageTk
from helpers import imshow
from conversions import *
from detector import *
from drawing import *
from random import randint
from part_division import *
from collections import deque

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
DARK_YELLOW = (0,204,204)
GREEN = (50,205,50)
RED = (0,0,255)
DARK_RED = (34,34,178)
ORANGE = (0, 165, 255)
PART_CUT_WIDTH = 3
# SUGGEST_NODES = 200
SHORT_SEARCH = 0.1
LONG_SEARCH = 2.0
EXTRA_CUT_LENGTH = 7

#global variables
targetBinString = '100101011'#'110000111010110110101011100011011010' #'11001110111000001011101001010110001'#'11001101'#'1110010110110011001110101101101111' #Put your target encoding here!

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
suggestMode = 0
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
suggestToggle = 0
suggestionIndex = 0
drawTargetToggle = 0
drawContoursToggle = 0


#reset global variables to initial values
def resetVars():
    global mode, drawColour, drawRadius, suggestions, targetEncoding, drawEncodings, drawCentroids, \
        drawAmbToggle, suggestionIndex, suggestionTopString, suggestToggle, protected_centroids

    mode = 'idle'
    drawColour = (0, 0, 0)
    drawRadius = 10
    suggestions = []
    drawEncodings = 0
    drawCentroids = 0
    drawAmbToggle = 0
    suggestToggle = 0
    suggestionIndex = 0
    suggestionTopString = ""
    protected_centroids = []


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

def satisfy_check(level,x,y,radius):
    global img
    for child in level.children:
        if not out_contour(x ,y , child.contour,radius):
            print("Failed in satisfy_check")
            # cv2.circle(img,(x,y),1,(255,0,0),-1)
            return False

    return True

def out_contour(x, y, contour,radius,radius_multiplier=3):
    global drawRadius
    ret = cv2.pointPolygonTest(contour, (y, x), True)
    if ret > -(radius_multiplier*radius):
        return False

    return True

def in_contour( x, y, contour,radius, radius_multiplier=3):
    ret = cv2.pointPolygonTest(contour, (x, y), True)
    if ret < (radius_multiplier*radius):
        # print("Failed in in_contour")
        return False

    return True

def add_blob(part):
    global img,drawRadius,drawColour,recent_auto_changes
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
    max_count = 200

    while count < max_count:
        sampled_x = int(np.random.uniform(range_in_x[0],range_in_x[1],1))
        sampled_y = int(np.random.uniform(range_in_y[0],range_in_y[1],1))

        if satisfy_check(part,sampled_x,sampled_y,radius) and in_contour(sampled_y,sampled_x,part.contour,radius):
            print("Drawing on %d %d" % (sampled_x,sampled_y))
            cv2.circle(img, (sampled_y, sampled_x), radius, colour, -1)
            recent_auto_changes.append(('add_circle_blob', (sampled_y, sampled_x), radius))
            updateEncodings()
            return True
        count += 1
        # print(sampled_x,sampled_y,"No")
        if count >= max_count:
            print "ERROR: No valid location found for blob placement"
            return False

    return False

def increase_blob(source='button'):
    global undoStack, undoIndex, img, globalLevels
    exit_protect_mode()
    exit_select_mode()
    print(globalLevels)
    for part in globalLevels[1]:
        add_blob(part)
    updateEncodings()
    logEvent(source + 'increase')

#########################################


####### Code for Deleting a blob #######

def delete_blob(blob):
    global img, recent_auto_changes
    cv2.fillPoly(img, pts =[blob.contour], color=(255,255,255))
    recent_auto_changes.append(('delete_blob', blob.contour))
    updateEncodings()

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
    exit_select_mode()
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

def join_2_points(p1, p2, thickness=2):
    global img, recent_auto_changes
    cv2.line(img,(p1[0][0],p1[0][1]),(p2[0][0],p2[0][1]),(0,0,0),thickness)
    updateEncodings()


def join_blobs(source='button'):
    global img,globalLevels, recent_auto_changes
    # exit_protect_mode()
    # exit_select_mode()

    for level in globalLevels[1]:
        if len(level.children) > 1:
            pairs,_ = closest_pair_of_blobs_points(level.children)
            join_2_points(*pairs)
            # blob_with_min_area = min(level.children,key = lambda x: x.area)

###### Join a Blob to the nearest edge or blob #####
def join_blob_and_edge(level,sorted_parts):
    global index
    wanted_pair = None
    min_dist = None
    description = ""
    curr_blob = None
    if len(level.children) == 1 and len(level.children[0].children) > 0:
        delete_blob(level.children[0])
        return
    if index > 0:
        previous_area = sorted_parts[index - 1].area
    else:
        previous_area = 0
    for blob in level.children:
        if len(blob.children) > 0:
            continue
        pairs,dist = closest_pair_of_points_between_blobs(blob,level)
        if min_dist is None:
            min_dist = dist
            wanted_pair = pairs
            description = "join_to_edge"
            curr_blob = blob
        elif dist < min_dist:
            min_dist = dist
            wanted_pair = pairs
            curr_blob = blob
            description = "join_to_edge"
    if min_dist is not None:
        if level.area - (3*min_dist + curr_blob.area) <= previous_area: #2 is the thickness of the line
            min_dist = None
            wanted_pair = None
    if level.children > 1:
        for combo in itertools.combinations(level.children,2):
            pairs,dist = closest_pair_of_points_between_blobs(*combo)
            if min_dist is None:
                min_dist = dist
                wanted_pair = pairs
                description = "join_blobs"
            elif dist < min_dist:
                min_dist = dist
                wanted_pair = pairs
                description = "join_blobs"
    if not determine_adjacent(wanted_pair[0][0],wanted_pair[1][0]):
        delete_blob(level.children[0])
        return
    if wanted_pair is None and len(level.children)  == 1:
        delete_blob(level.children[0])
    else:
        join_2_points(wanted_pair[0], wanted_pair[1], 2)
        recent_auto_changes.append((description, tuple(wanted_pair[0][0]), tuple(wanted_pair[1][0]), 2))

def join_blob_to_edge(source='button'):
    # exit_protect_mode()
    # exit_select_mode()
    for level in globalLevels[1]:
        for blob in level.children:
            pairs,_ = closest_pair_of_points_between_blobs(blob,level)
            join_2_points(*pairs)

###### Split a blob #######

def split_blob(part):
    pass
    


###### Add a most frequent occuring blob #######

def check_if_blob_inside(points,part_contour):
    # if in_contour(sampled_x,sampled_y,part_contour,3,radius_multiplier=3):
    #     return True

    distance = 10
    for point in points:
        ret = cv2.pointPolygonTest(part_contour, (point[0][0], point[0][1]), True)
        # print sampled_x,sampled_y,ret
        # x = input()
        if ret < (distance):
            # print("Failed in in_contour")
            return False

    return True

def check_if_all_points_are_at_certain_distance_from_all_the_blobs(points,level,distance = 10):

    for child in level.children:
        for point in points:
            if cv2.pointPolygonTest(child.contour, (point[0],point[1]), True) > -(distance):
                return False

    return True



def draw_most_frequent_if_possible(required_blob_points,black_points_in_the_part,level,right_limit,left_limit,bottom_limit,top_limit,required_blob_image):
    global globalLevels,img,add_blob_tried_position,recent_auto_changes
    mode = 'random'
    max_try = 300
    try_count = 0
    if mode == 'random':
        while True:

            if try_count > max_try:
                print "Sorry! I Was not able to find a point quickly"
                break


            sampled_x_displacement = int(np.random.uniform(0,right_limit-left_limit,1))
            sampled_y_displacement = int(np.random.uniform(0,bottom_limit-top_limit,1))
            # print sampled_x_displacement,sampled_y_displacement
            if add_blob_tried_position[top_limit + sampled_y_displacement,left_limit + sampled_x_displacement] == 1:
                # print 'hi'
                continue
            try_count += 1
            new_points_for_blob = required_blob_points.copy()
            new_points_for_blob[:,0] += sampled_x_displacement
            new_points_for_blob[:,1]  += sampled_y_displacement
            new_image_for_blob = required_blob_image.copy()
            new_image_for_blob = np.roll(new_image_for_blob,sampled_x_displacement,axis = 1)
            new_image_for_blob = np.roll(new_image_for_blob,sampled_y_displacement,axis = 0)

            extreme_left = tuple(new_points_for_blob[new_points_for_blob[:, 0].argmin()]) # extreme_left
            extreme_right = tuple(new_points_for_blob[new_points_for_blob[:, 0].argmax()]) # extreme_right
            extreme_top = tuple(new_points_for_blob[new_points_for_blob[:,  1].argmin()]) # extreme_top
            extreme_bottom = tuple(new_points_for_blob[new_points_for_blob[:, 1].argmax()]) # extreme_bottom

            if check_if_blob_inside(cv2.approxPolyDP(np.expand_dims(new_points_for_blob,axis = 1), 0.002 * cv2.arcLength(np.expand_dims(new_points_for_blob,axis = 1), True), True),part_contour=level.contour):

                filtered_points = list(filter(lambda x : x in black_points_in_the_part,new_points_for_blob.tolist()))
                if len(filtered_points) == 0:
                    if check_if_all_points_are_at_certain_distance_from_all_the_blobs(new_points_for_blob.tolist(),level):
                        print "Eureka!!! Found a point"
                        change_rgb_points = new_image_for_blob < 10
                        change_points = np.all(change_rgb_points, axis=-1)
                        img[change_rgb_points] = 0
                        recent_auto_changes.append(('add_shape',change_points))
                        add_blob_tried_position = cv2.fillPoly(add_blob_tried_position, pts =[np.expand_dims(new_points_for_blob,axis = 1)], color=(1))
                        # level.last_search_point = (i,j)
                        updateEncodings()
                        return True
                    else:
                        add_blob_tried_position[top_limit + sampled_y_displacement,left_limit + sampled_x_displacement] = 1
                else:
                    add_blob_tried_position[top_limit + sampled_y_displacement,left_limit + sampled_x_displacement] = 1

    else:
        for i in range(0,right_limit - left_limit,4):
            new_points_for_blob_2 = required_blob_points.copy()
            new_points_for_blob_2[:,0] += i
            new_image_for_blob_2 = required_blob_image.copy()
            new_image_for_blob_2 = np.roll(new_image_for_blob_2,i,axis = 1)
            for j in range(0,bottom_limit - top_limit,4):
                # if i < level.last_search_point[0] and j < level.last_search_point[1]:
                #     continue 
                new_points_for_blob = new_points_for_blob_2.copy()
                new_points_for_blob[:,1]  += j
                new_image_for_blob = new_image_for_blob_2.copy()
                new_image_for_blob = np.roll(new_image_for_blob,j,axis = 0)
                extreme_left = tuple(new_points_for_blob[new_points_for_blob[:, 0].argmin()]) # extreme_left
                extreme_right = tuple(new_points_for_blob[new_points_for_blob[:, 0].argmax()]) # extreme_right
                extreme_top = tuple(new_points_for_blob[new_points_for_blob[:,  1].argmin()]) # extreme_top
                extreme_bottom = tuple(new_points_for_blob[new_points_for_blob[:, 1].argmax()]) # extreme_bottom

                # print left_limit + i , top_limit + j
                if check_if_blob_inside(*extreme_left,part_contour=level.contour) and check_if_blob_inside(*extreme_right,part_contour=level.contour) \
                    and check_if_blob_inside(*extreme_top,part_contour=level.contour) and check_if_blob_inside(*extreme_bottom,part_contour=level.contour):

                    filtered_points = list(filter(lambda x : x in black_points_in_the_part,new_points_for_blob.tolist()))
                    if len(filtered_points) == 0:
                        if check_if_all_points_are_at_certain_distance_from_all_the_blobs(new_points_for_blob.tolist(),level):
                            print "Eureka!!! Found a point"
                            change_rgb_points = new_image_for_blob < 10
                            change_points = np.all(change_rgb_points, axis=-1)
                            img[change_rgb_points] = 0
                            recent_auto_changes.append(('add_shape',change_points))
                            # level.last_search_point = (i,j)
                            updateEncodings()
                            return True

    return False


def add_similar_blobs(index,target):
    global globalLevels,img,mainRoot,add_blob_tried_position,recent_auto_changes
    # exit_protect_mode()
    # exit_select_mode()
    sorted_parts = sortParts(mainRoot, 'area')
    level = sorted_parts[index]
    freq_cnt = {}
    images = {}
    start = time.time()
    for i in range(len(level.children)-1):
        child_i = level.children[i]
        extreme_left_part = tuple(child_i.contour[child_i.contour[:, :, 0].argmin()][0])[0] - 7# extreme_left
        extreme_right_part = tuple(child_i.contour[child_i.contour[:, :, 0].argmax()][0])[0] + 7# extreme_right
        extreme_top_part = tuple(child_i.contour[child_i.contour[:, :, 1].argmin()][0])[1]  - 7# extreme_top
        extreme_bottom_part = tuple(child_i.contour[child_i.contour[:, :, 1].argmax()][0])[1]  + 7# extreme_bottom

        img_gray = img[extreme_top_part:extreme_bottom_part,extreme_left_part:extreme_right_part,:]
        img_gray = cv2.cvtColor(img_gray, cv2.COLOR_BGR2GRAY)

        bw_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        temp_image = np.full(bw_img.shape,0,dtype='uint8')
        bw_img_mask = bw_img < 100
        cv2.fillPoly(temp_image, pts =[child_i.contour], color=(255))
        temp_image = np.logical_and(temp_image, bw_img_mask)
        temp_image = np.logical_not(temp_image)
        temp_image += np.zeros_like(temp_image)
        temp_image = temp_image*255
        temp_image = np.uint8(temp_image)

        if i not in images:
            images[i] = np.dstack([temp_image]*3)

        for j in range(i+1,len(level.children)):

            child = level.children[j]
            extreme_left = tuple(child.contour[child.contour[:, :, 0].argmin()][0])[0] - 3 # extreme_left
            extreme_right = tuple(child.contour[child.contour[:, :, 0].argmax()][0])[0] + 3  # extreme_right
            extreme_top = tuple(child.contour[child.contour[:, :, 1].argmin()][0])[1] - 3# extreme_top
            extreme_bottom = tuple(child.contour[child.contour[:, :, 1].argmax()][0])[1] + 3# extreme_bottom
            bw_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            temp_image = np.full(bw_img.shape,0,dtype='uint8')
            bw_img_mask = bw_img < 100
            cv2.fillPoly(temp_image, pts =[child.contour], color=(255))
            temp_image = np.logical_and(temp_image, bw_img_mask)
            temp_image = np.logical_not(temp_image)
            temp_image += np.zeros_like(temp_image)
            temp_image = temp_image*255
            temp_image = np.uint8(temp_image)
            # temp_image[np.squeeze(child.contour,axis = 1)] = 0
            # _,temp_contours,hierarchy = cv2.findContours(temp_image,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
            template = temp_image[extreme_top:extreme_bottom,extreme_left:extreme_right]
            # template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            w, h = template.shape[1], template.shape[0]
            if img_gray.shape[1] < w or img_gray.shape[0] < h:
                img_gray = np.pad(img_gray,(max(w-img_gray.shape[1],h-img_gray.shape[0]) + 5),'constant',constant_values = (255))
                img_gray = np.uint8(img_gray)


            if j not in images:
                images[j] = np.dstack([temp_image]*3)


            res = cv2.matchTemplate(img_gray,template,cv2.TM_CCOEFF_NORMED)

            # print res
            threshold = 0.5
            loc = np.where( res >= threshold)
            # print res[loc]
            if len(loc[0]) > 3:
                # print i,j
                if i in freq_cnt:
                    freq_cnt[i] += 1
                else:
                    freq_cnt[i] = 1                    
    # print freq_cnt
    print time.time() - start
    if len(freq_cnt) == 0:
        print "ERROR! No similar contours found"
        return False
    sorted_freq = sorted(freq_cnt.items(), key = lambda x: x[1]) 
    required_blob = level.children[sorted_freq[-1][0]]
    required_blob_image = images[sorted_freq[-1][0]]
    required_blob_points = [point[0] for point in required_blob.contour]
    curr_no_blobs  = len(level.children)
    add_blob_tried_position = None
    while curr_no_blobs < target :
        sorted_parts = sortParts(mainRoot, 'area')
        level = sorted_parts[index]
        bw = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        extreme_left = tuple(required_blob.contour[required_blob.contour[:, :, 0].argmin()][0]) # extreme_left
        extreme_right = tuple(required_blob.contour[required_blob.contour[:, :, 0].argmax()][0]) # extreme_right
        extreme_top = tuple(required_blob.contour[required_blob.contour[:, :, 1].argmin()][0]) # extreme_top
        extreme_bottom = tuple(required_blob.contour[required_blob.contour[:, :, 1].argmax()][0]) # extreme_bottom

        extreme_left_part = tuple(level.contour[level.contour[:, :, 0].argmin()][0]) # extreme_left
        extreme_right_part = tuple(level.contour[level.contour[:, :, 0].argmax()][0]) # extreme_right
        extreme_top_part = tuple(level.contour[level.contour[:, :, 1].argmin()][0]) # extreme_top
        extreme_bottom_part = tuple(level.contour[level.contour[:, :, 1].argmax()][0]) # extreme_bottom

        right_limit = extreme_right_part[0] - (extreme_right[0] - extreme_left[0])    
        left_limit = extreme_left_part[0]
        top_limit = extreme_top_part[1]
        bottom_limit = extreme_bottom_part[1] - (extreme_bottom[1] - extreme_top[1])
        black_points_in_the_part = [point[0].tolist() for child in level.children for point in child.contour]
        
        required_blob_points2 = np.array(required_blob_points)
        required_blob_points2[:,0] += extreme_left_part[0] - extreme_left[0]
        required_blob_points2[:,1] += extreme_top_part[1] - extreme_top[1]
        required_blob_image2 = required_blob_image.copy()
        required_blob_image2 = np.roll(required_blob_image2,extreme_left_part[0] - extreme_left[0],axis = 1)
        required_blob_image2 = np.roll(required_blob_image2,extreme_top_part[1] - extreme_top[1],axis = 0)

        if add_blob_tried_position is None:
            add_blob_tried_position = np.zeros((img.shape[0],img.shape[1]))
        # cv2.circle(img,(left_limit,top_limit),1,(255,0,0),-1)
        # cv2.circle(img,(right_limit,bottom_limit),1,(0,0,255),-1)
        # updateEncodings()
        if draw_most_frequent_if_possible(required_blob_points2,black_points_in_the_part,level,right_limit,left_limit,bottom_limit,top_limit,required_blob_image2):
            curr_no_blobs += 1
        else:
            print "ERROR! The algorithm was not able to add blobs"
            return False

    return True

        # cv2.circle(img,extreme_top,1,(0,255,0),-1)
        # cv2.circle(img,extreme_bottom,1,(255,0,255),-1)

        # required_blob_points = list(map(lambda x: (x[0] + extreme_top_part[0] - extreme_top[0]),required_blob_points))
        # required_blob_points = list(map(lambda x: (x[1] + extreme_left_part[1] - extreme_left[1]),required_blob_points))
        # only take extreme points of the required blob instead of all the points

        # @todo : placing of the detected frequent blob

def add_most_frequent_blob(source='button'):
    # exit_protect_mode()
    # exit_select_mode()

    # for i in range(len(globalLevels[1])):
    #     add_similar_blobs(i,20)  
    add_reduce_blobs([0],[20])  

def reduce_n_blobs(index,goal):
    global globalLevels,mainRoot
    sorted_parts = sortParts(mainRoot, 'area')
    current_children = len(sorted_parts[index].children)
    while current_children > goal:
        join_blob_and_edge(sorted_parts[index],sorted_parts)
        sorted_parts = sortParts(mainRoot, 'area')
        current_children += -1



def add_reduce_blobs(indices_of_parts,list_of_changes):
    global globalLevels,mainRoot, currSuggestion, index
    if mainRoot is None or len(mainRoot.children) <= 0:
        return

    if len(mainRoot.children) != max(indices_of_parts)+1:
        updateSuggestion(SHORT_SEARCH)
        indices_of_parts = list(range(len(currSuggestion[1][1])))
        list_of_changes = currSuggestion[1][1]
        print "ERROR: parts have changed for add_reduce_blobs"

    for i in range(len(indices_of_parts)):
        index = indices_of_parts[i]
        goal = list_of_changes[i]
        if goal < 0:
            print "ERROR! goal is negetive"
        sorted_parts = sortParts(mainRoot, 'area')

        curr_children = len(sorted_parts[index].children)
        changes = goal - curr_children
        if changes == 0:
            continue
        elif changes > 0:
            output = add_similar_blobs(index,goal)
            if output is False:
                sorted_parts = sortParts(mainRoot, 'area')
                curr_children = len(sorted_parts[index].children)
                while curr_children < goal:
                    output = add_blob(sorted_parts[index])
                    if output is False:
                        print "Cannot change blobs"
                        break
                    sorted_parts = sortParts(mainRoot, 'area')
                    curr_children = len(sorted_parts[index].children)
        else:
            # print "reducing"
            reduce_n_blobs(index,goal)



############################################


def set_target_dividers(posn_list):
    global targetDividers
    if posn_list is not None and len(posn_list) > 0:
        resetTargetDividers()
        for posn in posn_list:
            targetDividers = targetDividers[:posn] + '|' + targetDividers[posn+1:]

def cost_params():
    global mainRoot, addRemovePrefScale
    cost_base = 10
    protected_multiplier = 100
    sorted_parts = sortParts(mainRoot, 'area')
    multipliers = []
    areas_remaining = []
    for part in sorted_parts:
        if part.protected:
            multipliers.append(protected_multiplier)
        else:
            multipliers.append(1)
        area_remaining = part.area
        if part.children is not None:
            for child in part.children:
                area_remaining -= child.area
        areas_remaining.append(area_remaining)
    prefVal = addRemovePrefScale.get()
    prefVal = float(prefVal) / 20.0
    return (cost_base, multipliers, prefVal, areas_remaining)


def str_format_recent_auto_changes():
    global recent_auto_changes
    out_str = ''
    for entry in recent_auto_changes:
        if entry[0] == 'delete_blob':
            if entry[1] is not None and len(entry[1]) > 0:
                print_tuple = ('delete_blob', tuple(entry[1][0,0]))
            else:
                print_tuple = ('delete_blob', None)
            out_str += str(print_tuple) + ' '
        elif entry[0] == 'add_shape':
            altered_pts = np.where(entry[1])
            if len(altered_pts)>0 and len(altered_pts[0])>0:
                top_left = (altered_pts[0][0],altered_pts[1][0])
            else:
                top_left = (-1,-1)
            print_tuple = ('add_shape', top_left)
            out_str += str(print_tuple) + ' '
        else:
            out_str += str(entry) + ' '
    return out_str


def auto_fix_blobs(prefVal=0.0):
    global mainRoot, targetBinString, targetDividers, recent_auto_changes, currSuggestion

    if mainRoot is None or not mainRoot.children:
        print "Cannot fix blobs; No parts found"
        return

    recent_auto_changes = []
    perform_best_part_cuts()
    set_target_dividers(currSuggestion[1][2])
    add_reduce_blobs(list(range(len(currSuggestion[1][1]))), currSuggestion[1][1])
    logEvent('auto_fix_blobs', str_format_recent_auto_changes())
    addUndoable()
    updateEncodings()
    updateVisualTargetPanel()


    #returns ([(cut_length,(pt1),(pt2),part1.cNum,part2.cNum),
#          (div_cost,[part_encodings],[divider_posns]),
#          [(part_area,part_encoding,[former_part.cNums],multiplier,[former_part.centroids])]

    # img_part_vals = []
    # sorted_parts = sortParts(mainRoot, 'area')
    # for part in sorted_parts:
    #     img_part_vals.append(part.encoding)
    # cost_base, multipliers, _ = cost_params()
    #
    # fixed_target = find_divisions(img_part_vals,targetBinString,exp_weight_cost_fun(cost_base, prefVal),multipliers)
    # if fixed_target is None or fixed_target[1] is None:
    #     print "ERROR: Unable to find valid dividers"
    #     return
    # target_part_vals = fixed_target[1]
    # set_target_dividers(fixed_target[2])
    #
    # for i in range(len(sorted_parts)):
    #     sorted_parts = sortParts(mainRoot, 'area')
    #     sorted_parts[i].children = sortBlobs(sorted_parts[i], 'area')
    #     counter = 0
    #     max_count = 100
    #     while img_part_vals[i] != target_part_vals[i] and counter < max_count:
    #         sorted_parts = sortParts(mainRoot, 'area')
    #         sorted_parts[i].children = sortBlobs(sorted_parts[i], 'area')
    #         if img_part_vals[i] < target_part_vals[i]:
    #             add_blob(sorted_parts[i])
    #             img_part_vals[i] += 1
    #         else:
    #             delete_first_blob(sorted_parts[i])
    #             img_part_vals[i] -= 1
    #     if counter >= max_count:
    #         print "ERROR: Fix blobs failed with too many attempts"
    # updateEncodings()
    # updateVisualTargetPanel()

def auto_fix_blobs_btn(source='button'):
    global addRemovePrefScale, suggestMode, fixBlobBtn
    fixBlobBtn.config(relief=SUNKEN)
    exit_protect_mode()
    exit_select_mode()
    if suggestMode == 0:
        pass
    elif suggestMode == 1:
        updateSuggestion(LONG_SEARCH)
    else:
        prefVal = addRemovePrefScale.get()
        prefVal = float(prefVal) / 20.0
        auto_fix_blobs(prefVal)
    updateEncodings()
    fixBlobBtn.config(relief=RAISED)
    logEvent(source + 'auto_fix_blobs', suggestMode)

def protect_btn(source='button'):
    global tool, protectBtn
    exit_select_mode()
    if tool == 'protect':
        exit_protect_mode()
    else:
        protectBtn.config(relief=SUNKEN)
        tool = 'protect'
    logEvent(source + 'protect_toggle', tool)

def exit_protect_mode():
    global tool, protectBtn, protectImg, drawProtected
    protectBtn.config(relief=RAISED)
    tool = 'pen'
    protectImg = np.ones((CANVAS_HEIGHT, CANVAS_WIDTH, 3), np.uint8) * 255
    # drawProtected = False

def toggle_blob_protection(x, y):
    global mainRoot, protected_centroids, suggestMode
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
            i = 0
            while i < len(protected_centroids):
                centroid = protected_centroids[i]
                if in_contour(centroid[0],centroid[1],selected.contour,0):
                    protected_centroids = protected_centroids[:i] + protected_centroids[i+1:]
                    i -= 1
                i += 1
        else:
            selected.protected = True
            protected_centroids.append((x,y))
    # colour_protected()
    if suggestMode != 0:
        updateSuggestion(SHORT_SEARCH)
    updateEncodings()

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

#### Drag and drop blobs ########

def select_blob_btn(source='button'):
    global tool,selectBtn
    exit_protect_mode()
    if tool == 'select':
        exit_select_mode()
    else:
        selectBtn.config(relief=SUNKEN)
        tool = 'select'
    logEvent(source + 'select_toggle')

def exit_select_mode():
    global tool, selectBtn, select_img,current_selected_blob,blob_image,click_points,image_wo_blob
    # protectBtn.config(relief=RAISED)
    selectBtn.config(relief=RAISED)
    tool = 'pen'
    reset_select_mode()
    # drawProtected = False

def reset_select_mode():
    global tool, selectBtn, select_img,current_selected_blob,blob_image,click_points,image_wo_blob, blob_moved
    # protectBtn.config(relief=RAISED)
    current_selected_blob = None
    blob_image = None
    image_wo_blob = None
    click_points = None
    if blob_moved:
        addUndoable()
        blob_moved = False
    updateEncodings()

def select_blob(x,y):
    global mainRoot,current_selected_blob,blob_image,click_points
    current_selected_blob = None
    blob_image = None
    click_points = (x,y)
    if mainRoot is None:
        return
    selected = None
    for part in mainRoot.children:
        for child in part.children:
            if in_contour(x, y, child.contour, 0):
                selected = child
                break
    if selected is not None:
        if selected.dnd:
            selected.dnd = False
        else:
            selected.dnd = True

        current_selected_blob = selected

def remove_the_selected_blob():
    global current_selected_blob,blob_image,img,image_wo_blob,blob_moved

    if current_selected_blob is None:
        pass
    else:
        blob_moved = True
        bw_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blob_image = np.full(bw_img.shape,0,dtype='uint8')
        bw_img_mask = bw_img < 100
        cv2.fillPoly(blob_image, pts =[current_selected_blob.contour], color=(255))
        blob_image = np.logical_and(blob_image, bw_img_mask)
        blob_image = np.logical_not(blob_image)
        blob_image += np.zeros_like(blob_image)
        blob_image = blob_image*255
        blob_image = np.uint8(blob_image)
        blob_image = np.dstack([blob_image]*3)
        img[blob_image < 10] = 255
        image_wo_blob = img.copy()

def move_selected(x,y):
    global current_selected_blob,img,blob_image,click_points,image_wo_blob,canvasPanel,displayImg

    if current_selected_blob is None:
        pass
    else:
        if blob_image is None:
            remove_the_selected_blob()
        change_in_x = x - click_points[0]
        change_in_y = y - click_points[1]
        click_points = (x,y)
        blob_image = np.roll(blob_image,change_in_x,axis = 1)
        blob_image = np.roll(blob_image,change_in_y,axis = 0)
        img = image_wo_blob.copy()
        img[blob_image < 10] = 0
        displayImg = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        displayImg = Image.fromarray(displayImg)
        displayImg = ImageTk.PhotoImage(displayImg)
        canvasPanel.configure(image=displayImg)
        canvasPanel.image = displayImg






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

def square_dist(p1,p2):
    return (p1[0]-p2[0])**2 + (p1[1]-p2[1])**2

def choose_contour_points(contour):
    min_sep = 20 #minimum Manhattan distance between consecutive points
    if contour is None or len(contour) <= 0:
        return []
    selected = [contour[0][0]]
    for item in contour:
        if manhattan_dist(item[0], selected[-1]) >= min_sep:
            selected.append(item[0])
    return selected

def dot_prod(vec1, vec2):
    sum = 0
    for i in range(len(vec1)):
        sum += vec1[i]*vec2[i]
    return sum

def closest_pt_on_segment(pt, seg_pt1, seg_pt2):
    if seg_pt1 == seg_pt2:
        print "ERROR: Cannot define a line segment from one point"
        return None
    u = (seg_pt1[0]-pt[0],seg_pt1[1]-pt[1])
    v = (seg_pt2[0]-seg_pt1[0],seg_pt2[1]-seg_pt1[1])
    t = -float(dot_prod(v,u))/(dot_prod(v,v))
    if t >= 0 and t <= 1:
        closest_x = int(round(((1-t)*seg_pt1[0]+t*seg_pt2[0])))
        closest_y = int(round(((1-t)*seg_pt1[1]+t*seg_pt2[1])))
        closest = (closest_x, closest_y)
        dist_vec = (closest[0]-pt[0],closest[1]-pt[1])
        dist_sqr = dist_vec[0]**2 + dist_vec[1]**2
        return (dist_sqr, closest)
    else:
        return min((square_dist(pt,seg_pt1),seg_pt1), (square_dist(pt,seg_pt2),seg_pt2))


#extend the line segment ending at pt1
def extend_line(pt1,pt2,extend_dist):
    if pt1[0]-pt2[0] == 0:
        slope = np.sign(pt1[1]-pt2[1])*100000.0
    else:
        slope = float(pt1[1]-pt2[1])/(pt1[0]-pt2[0])
    factor = math.sqrt(float(extend_dist**2)/(slope**2 + 1))
    out_point = [None,None]
    if pt1[0] - pt2[0] >= 0:
        out_point[0] = int(round(pt1[0] + factor))
    else:
        out_point[0] = int(round(pt1[0] - factor))
    if pt1[1] - pt2[1] >= 0:
        out_point[1] = int(round(pt1[1] + factor*abs(slope)))
    else:
        out_point[1] = int(round(pt1[1] - factor*abs(slope)))
    if out_point[0] < 0:
        out_point[0] = 0
    if out_point[1] < 0:
        out_point[1] = 0
    if out_point[0] > CANVAS_WIDTH-1:
        out_point[0] = CANVAS_WIDTH-1
    if out_point[1] > CANVAS_HEIGHT-1:
        out_point[1] = CANVAS_HEIGHT-1
    return tuple(out_point)


def closest_point_pairs():
    global mainRoot, markedImg
    max_cut_dist = 30
    if mainRoot is None or len(mainRoot.children) <= 1:
        return []
    min_list = []
    #check pairs of parts
    for i in range(len(mainRoot.children)):
        part1 = mainRoot.children[i]
        for j in range(i+1,len(mainRoot.children)+1):
            if j == len(mainRoot.children):
                part2 = mainRoot
                using_root = True
            else:
                part2 = mainRoot.children[j]
                using_root = False
            if bounding_box_check(part1,part2):
                # if part1.select_points is None:
                #     part1.select_points = choose_contour_points(part1.contour)
                # if part2.select_points is None:
                #     part2.select_points = choose_contour_points(part2.contour)
                min_tuple = None

                for p1_index in range(len(part1.approx)):
                    p1_point = part1.approx[p1_index][0]
                    for p2_index in range(len(part2.approx)):
                        p2_point = part2.approx[p2_index][0]
                        curr_dist = square_dist(p1_point,p2_point)
                        if (min_tuple is None or curr_dist <= min_tuple[0]): # and determine_adjacent(p1_point,p2_point):
                            min_tuple = (curr_dist, p1_point, p2_point, p1_index, p2_index)

                if min_tuple is not None:
                    p1_mid = tuple(part1.approx[min_tuple[3]][0])
                    p1_1 = tuple(part1.approx[min_tuple[3]-1][0])
                    p1_2 = tuple(part1.approx[(min_tuple[3]+1)%len(part1.approx)][0])
                    p2_mid = tuple(part2.approx[min_tuple[4]][0])
                    p2_1 = tuple(part2.approx[min_tuple[4]-1][0])
                    p2_2 = tuple(part2.approx[(min_tuple[4]+1)%len(part2.approx)][0])
                    candidates = [[None,p1_mid,p2_1,p2_mid], [None,p1_mid,p2_2,p2_mid],
                                  [None,p1_1,p2_1,p2_mid], [None,p1_1,p2_2,p2_mid],
                                  [None,p1_2,p2_1,p2_mid], [None,p1_2,p2_2,p2_mid],
                                  [None,p2_mid,p1_1,p1_mid], [None,p2_mid,p1_2,p1_mid],
                                  [None,p2_1,p1_1,p1_mid], [None,p2_1,p1_2,p1_mid],
                                  [None,p2_2,p1_1,p1_mid], [None,p2_2,p1_2,p1_mid]]
                    for curr in candidates:
                        curr[0] = closest_pt_on_segment(curr[1],curr[2],curr[3])
                    closest = min(candidates)
                    if determine_adjacent(closest[0][1],closest[1]) and closest[0][0]<=max_cut_dist**2:
                        extended_1 = extend_line(closest[0][1],closest[1],EXTRA_CUT_LENGTH)
                        extended_2 = extend_line(closest[1],closest[0][1],EXTRA_CUT_LENGTH)
                        min_list.append((closest[0][0],extended_1,extended_2,part1.cNum,part2.cNum))
                        # if not using_root:
                        #     min_list.append((closest[0][0],closest[0][1],closest[1],part1.cNum,part2.cNum))
                        # else:
                        #     root_point = extend_line(closest[0][1],closest[1],EXTRA_CUT_LENGTH)
                        #     min_list.append((closest[0][0],root_point,closest[1],part1.cNum,part2.cNum))

    # for item in min_list:
    #     cv2.line(markedImg,item[1],item[2],(0,0,255),2)
    # for part in mainRoot.children:
    #     for point in part.approx:
    #         cv2.circle(markedImg, tuple(point[0]), 3, (255,0,0), -1)
    # updateGuiImage()
    return min_list


def est_cut_area(pt1,pt2,width):
    return int(round(max((math.sqrt(square_dist(pt1,pt2))-EXTRA_CUT_LENGTH*2)*width,0)))


# def bfs_part_reduction(max_nodes):
#     global targetBinString, mainRoot
#     if mainRoot is None or len(mainRoot.children)<=0:
#         return []
#     ambig_factor = 1.0
#     sorted_parts = sortParts(mainRoot, 'area')
#     cost_base, multipliers, prefVal = cost_params()
#     possible_cuts = closest_point_pairs()
#     part_info = []
#     for i in range(len(sorted_parts)):
#         part = sorted_parts[i]
#         part_info.append([part.area,part.encoding,[part.cNum],multipliers[i]])
#     initial_div = find_divisions([i[1] for i in part_info],targetBinString,exp_weight_cost_fun(cost_base, prefVal),multipliers)
#     cuts_tried = {}
#     cuts_used = []
#     cuts_tried[tuple(cuts_used)] = (initial_div[0],part_info)
#     #root_state = (initial_div[0],part_info,[],0)
#     best_state = (cuts_used, initial_div)
#     q = deque([cuts_used])
#     num_nodes = 0
#
#     while q:
#         curr_cuts = q.popleft()
#         curr_info = cuts_tried[tuple(curr_cuts)][1]
#         if num_nodes > max_nodes:
#             break
#         else:
#             for i in range(len(possible_cuts)):
#                 if i not in curr_cuts:
#                     new_cuts = curr_cuts[:] + [i]
#                     new_cuts.sort()
#                     if tuple(new_cuts) not in cuts_tried:
#                         new_info = []
#                         part_cut_1 = possible_cuts[i][3]
#                         part_cut_2 = possible_cuts[i][4]
#                         found_part = None
#                         cut_area = 0
#                         for curr_entry in curr_info:
#                             if part_cut_1 not in curr_entry[2] and part_cut_2 not in curr_entry[2]:
#                                 new_info.append([curr_entry[0],curr_entry[1],curr_entry[2][:],curr_entry[3]])
#                             elif found_part is None:
#                                 found_part = curr_entry
#                             else:
#                                 cut_area = est_cut_area(possible_cuts[i][1],possible_cuts[i][2],PART_CUT_WIDTH)
#                                 new_info.append([curr_entry[0]+found_part[0]+cut_area,
#                                                  curr_entry[1]+found_part[1],
#                                                  curr_entry[2]+found_part[2],
#                                                  max(curr_entry[3],found_part[3])])
#                         new_info.sort()
#                         ambiguous = False
#                         for i in range(len(new_info)):
#                             entry = new_info[i]
#                             if part_cut_1 in entry[2]:
#                                 if i>=1 and abs(new_info[i-1][0] - entry[0]) < cut_area*ambig_factor:
#                                     ambiguous = True
#                                 if i<len(new_info)-1 and abs(new_info[i+1][0] - entry[0]) < cut_area*ambig_factor:
#                                     ambiguous = True
#                         if ambiguous:
#                             cuts_tried[tuple(new_cuts)] = (None,new_info)
#                         else:
#                             new_div = find_divisions([i[1] for i in new_info],targetBinString, \
#                                                      exp_weight_cost_fun(cost_base, prefVal),[i[3] for i in new_info])
#                             if new_div is None:
#                                 cuts_tried[tuple(new_cuts)] = (None,new_info)
#                             else:
#                                 cuts_tried[tuple(new_cuts)] = (new_div[0],new_info)
#                                 if new_div[0] < cuts_tried[tuple(best_state[0])][0]:
#                                     best_state = (new_cuts, new_div)
#                                 q.append(new_cuts)
#             num_nodes += 1
#     final_cuts = []
#     for index in best_state[0]:
#         final_cuts.append(possible_cuts[index])
#     return (final_cuts, best_state[1])


#returns ([(cut_length,(pt1),(pt2),part1.cNum,part2.cNum),
#          (div_cost,[part_encodings],[divider_posns]),
#          [(part_area,part_encoding,[former_part.cNums],multiplier,[former_part.centroids],area_remaining)]
def bestfs_part_reduction(max_time):
    global targetBinString, mainRoot
    if mainRoot is None or len(mainRoot.children)<=0:
        return []
    ambig_factor = 1.0
    sorted_parts = sortParts(mainRoot, 'area')
    cost_base, multipliers, prefVal, areas_remaining = cost_params()
    possible_cuts = closest_point_pairs()
    part_info = []
    for i in range(len(sorted_parts)):
        part = sorted_parts[i]
        if in_contour(part.centroid[0],part.centroid[1],part.contour,0):
            point_in_contour = part.centroid
        else:
            point_in_contour = tuple(part.contour[0][0])
        part_info.append([part.area,part.encoding,[part.cNum],multipliers[i],[point_in_contour],areas_remaining[i]])
    initial_div = find_divisions([i[1] for i in part_info],targetBinString,exp_weight_cost_fun(cost_base, prefVal),multipliers,areas_remaining)
    cuts_tried = {}
    cuts_used = []
    cuts_tried[tuple(cuts_used)] = (initial_div[0],part_info)
    best_state = (cuts_used, initial_div, part_info)
    num_nodes = 0
    start_time = time.time()
    q = [(initial_div[0], cuts_used)]
    heapq.heapify(q)

    while q:
        curr_cuts = heapq.heappop(q)[1]
        curr_info = cuts_tried[tuple(curr_cuts)][1]
        # if num_nodes > max_nodes:
        if time.time() - start_time > max_time:
            break
        else:
            i = 0
            while i < len(possible_cuts) and not (time.time() - start_time > max_time):
                if i not in curr_cuts:
                    new_cuts = curr_cuts[:] + [i]
                    new_cuts.sort()
                    if tuple(new_cuts) not in cuts_tried:
                        new_info = []
                        part_cut_1 = possible_cuts[i][3]
                        part_cut_2 = possible_cuts[i][4]
                        found_part = None
                        cut_area = 0
                        for curr_entry in curr_info:
                            if part_cut_1 not in curr_entry[2] and part_cut_2 not in curr_entry[2]:
                                new_info.append([curr_entry[0],curr_entry[1],curr_entry[2][:],curr_entry[3], \
                                                 curr_entry[4][:], curr_entry[5]])
                            elif found_part is None:
                                found_part = curr_entry
                            else:
                                cut_area = est_cut_area(possible_cuts[i][1],possible_cuts[i][2],PART_CUT_WIDTH)
                                new_info.append([curr_entry[0]+found_part[0]+cut_area,
                                                 curr_entry[1]+found_part[1],
                                                 curr_entry[2]+found_part[2],
                                                 max(curr_entry[3],found_part[3]),
                                                 curr_entry[4]+found_part[4],
                                                 curr_entry[5]+found_part[5]])
                        new_info.sort()
                        ambiguous = False
                        for j in range(len(new_info)):
                            entry = new_info[j]
                            if part_cut_1 in entry[2]:
                                if j>=1 and abs(new_info[j-1][0] - entry[0]) < cut_area*ambig_factor:
                                    ambiguous = True
                                if j<len(new_info)-1 and abs(new_info[j+1][0] - entry[0]) < cut_area*ambig_factor:
                                    ambiguous = True
                        if ambiguous:
                            cuts_tried[tuple(new_cuts)] = (None,new_info)
                        else:
                            new_div = find_divisions([k[1] for k in new_info],targetBinString, \
                                                     exp_weight_cost_fun(cost_base, prefVal), \
                                                     [k[3] for k in new_info], [k[5] for k in new_info])
                            if new_div is None:
                                cuts_tried[tuple(new_cuts)] = (None,new_info)
                            else:
                                cuts_tried[tuple(new_cuts)] = (new_div[0],new_info)
                                if new_div[0] < cuts_tried[tuple(best_state[0])][0]:
                                    best_state = (new_cuts,new_div,new_info)
                                heapq.heappush(q,(new_div[0],new_cuts))
                        num_nodes += 1
                i += 1

    final_cuts = []
    print "Searched " + str(num_nodes) + " nodes"
    for index in best_state[0]:
        final_cuts.append(possible_cuts[index])
    return (final_cuts, best_state[1], best_state[2])


def perform_best_part_cuts():
    global img, recent_auto_changes, currSuggestion
    updateSuggestion(LONG_SEARCH)
    best_cuts = currSuggestion[0]
    for cut in best_cuts:
        recent_auto_changes.append(('cut_part', cut[1], cut[2], PART_CUT_WIDTH))
        cv2.line(img,cut[1],cut[2],WHITE,PART_CUT_WIDTH)
    updateEncodings()
    logEvent('perform_best_cuts')


def reduce_part(source='button'):
    global undoStack, undoIndex, img, globalLevels
    perform_best_part_cuts()
    exit_protect_mode()
    exit_select_mode()
    # for level in globalLevels[1]:
    #     cut_part(level)
    logEvent(source + 'reduce_part')


def sliderRelease(event):
    global suggestToggle, addRemovePrefScale
    if suggestToggle != 0:
        updateSuggestion(SHORT_SEARCH)
    logEvent('sliderRelease', addRemovePrefScale.get())


def updateSuggestion(time=SHORT_SEARCH):
    global currSuggestion
    currSuggestion = bestfs_part_reduction(time)
    if currSuggestion:
        set_target_dividers(currSuggestion[1][2])
        updateVisualTargetPanel()
    updateEncodings()
    logEvent('updateSuggestion', str(currSuggestion))


def match_points_to_parts(pts):
    global mainRoot
    if mainRoot is None or len(mainRoot.children) <= 0:
        return [None for _ in range(len(pts))]
    matches = []
    sorted_parts = sortParts(mainRoot, 'area')
    for pt in pts:
        i=0
        found = False
        while i < len(sorted_parts) and not found:
            if in_contour(pt[0], pt[1], sorted_parts[i].contour, 0):
                found = True
                matches.append(sorted_parts[i])
            i += 1
        if not found:
            matches.append(None)
    return matches


def drawSuggestion():
    global mainRoot, markedImg, currSuggestion
    if mainRoot is None or len(mainRoot.children) <= 0 or currSuggestion is None or len(currSuggestion) <= 0:
        text1 = 'Start by drawing a marker with at least one part.'
        text2 = 'As a rule of thumb, you will probably want about half as many parts as the number of bits you are encoding.'
        text3 = '(e.g. 10 bits -> 5 parts, 20 bits -> 10 parts)'
        cv2.putText(markedImg, text1, (10,20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, GREEN, 2)
        cv2.putText(markedImg, text2, (10,40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, GREEN, 2)
        cv2.putText(markedImg, text3, (10,60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, GREEN, 2)
        return

    cuts = currSuggestion[0]
    first_cut_parts = match_points_to_parts([cut[1] for cut in cuts])
    for i in range(len(cuts)):
        cut = cuts[i]
        part = first_cut_parts[i]
        if part is not None and in_contour(cut[2][0], cut[2][1], part.contour, 0):
            line_colour = GREEN
        else:
            line_colour = RED
        cv2.line(markedImg,cut[1],cut[2],line_colour,8)

    centroid_lists = [info[4] for info in currSuggestion[2]]
    centroids = [l[0] for l in centroid_lists]
    encodings = currSuggestion[1][1]
    if encodings is not None and len(encodings) > 0:
        matches = match_points_to_parts(centroids)
        for i in range(len(centroids)):
            centroid = centroids[i]
            encoding = encodings[i]
            part = matches[i]
            if part is None:
                text = '-/' + str(encoding)
                cv2.putText(markedImg, text, centroid, cv2.FONT_HERSHEY_SIMPLEX, 0.5, DARK_RED, 2)
            else:
                text = str(part.encoding) + '/' + str(encoding)
                if part.encoding == encoding:
                    cv2.putText(markedImg, text, centroid, cv2.FONT_HERSHEY_SIMPLEX, 0.5, GREEN, 2)
                else:
                    cv2.putText(markedImg, text, centroid, cv2.FONT_HERSHEY_SIMPLEX, 0.5, RED, 2)


def drawFixes():
    global markedImg, recent_auto_changes
    for change in recent_auto_changes:
        if change[0] == 'cut_part' or change[0] == 'join_blobs' or change[0] == 'join_to_edge':
            cv2.line(markedImg,change[1],change[2],ORANGE,change[3])
        elif change[0] == 'delete_blob':
            cv2.drawContours(markedImg,[change[1]], -1, ORANGE, 2)
        elif change[0] == 'add_circle_blob':
            cv2.circle(markedImg, change[1], change[2], ORANGE, -1)
        elif change[0] == 'add_shape':
            markedImg[change[1]] = ORANGE
        else:
            print 'ERROR: drawFixes encountered unrecognized change description'

        # recent_auto_changes.append(('cut_part', cut[1], cut[2], PART_CUT_WIDTH))
        # cv2.line(img,cut[1],cut[2],WHITE,PART_CUT_WIDTH)

        # img[new_image_for_blob < 10] = 0
        # recent_auto_changes.append(('add_shape',new_image_for_blob < 10))

        # join_2_points(wanted_pair[0], wanted_pair[1], 2)
        # recent_auto_changes.append((description, tuple(wanted_pair[0][0]), tuple(wanted_pair[1][0]), 2))

        # cv2.fillPoly(img, pts =[blob.contour], color=(255,255,255))
        # recent_auto_changes.append(('delete_blob', blob.contour))
        #
        # cv2.circle(img, (sampled_y, sampled_x), radius, colour, -1)
        # recent_auto_changes.append(('add_circle_blob', (sampled_y, sampled_x), radius))

##########################################



###### Determine adjacent point ########

def determine_adjacent(point1, point2):
    global img 
    bw  = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    angle = np.arctan2(point2[1] - point1[1],point2[0] - point1[0])
    distance = 1
    nw1,nb,nw2 = 0,0,0
    sign_x = np.sign(np.cos(angle))
    sign_y = np.sign(np.sin(angle))
    while True:
        new_x = distance*np.cos(angle) + point1[0]
        new_y = distance*np.sin(angle) + point1[1]
        if int(np.round(new_x)) < 0:
            new_x = 0
        if int(np.round(new_x)) > CANVAS_WIDTH-1:
            new_x = CANVAS_WIDTH - 1
        if int(np.round(new_y)) < 0:
            new_y = 0
        if int(np.round(new_y)) > CANVAS_HEIGHT-1:
            new_y = CANVAS_HEIGHT-1
        val = bw[int(np.round(new_y)),int(np.round(new_x))]
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

        if sign_x == 0 or (sign_x>0 and int(np.round(new_x)) >= point2[0]) or (sign_x<0 and int(np.round(new_x)) <= point2[0]):
            if sign_y == 0 or (sign_y>0 and int(np.round(new_y)) >= point2[1]) or (sign_y<0 and int(np.round(new_y)) <= point2[1]):
                break

        # if int(np.round(new_x)) == point2[0] and int(np.round(new_y)) == point2[1]:
        #     break

        distance += 1

    if nw1 > -1 and nb > 0 and nw2 > -1:
        return True
    
    return False

#######################################




#figures out the current encoding of the image and updates all overlays
def updateEncodingsForReal():
    global drawEncodings, drawCentroids, drawAmbToggle, suggestionIndex, suggestionImg, suggestions, \
        suggestionLocs, drawTargetToggle, img, markedImg, mainRoot, expPhase, blobMode, oldEncoding, \
        blobOrderMode, blobIconDict, oldPartNum, globalLevels, usingThreading, oldEncodingNum, suggestToggle, \
        suggestMode, protected_centroids
    markedImg = img.copy()

    #find the region adjacency tree of the image
    if not usingThreading:
        determineMainRoot()
    levels = globalLevels

    if mainRoot is not None and len(mainRoot.children) > 0:
        for part in mainRoot.children:
            for centroid in protected_centroids:
                if in_contour(centroid[0],centroid[1],part.contour,0):
                    part.protected = True
                    cv2.drawContours(markedImg, [part.contour], -1, DARK_YELLOW, 4)

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

    if suggestToggle != 0:
        if suggestMode == 0:
            pass
        elif suggestMode == 1:
            drawSuggestion()
        else:
            drawFixes()

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
    global undoStack, undoIndex, img, suggestToggle, suggestMode
    exit_protect_mode()
    exit_select_mode()
    if undoIndex < len(undoStack)-1:
        img = np.copy(undoStack[undoIndex+1])
        undoIndex += 1
        updateEncodings()
        if suggestToggle != 0 and suggestMode != 0:
            updateSuggestion(SHORT_SEARCH)
    logEvent(source + 'Undo')


#perform one redo action on the canvas
def redo(source='button'):
    global undoStack, undoIndex, img
    exit_protect_mode()
    exit_select_mode()
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
    elif tool == 'select':
        select_blob(event.x , event.y)
    else:
        mode = 'drawing'
        drawStuff(event.x, event.y)
    logEvent('leftMouseDown-'+tool, event.x, event.y)


#handles mouse releases
def leftMouseUp(event):
    global lastX, lastY, tool, suggestToggle, suggestMode, protected_centroids
    if tool == 'protect':
        pass
    elif tool == 'select':
        reset_select_mode()
        # exit_select_mode()
    else:
        mode = 'idle'
        lastX = -1
        lastY = -1
        addUndoable()
        if suggestToggle != 0 and suggestMode != 0:
            updateSuggestion(SHORT_SEARCH)
    if tool == 'protect':
        logEvent('leftMouseUp-'+tool, event.x, event.y, protected_centroids)
    else:
        logEvent('leftMouseUp-'+tool, event.x, event.y)


#handles mouse dragging while clicked
def leftMouseMove(event):
    global tool
    if tool == 'protect':
        pass
    elif tool == 'select':
        move_selected(event.x,event.y)
    else:
        drawStuff(event.x, event.y)
    logEvent('leftMouseMove-'+tool, event.x, event.y)


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
    elif event.char == '/' or event.char == '?':
        toggleSuggest('keyboard')
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
        switchSuggestMode()
        # switchExpMode()
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
    updateSuggestionModePanel()
    updateVisualTargetPanel()
    logEvent('switchExpMode')


def switchSuggestMode():
    global suggestMode
    suggestMode = (suggestMode+1)%3
    updateSuggestion(SHORT_SEARCH)
    updateSuggestionModePanel()
    logEvent('switchSuggestionMode')


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

    #From original code
    # if expPhase == 2:
    #     drawCentroids = (drawCentroids + 1) % 2
    # elif expPhase == 3:
    #     drawCentroids = (drawCentroids + 1) % 3

    drawCentroids = (drawCentroids + 1) % 2
    updateEncodings()
    updateOrderPanel()
    logEvent(source + 'ToggleOrder')


def toggleSuggest(source='button'):
    global suggestToggle, suggestMode
    suggestToggle = (suggestToggle + 1) % 2
    if suggestToggle != 0 and suggestMode != 0:
        updateSuggestion(SHORT_SEARCH)
    else:
        updateEncodings()
    updateSuggestPanel()
    logEvent(source + 'ToggleSuggest')


#toggles the labelling overlay between parts, blobs, and off
#source indicates where the command came from (UI button or keyboard) for the purpose of logging
def toggleLabeller(source='button'):
    global markerMode, drawEncodings, expPhase
    #dtouch mode disabled in this version
    # if markerMode == 'dtouch':
    #     drawEncodings = (drawEncodings + 1) % 3
    # else:
    #     drawEncodings = (drawEncodings + 1) % 4

    #From original code
    # if expPhase == 1 or expPhase == 2 or expPhase == 3:
    #     drawEncodings = (drawEncodings + 1) % 3
    drawEncodings = (drawEncodings + 1) % 2
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
    global img, markedImg, suggestionTopString, globalLevels, mainRoot, protected_centroids
    exit_protect_mode()
    exit_select_mode()
    img = np.ones((CANVAS_HEIGHT, CANVAS_WIDTH, 3), np.uint8) * 255
    markedImg = img.copy()
    suggestionTopString = ""
    protected_centroids = []
    resetSuggestions()
    clearRootAndLevels()
    updateEncodings()
    addUndoable()
    logEvent(source + 'Clear')


#makes the brush a little bigger, up to a maximum
def growBrush(source='button'):
    global drawRadius
    exit_protect_mode()
    exit_select_mode()
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
    exit_select_mode()
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
    # if drawProtected:
    #     combined = protectImg.copy()
    #     marked_posns = np.where(markedImg != WHITE)
    #     combined[marked_posns[0],marked_posns[1]] = markedImg[marked_posns[0],marked_posns[1]]
    #     displayImg = cv2.cvtColor(combined, cv2.COLOR_BGR2RGB)
    # else:
    #     displayImg = cv2.cvtColor(markedImg, cv2.COLOR_BGR2RGB)
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
    exit_select_mode()
    drawRadius = 5
    drawColour = BLACK
    updateBrush()
    logEvent('smallBlackBrush')


#sets the brush to a preset colour/size combo
def medBlackBrush():
    global drawRadius, drawColour
    exit_protect_mode()
    exit_select_mode()
    drawRadius = 12
    drawColour = BLACK
    updateBrush()
    logEvent('medBlackBrush')


#sets the brush to a preset colour/size combo
def largeBlackBrush():
    global drawRadius, drawColour
    exit_protect_mode()
    exit_select_mode()
    drawRadius = 25
    drawColour = BLACK
    updateBrush()
    logEvent('largeBlackBrush')


#sets the brush to a preset colour/size combo (unused)
def smallGreyBrush():
    global drawRadius, drawColour
    exit_protect_mode()
    exit_select_mode()
    drawRadius = 5
    drawColour = GREY
    updateBrush()
    logEvent('smallGreyBush')


#sets the brush to a preset colour/size combo (unused)
def medGreyBrush():
    global drawRadius, drawColour
    exit_protect_mode()
    exit_select_mode()
    drawRadius = 12
    drawColour = GREY
    updateBrush()
    logEvent('medGreyBrush')


#sets the brush to a preset colour/size combo (unused)
def largeGreyBrush():
    global drawRadius, drawColour
    exit_protect_mode()
    exit_select_mode()
    drawRadius = 25
    drawColour = GREY
    updateBrush()
    logEvent('largeGreyBrush')


#sets the brush to a preset colour/size combo
def smallWhiteBrush():
    global drawRadius, drawColour
    exit_protect_mode()
    exit_select_mode()
    drawRadius = 5
    drawColour = WHITE
    updateBrush()
    logEvent('smallWhiteBrush')


#sets the brush to a preset colour/size combo
def medWhiteBrush():
    global drawRadius, drawColour
    exit_protect_mode()
    exit_select_mode()
    drawRadius = 12
    drawColour = WHITE
    updateBrush()
    logEvent('medWhiteBrush')


#sets the brush to a preset colour/size combo
def largeWhiteBrush():
    global drawRadius, drawColour
    exit_protect_mode()
    exit_select_mode()
    drawRadius = 25
    drawColour = WHITE
    updateBrush()
    logEvent('largeWhiteBrush')


#adds an event to the text log
#events have a name and up to 3 other values
def logEvent(eventName, x=-1, y=-1, z=-1):
    global logFile
    logString = str(datetime.datetime.now()) + ' ' + eventName + ' ' + str(x) + ' ' + str(y) + ' ' + str(z) + '\n'
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


def updateSuggestionModePanel():
    global suggestMode, suggestionModePanel
    newText = 'Suggestions: '
    if suggestMode == 0:
        newText += 'Off'
    elif suggestMode == 1:
        newText += 'Helper'
    else:
        newText += 'Auto-Complete'
    suggestionModePanel.configure(text=newText)


#updates the GUI element that displays the state of the labelling overlay
def updateLabellerPanel():
    global labellerPanel, drawEncodings, expPhase

    #From original code
    # if expPhase == 1:
    #     if drawEncodings == 0:
    #         newText = 'Off'
    #     elif drawEncodings == 1:
    #         newText = 'On'
    # elif expPhase == 2 or expPhase == 3:
    #     if drawEncodings == 0:
    #         newText = 'Off'
    #     elif drawEncodings == 1:
    #         newText = 'Part'
    #     elif drawEncodings == 2:
    #         newText = 'Blob'

    if drawEncodings == 0:
        newText = 'Off'
    elif drawEncodings == 1:
        newText = 'On'
    labellerPanel.configure(text=newText)


#updates the GUI element that displays the state of the ordering overlay
def updateOrderPanel():
    global orderPanel, drawCentroids, markerMode, expPhase
    newText = 'Off'

    #From original code
    # if drawCentroids != 0 and expPhase == 2:
    #     # if markerMode == 'dtouch' or drawCentroids == 2:
    #     newText = 'Blob'
    # elif expPhase == 3:
    #     if drawCentroids == 1:
    #         newText = 'Part'
    #     elif drawCentroids == 2:
    #         newText = 'Blob'

    if drawCentroids == 1:
        newText = 'On'
    orderPanel.configure(text=newText)


def updateSuggestPanel():
    global suggestPanel, suggestToggle
    newText = 'Off'
    if suggestToggle == 1:
        newText = 'On'
    suggestPanel.configure(text=newText)


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
    add_blob_tried_position = np.zeros((img.shape[0],img.shape[1]),np.uint8)
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
    currSuggestion = None
    recent_auto_changes = []
    protected_centroids = []
    blob_moved = False

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
    incBtn = Button(tkRoot, text="Inc", font=buttonTextFont, command=add_most_frequent_blob)#increase_blob)
    #incBtn.place(x=1285, y=300, width=50, height=50)

    decBtn = Button(tkRoot, text="Dec", font=buttonTextFont, command=join_blob_to_edge)
    #decBtn.place(x=1345, y=300, width=50, height=50)

    redprtBtn = Button(tkRoot, text="RedPart", font=buttonTextFont, command=reduce_part)
    #redprtBtn.place(x=1285, y=360, width=50, height=50)

    #and also some not Rahul's code
    fixBlobBtn = Button(tkRoot, text="Fix", font=buttonTextFont, command=auto_fix_blobs_btn, bg='orange')
    fixBlobBtn.place(x=1285, y=420, width=50, height=50)

    protectBtn = Button(tkRoot, text="Prot.", font=buttonTextFont, command=protect_btn, bg='yellow3')
    protectBtn.place(x=1345, y=420, width=50, height=50)

    selectBtn = Button(tkRoot, text="Sel.", font=buttonTextFont, command=select_blob_btn)
    selectBtn.place(x=1285, y=300, width=50, height=50)
    #selectBtn.place(x=1405, y=420, width=50, height=50)

    addRemovePrefScale = Scale(tkRoot, from_=-20, to=20, orient=HORIZONTAL, label='Prefer Removing or Adding Blobs')
    addRemovePrefScale.place(x=1270, y=480, width=200)
    addRemovePrefScale.bind("<ButtonRelease-1>", sliderRelease)
    ambPanel = Label(text="Removing           Neutral              Adding", font=sliderFont)
    ambPanel.place(x=1250, y=540, width=240, height=20)

    ######################################
    visualTargetPanel = None
    resetVTGuiElements()
    updateVisualTargetPanel()

    markerModePanel = Label(text="Mode: Sketch'n'code", font=buttonTextFont, anchor='w')
    markerModePanel.place(x=1260, y=650, width=200, height=40)
    updateMarkerModePanel()

    suggestionModePanel = Label(text="Suggestions: Off", font=buttonTextFont, anchor='w')
    suggestionModePanel.place(x=1260, y=610, width=240, height=40)
    updateSuggestionModePanel()

    labellerPanel = Label(text="Off", font=buttonTextFont)
    labellerPanel.place(x=1285, y=695, width=50, height=30)
    updateLabellerPanel()

    orderPanel = Label(text="Off", font=buttonTextFont)
    orderPanel.place(x=1345, y=695, width=50, height=30)
    updateOrderPanel()

    ambPanel = Label(text="Off", font=buttonTextFont)
    # ambPanel.place(x=1465, y=695, width=50, height=30)
    updateAmbPanel()

    suggestPanel = Label(text="Off", font=buttonTextFont)
    suggestPanel.place(x=1405, y=695, width=50, height=30)
    updateSuggestPanel()


    labellerBtn = Button(tkRoot, text="Label", font=buttonTextFont, command=toggleLabeller, bg="red")
    labellerBtn.place(x=1285, y=730, width=50, height=50)
    orderingBtn = Button(tkRoot, text="Order", font=buttonTextFont, command=toggleOrder, bg="cyan")
    orderingBtn.place(x=1345, y=730, width=50, height=50)
    ambBtn = Button(tkRoot, text="Ambig", font=buttonTextFont, command=toggleAmb, bg="orange")
    # ambBtn.place(x=1465, y=730, width=50, height=50)
    suggestBtn = Button(tkRoot, text="Sug.", font=buttonTextFont, command=toggleSuggest, bg="green")
    suggestBtn.place(x=1405, y=730, width=50, height=50)

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