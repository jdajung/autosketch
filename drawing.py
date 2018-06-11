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
# from application import getBlobImgList


def drawMarkerBlobs(levels, displayImage):
    if len(levels) >= 3:
        for marker in levels[2]:
            binString = binaryString(marker.encoding, marker.bitsRepresented)
            centroid = marker.centroid
            # cv2.circle(displayImage,centroid,2,(255,0,0),-1)
            cv2.putText(displayImage, binString, centroid, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)


def drawMarkerParts(levels, displayImage):
    if len(levels) >= 2:
        for marker in levels[1]:
            binString = binaryString(marker.encoding, marker.bitsRepresented)
            centroid = marker.centroid
            # cv2.circle(displayImage,centroid,2,(255,0,0),-1)
            cv2.putText(displayImage, str(binaryStringToDec(binString)[0]), centroid, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)



def drawMarkers(levels, displayImage):
    if len(levels) >= 1:
        for marker in levels[0]:
            binString = binaryString(marker.encoding)
            centroid = marker.centroid
            cv2.putText(displayImage, binString, centroid, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)


def drawBlobAreas(levels, displayImage, blobOrderMode, partOrderMode):
    if len(levels) >= 2:
        for root in levels[0]:
            partList = sortParts(root, partOrderMode)
            currNum = 1
            for part in partList:
                blobList = sortBlobs(part, blobOrderMode)
                # cv2.circle(displayImage, part.centroid, 3, (255, 255, 0), -1)
                # cv2.circle(displayImage, part.centroid, 4, (200, 200, 0), 2)
                blobNum = 1
                for blob in blobList:
                    cv2.circle(displayImage, blob.centroid, 3, (255, 255, 0), -1)
                    yTextVal = blob.centroid[1]-10
                    if yTextVal < 0:
                        yTextVal = 0
                    displayString = str(blobNum) + ' (' + str(int(blob.area/10.0)) + ')'
                    cv2.putText(displayImage, displayString, (blob.centroid[0],yTextVal), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 0), 2)
                    currNum += 1
                    blobNum += 1


def drawPartAreas(levels, displayImage, partOrderMode):
    if len(levels) >= 1:
        for root in levels[0]:
            partList = sortParts(root, partOrderMode)
            currNum = 1
            for part in partList:
                cv2.circle(displayImage, part.centroid, 3, (255, 255, 0), -1)
                yTextVal = part.centroid[1]-10
                if yTextVal < 0:
                    yTextVal = 0
                displayString = str(currNum) + ' (' + str(int(part.area/10.0)) + ')'
                cv2.putText(displayImage, displayString, (part.centroid[0],yTextVal), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 0), 2)
                currNum += 1


def drawBlobCentroidCircles(levels, displayImage, blobOrderMode, partOrderMode):
    if len(levels) >= 2:
        for root in levels[0]:
            partList = sortParts(root, partOrderMode)
            currNum = 1
            for part in partList:
                blobList = sortBlobs(part, blobOrderMode)
                cv2.circle(displayImage, part.centroid, 3, (255, 255, 0), -1)
                cv2.circle(displayImage, part.centroid, 4, (200, 200, 0), 2)
                blobNum = 1
                for blob in blobList:
                    radius = int(round(euclideanDist(part.centroid, blob.centroid)))
                    cv2.circle(displayImage, part.centroid, radius, (255, 255, 0), 1)
                    cv2.circle(displayImage, blob.centroid, 3, (255, 255, 0), -1)
                    yTextVal = blob.centroid[1]-10
                    if yTextVal < 0:
                        yTextVal = 0
                    cv2.putText(displayImage, str(blobNum), (blob.centroid[0],yTextVal), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 0), 2)
                    currNum += 1
                    blobNum += 1


def drawPartCentroidCircles(levels, displayImage, partOrderMode):
    if len(levels) >= 1:
        for root in levels[0]:
            cv2.circle(displayImage, root.centroid, 3, (255, 255, 0), -1)
            cv2.circle(displayImage, root.centroid, 4, (200, 200, 0), 2)
            partList = sortParts(root, partOrderMode)
            currNum = 1
            for part in partList:
                radius = int(round(euclideanDist(root.centroid, part.centroid)))
                cv2.circle(displayImage, root.centroid, radius, (255, 255, 0), 1)
                cv2.circle(displayImage, part.centroid, 3, (255, 255, 0), -1)
                yTextVal = part.centroid[1] - 10
                if yTextVal < 0:
                    yTextVal = 0
                cv2.putText(displayImage, str(currNum), (part.centroid[0], yTextVal), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 0), 2)
                currNum += 1


def drawDtouchOrdering(levels, displayImage):
    if len(levels) >= 1:
        for root in levels[0]:
            pairs = []
            for part in root.children:
                pairs.append([part.encoding, part.centroid])
            pairs.sort()

            orderPosn = 1
            for pair in pairs:
                if pair[0] > 0:
                    yTextVal = pair[1][1] - 15
                    if yTextVal < 0:
                        yTextVal = 0
                    cv2.putText(displayImage, (str(orderPosn) + " (" + str(pair[0]) + ")"),
                                (pair[1][0], yTextVal), \
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
                    orderPosn += 1


def drawAmbiguities(levels, displayImage, blobOrderMode, partOrderMode):
    ambiguousPairs = detectAmbiguity(levels, blobOrderMode, partOrderMode)
    for pair in ambiguousPairs:
        contours = [pair[0].contour, pair[1].contour]
        cv2.drawContours(displayImage, contours, -1, (0, 165, 255), 2)
        cv2.circle(displayImage, pair[0].centroid, 3, (0, 165, 255), -1)
        cv2.circle(displayImage, pair[1].centroid, 3, (0, 165, 255), -1)
        cv2.line(displayImage, pair[0].centroid, pair[1].centroid, (0, 165, 255), 2)


def drawSuggestion(suggestNum, suggestion, textPoint, levels, displayImage):
    if suggestion == None or suggestion == []:
        print "ERROR: suggestion empty or null"
        return
    if levels == None or levels == []:
        print "ERROR: levels empty or null"
        return
    if levels[0] == []:
        return

    root = levels[0][0]
    for i in range(1, len(levels[0])):
        if levels[0][i].area > root.area:
            root = levels[0][i]
    partStructure = getPartStructure(root)
    partIndex, blobIndex = findIndices(partStructure, suggestion[1])
    partList = sortParts(root)
    blobList = sortBlobs(partList[partIndex])
    printString = "Suggested Step " + str(suggestNum) + ": "
    convexityString = 'convex'
    colourString = 'black'
    if suggestion[2] % 2 == 1:
        colourString = 'non-black'
    if (suggestion[2] / 2) % 2 == 1:
        convexityString = 'concave'

    if suggestion[0] == 'insert':
        innerRadius = -1
        outerRadius = -1
        if blobIndex <= 0:
            innerRadius = 0
        else:
            innerRadius = blobList[blobIndex - 1].dist
        if blobIndex >= partStructure[partIndex]:
            outerRadius = innerRadius + 2 * AMBIGUITY_THRESHOLD
        else:
            outerRadius = blobList[blobIndex].dist
        desiredRadius = int(round(innerRadius + (outerRadius - innerRadius) / 2.0))
        cv2.circle(displayImage, partList[partIndex].centroid, 3, (0, 255, 0), -1)
        cv2.circle(displayImage, partList[partIndex].centroid, desiredRadius, (0, 255, 0), 2)
        printString += "Consider adding a blob at the highlighted radius that is " \
                       + convexityString + " and " + colourString + "."

    elif suggestion[0] == 'delete':
        selectedBlob = blobList[blobIndex]
        cv2.drawContours(displayImage, selectedBlob.contour, -1, (0, 255, 0), 2)
        printString += "Consider removing the highlighted blob."

    elif suggestion[0] == 'substitute':
        selectedBlob = blobList[blobIndex]
        cv2.drawContours(displayImage, selectedBlob.contour, -1, (0, 255, 0), 2)
        printString += "Consider changing the highlighted blob to one that is " \
                       + convexityString + " and " + colourString + "."
    else:
        print "ERROR: type not recognized in drawSuggestion"

    cv2.putText(displayImage, printString, textPoint, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)


def printSuggestion(suggestNum, suggestion, levels, displayImage):
    if suggestion == None or suggestion == []:
        print "ERROR: suggestion empty or null"
        return
    if levels == None or levels == []:
        print "ERROR: levels empty or null"
        return
    if levels[0] == []:
        return

    root = levels[0][0]
    for i in range(1, len(levels[0])):
        if levels[0][i].area > root.area:
            root = levels[0][i]
    partStructure = getPartStructure(root)
    partIndex, blobIndex = findIndices(partStructure, suggestion[1])
    partList = sortParts(root)
    blobList = sortBlobs(partList[partIndex])
    printString = "Suggested Step " + str(suggestNum) + ":\n"
    convexityString = 'convex'
    colourString = 'black'
    if suggestion[2] % 2 == 1:
        colourString = 'non-black'
    if (suggestion[2] / 2) % 2 == 1:
        convexityString = 'concave'

    if suggestion[0] == 'insert':
        innerRadius = -1
        outerRadius = -1
        if blobIndex <= 0:
            innerRadius = 0
        else:
            innerRadius = blobList[blobIndex - 1].dist
        if blobIndex >= partStructure[partIndex]:
            outerRadius = innerRadius + 2 * AMBIGUITY_THRESHOLD
        else:
            outerRadius = blobList[blobIndex].dist
        desiredRadius = int(round(innerRadius + (outerRadius - innerRadius) / 2.0))
        printString += "Consider adding a blob at the highlighted radius that is " \
                       + convexityString + " and " + colourString + ".\n"

    elif suggestion[0] == 'delete':
        selectedBlob = blobList[blobIndex]
        printString += "Consider removing the highlighted blob.\n"

    elif suggestion[0] == 'substitute':
        selectedBlob = blobList[blobIndex]
        printString += "Consider changing the highlighted blob to one that is " \
                       + convexityString + " and " + colourString + ".\n"
    else:
        print "ERROR: type not recognized in printSuggestion"

    print printString


def drawTarget(root, targetBinString, writePosn, displayImage):
    if root == None:
        currBinString = ""
    else:
        currBinString = binaryString(root.encoding, root.bitsRepresented)
    if len(targetBinString) % 2 == 1:
        targetBinString = '0' + targetBinString
    bigSkip = False
    currPosn = writePosn

    for i in range(len(targetBinString)):
        currColour = (0, 255, 0)
        if i >= len(currBinString) or currBinString[i] != targetBinString[i]:
            currColour = (0, 0, 255)
        cv2.putText(displayImage, targetBinString[i], currPosn, cv2.FONT_HERSHEY_SIMPLEX, 0.5, currColour, 2)
        if targetBinString[i] == '0':
            currPosn = (currPosn[0] + ZERO_PIXELS, currPosn[1])
        else:
            currPosn = (currPosn[0] + ONE_PIXELS, currPosn[1])
        if bigSkip:
            currPosn = (currPosn[0] + SPACE_PIXELS, currPosn[1])
        bigSkip = not bigSkip

    if len(currBinString) > len(targetBinString):
        if bigSkip:
            currPosn = (currPosn[0] + SPACE_PIXELS, currPosn[1])
        cv2.putText(displayImage, '...', currPosn, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)