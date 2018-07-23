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

CONTOUR_AREA_THRESHOLD = 10
APPROX_POLY_FACTOR = 0.025
CLOSER_PIXELS = 1  # number of pixels away from contour boundary to check for colour
BITS_PER_BLOB = 2
WHITE_ABOVE = 120  # 120
BLACK_BELOW = 50  # 70
AMBIGUITY_THRESHOLD = 10
AMBIGUITY_PERCENT = 0.1
A_LARGE_NUMBER = 1000000000.0
ZERO_PIXELS = 11
ONE_PIXELS = 8
SPACE_PIXELS = 8

COLOUR = {}
COLOUR['none'] = -1
COLOUR['white'] = 0
COLOUR['black'] = 1
COLOUR['grey'] = 2


class Component:
    def __init__(self, cNum, contour, parent, level, img):
        self.cNum = cNum
        self.contour = contour
        self.parent = parent
        self.level = level
        self.approx = cv2.approxPolyDP(contour, APPROX_POLY_FACTOR * cv2.arcLength(contour, True), True)
        self.box = None
        self.select_points = None
        self.convex = cv2.isContourConvex(self.approx)
        self.area = cv2.contourArea(contour)
        self.centroid = getCentroid(contour)
        if not parent == None:
            self.dist = euclideanDist(self.centroid, parent.centroid)
        else:
            self.dist = -1
        self.colour = colourVote(contour, self.centroid, img)
        self.children = []
        self.encoding = sys.maxint
        self.encChunks = []
        self.bitsRepresented = -1
        self.protected = False

    def __str__(self):
        return "L: " + str(self.level) + ", #" + str(self.cNum) + " " + binaryString(self.encoding,
                                                                                     self.bitsRepresented)


def getCentroid(contour):
    M = cv2.moments(contour)
    cx = int(M['m10'] / M['m00'])
    cy = int(M['m01'] / M['m00'])
    return (cx, cy)


def euclideanDist(p1, p2):
    sum = 0.0
    for i in range(len(p1)):
        sum += math.pow(p1[i] - p2[i], 2)
    return math.sqrt(sum)


def closerPoint(pnt, centroid):
    new_point = [pnt[0], pnt[1]]
    xSign = np.sign(centroid[0] - pnt[0])
    ySign = np.sign(centroid[1] - pnt[1])
    new_point[0] += xSign * CLOSER_PIXELS
    new_point[1] += ySign * CLOSER_PIXELS
    return (new_point[0], new_point[1])


# TODO: add detection for colours
def findColour(pixel):
    if isinstance(pixel, int):
        if pixel < BLACK_BELOW:
            return COLOUR['black']
        elif pixel > WHITE_ABOVE:
            return COLOUR['white']
        else:
            return COLOUR['grey']
    elif isinstance(pixel, np.ndarray) or isinstance(pixel, list):
        if pixel[0] < BLACK_BELOW:
            return COLOUR['black']
        elif pixel[0] > WHITE_ABOVE:
            return COLOUR['white']
        else:
            return COLOUR['grey']
    else:
        print "ERROR: pixel type not recognized"


def colourVote(contour, centroid, img):
    votes = {}
    points = contour[0]
    mostVotes = -1
    votedColour = COLOUR['none']

    for p in points:
        closerP = closerPoint(p, centroid)
        x = closerP[0]
        y = closerP[1]
        if y >= len(img):
            y = len(img) - 1
        if x >= len(img[0]):
            x = len(img[0]) - 1
        pixel = img[y][x]
        currVote = findColour(pixel)
        if currVote not in votes:
            votes[currVote] = 0
        votes[currVote] += 1

    for col in votes:
        if votes[col] > mostVotes:
            mostVotes = votes[col]
            votedColour = col

    return votedColour


def sortParts(root, partOrderMode):
    children = root.children
    numChildren = len(children)

    if partOrderMode == 'distance':
        sortList = [[children[i], children[i].dist] for i in range(numChildren)]
    elif partOrderMode == 'area':
        sortList = [[children[i], children[i].area] for i in range(numChildren)]
    else:
        print "ERROR: Unrecognized partOrderMode passed to sortParts"

    # sortList = [[children[i], len(children[i].children), children[i].dist] for i in range(numChildren)]
    # sortList.sort(key=lambda x: x[1] + float(x[2]) / A_LARGE_NUMBER)
    sortList.sort(key=lambda x: x[1])
    sortedParts = [sortList[i][0] for i in range(numChildren)]
    return sortedParts


def sortBlobs(part, blobOrderMode):
    children = part.children
    numChildren = len(children)

    if blobOrderMode == 'distance':
        sortList = [[children[i], children[i].dist] for i in range(numChildren)]
    elif blobOrderMode == 'area':
        sortList = [[children[i], children[i].area] for i in range(numChildren)]
    else:
        print "ERROR: Unrecognized blobOrderMode passed to sortBlobs"

    sortList.sort(key=lambda x: x[1])
    sortedBlobs = [sortList[i][0] for i in range(numChildren)]
    return sortedBlobs


def mergeEncodings(comps):
    encoding = 0
    for i in range(len(comps)):
        currComp = comps[i]
        encoding *= math.pow(2, currComp.bitsRepresented)
        encoding += currComp.encoding
    return int(encoding)


def determineExpEncoding(comp, expPhase, blobMode, blobOrderMode, partOrderMode):
    if expPhase == 1: #or ((expPhase == 2 or expPhase == 3) and blobMode == 'number'):
        if blobMode == "number":
            if comp.level == 1:
                comp.encoding = len(comp.children)
                if comp.encoding == 0:
                    comp.bitsRepresented = 1
                else:
                    comp.bitsRepresented = int(math.ceil(math.log((comp.encoding + 1), 2)))
            elif comp.level == 0:
                childEncodings = []
                bitsRepresented = 0
                encodingString = ""
                for child in comp.children:
                    determineExpEncoding(child, expPhase, blobMode, blobOrderMode, partOrderMode)
                    childEncodings.append(child.encoding)
                    bitsRepresented += child.bitsRepresented
                childEncodings.sort()

                for enc in childEncodings:
                    encodingString += binaryString(enc)
                comp.encoding = binaryStringToDec(encodingString)[0]
                comp.encChunks = childEncodings
                comp.bitsRepresented = bitsRepresented

        elif blobMode == "convexity":
            if comp.level == 2:
                convexityBit = 0
                if not comp.convex:
                    convexityBit = 1
                comp.encoding = convexityBit
                comp.bitsRepresented = 1
            else:
                repSum = 0
                for child in comp.children:
                    determineExpEncoding(child, expPhase, blobMode, blobOrderMode, partOrderMode)
                    repSum += child.bitsRepresented
                comp.bitsRepresented = repSum
                # if comp.level == 1:
                #     sortedChildren = sortBlobs(comp, blobOrderMode)
                # else:
                #     sortedChildren = sortParts(comp, partOrderMode)
                # comp.encoding = mergeEncodings(sortedChildren)
                if comp.level == 1:
                    comp.encChunks = [child.encoding for child in comp.children]
                else:
                    for child in comp.children:
                        comp.encChunks = comp.encChunks + child.encChunks
                comp.encChunks.sort()

        elif blobMode == "hollow":
            if comp.level == 2:
                hollowBit = 0
                if len(comp.children) > 0:
                    hollowBit = 1
                comp.encoding = hollowBit
                comp.bitsRepresented = 1
            else:
                repSum = 0
                for child in comp.children:
                    determineExpEncoding(child, expPhase, blobMode, blobOrderMode, partOrderMode)
                    repSum += child.bitsRepresented
                comp.bitsRepresented = repSum
                # if comp.level == 1:
                #     sortedChildren = sortBlobs(comp, blobOrderMode)
                # else:
                #     sortedChildren = sortParts(comp, partOrderMode)
                # comp.encoding = mergeEncodings(sortedChildren)
                if comp.level == 1:
                    comp.encChunks = [child.encoding for child in comp.children]
                else:
                    for child in comp.children:
                        comp.encChunks = comp.encChunks + child.encChunks
                comp.encChunks.sort()

        elif blobMode == "convexityHollow":
            if comp.level == 2:
                hollowBit = 0
                convexityBit = 0
                if len(comp.children) > 0:
                    hollowBit = 1
                if not comp.convex:
                    convexityBit = 1
                comp.encoding = 1 * hollowBit + 2 * convexityBit
                comp.bitsRepresented = 2
            else:
                repSum = 0
                for child in comp.children:
                    determineExpEncoding(child, expPhase, blobMode, blobOrderMode, partOrderMode)
                    repSum += child.bitsRepresented
                comp.bitsRepresented = repSum
                # if comp.level == 1:
                #     sortedChildren = sortBlobs(comp, blobOrderMode)
                # else:
                #     sortedChildren = sortParts(comp, partOrderMode)
                # comp.encoding = mergeEncodings(sortedChildren)
                if comp.level == 1:
                    comp.encChunks = [child.encoding for child in comp.children]
                else:
                    for child in comp.children:
                        comp.encChunks = comp.encChunks + child.encChunks
                comp.encChunks.sort()

    elif expPhase == 2 or expPhase == 3:
        if blobMode == "number":
            if comp.level == 1:
                comp.encoding = len(comp.children)
                if comp.encoding == 0:
                    comp.bitsRepresented = 1
                else:
                    comp.bitsRepresented = int(math.ceil(math.log((comp.encoding + 1), 2)))
            elif comp.level == 0:
                bitsRepresented = 0
                encodingString = ""
                for child in comp.children:
                    determineExpEncoding(child, expPhase, blobMode, blobOrderMode, partOrderMode)
                    bitsRepresented += child.bitsRepresented

                sortedChildren = sortParts(comp, partOrderMode)
                comp.encoding = mergeEncodings(sortedChildren)
                comp.encChunks = [child.encoding for child in comp.children]
                comp.bitsRepresented = bitsRepresented

        elif blobMode == "hollow":
            if comp.level == 2:
                hollowBit = 0
                if len(comp.children) > 0:
                    hollowBit = 1
                comp.encoding = hollowBit
                comp.bitsRepresented = 1
            else:
                repSum = 0
                for child in comp.children:
                    determineExpEncoding(child, expPhase, blobMode, blobOrderMode, partOrderMode)
                    repSum += child.bitsRepresented
                comp.bitsRepresented = repSum

                if comp.level == 1:
                    sortedChildren = sortBlobs(comp, blobOrderMode)
                    comp.encoding = mergeEncodings(sortedChildren)
                elif comp.level == 0:
                    sortedChildren = sortParts(comp, partOrderMode)
                    comp.encoding = mergeEncodings(sortedChildren)

                # if comp.level == 0:
                #     comp.encChunks = [binaryString(child.encoding, child.bitsRepresented) for child in comp.children]
                # comp.encChunks.sort(key = len)

        elif blobMode == 'convexityHollow':
            if comp.level == 2:
                hollowBit = 0
                convexityBit = 0
                if len(comp.children) > 0:
                    hollowBit = 1
                if not comp.convex:
                    convexityBit = 1
                comp.encoding = 1 * hollowBit + 2 * convexityBit
                comp.bitsRepresented = 2
            else:
                repSum = 0
                for child in comp.children:
                    determineExpEncoding(child, expPhase, blobMode, blobOrderMode, partOrderMode)
                    repSum += child.bitsRepresented
                comp.bitsRepresented = repSum
                if comp.level == 1:
                    sortedChildren = sortBlobs(comp, blobOrderMode)
                    comp.encoding = mergeEncodings(sortedChildren)
                elif comp.level == 0:
                    sortedChildren = sortParts(comp, partOrderMode)
                    comp.encoding = mergeEncodings(sortedChildren)

                # if comp.level == 0:
                #     comp.encChunks = [binaryString(child.encoding, child.bitsRepresented) for child in comp.children]
                # # else:
                # #     for child in comp.children:
                # #         comp.encChunks = comp.encChunks + child.encChunks
                # comp.encChunks.sort(key = len)

        if expPhase == 1 or expPhase == 2:
            if comp.level == 0:
                comp.encChunks = []
                for child in comp.children:
                    childBitString = binaryString(child.encoding, child.bitsRepresented)
                    if childBitString != '':
                        comp.encChunks.append(childBitString)
                # comp.encChunks = [binaryString(child.encoding, child.bitsRepresented) for child in comp.children]
            comp.encChunks.sort(key=len)
        elif expPhase == 3 and blobMode != 'number':
            sortedChildren = sortParts(comp, partOrderMode)
            if comp.level == 0:
                comp.encChunks = []
                for child in sortedChildren:
                    childBitString = binaryString(child.encoding, child.bitsRepresented)
                    if childBitString != '':
                        comp.encChunks.append(childBitString)

    else:
        print "ERROR: Unrecognized Experimental Phase in determineExpEncoding"


# def determineEncoding(comp):
#     if comp.level == 2:
#         convexityBit = 0
#         colourBit = 0
#         if not comp.convex:
#             convexityBit = 1
#         if comp.colour == COLOUR['grey']:
#             colourBit = 1
#         comp.encoding = 1 * colourBit + 2 * convexityBit
#         comp.bitsRepresented = BITS_PER_BLOB
#     else:
#         repSum = 0
#         for child in comp.children:
#             determineEncoding(child)
#             repSum += child.bitsRepresented
#         comp.bitsRepresented = repSum
#         if comp.level == 1:
#             sortedChildren = sortBlobs(comp)
#         else:
#             sortedChildren = sortParts(comp)
#         comp.encoding = mergeEncodings(sortedChildren)
#
#
# def determineDtouchEncoding(comp):
#     if comp.level == 1:
#         comp.encoding = len(comp.children)
#         if comp.encoding <= 0:
#             comp.bitsRepresented = 0
#         else:
#             comp.bitsRepresented = int(math.ceil(math.log((comp.encoding + 1), 2)))
#     elif comp.level == 0:
#         childEncodings = []
#         bitsRepresented = 0
#         encodingString = ""
#         for child in comp.children:
#             determineDtouchEncoding(child)
#             childEncodings.append(child.encoding)
#             bitsRepresented += child.bitsRepresented
#         childEncodings.sort()
#
#         for enc in childEncodings:
#             encodingString += binaryString(enc)
#         comp.encoding = binaryStringToDec(encodingString)[0]
#         comp.bitsRepresented = bitsRepresented


def detectAmbiguity(levels, blobOrderMode, partOrderMode):
    ambiguousPairs = []
    if len(levels) >= 2:
        for part in levels[1]:
            blobs = sortBlobs(part, blobOrderMode)
            for i in range(len(blobs) - 1):
                currBlob = blobs[i]
                j = i + 1
                outOfRange = False
                while currBlob.bitsRepresented > 0 and j < len(blobs) and not outOfRange:
                    nextBlob = blobs[i + 1]
                    if blobOrderMode == 'distance':
                        absDif = abs(currBlob.dist - nextBlob.dist)
                        percentDif = float(absDif) / min(currBlob.dist, nextBlob.dist)
                        if percentDif < AMBIGUITY_PERCENT or absDif < AMBIGUITY_THRESHOLD:
                            if currBlob.encoding != nextBlob.encoding and nextBlob.bitsRepresented > 0:
                                ambiguousPairs.append([currBlob, nextBlob])
                        else:
                            outOfRange = True
                    elif blobOrderMode == 'area':
                        absDif = abs(currBlob.area - nextBlob.area)
                        percentDif = float(absDif) / min(currBlob.area, nextBlob.area)
                        if percentDif < AMBIGUITY_PERCENT or absDif < AMBIGUITY_THRESHOLD*10:
                            if currBlob.encoding != nextBlob.encoding and nextBlob.bitsRepresented > 0:
                                ambiguousPairs.append([currBlob, nextBlob])
                        else:
                            outOfRange = True
                    j += 1

    if len(levels) >= 1:
        for root in levels[0]:
            parts = sortParts(root, partOrderMode)
            for i in range(len(parts) - 1):
                currPart = parts[i]
                j = i+1
                outOfRange = False
                while currPart.bitsRepresented > 0 and j < len(parts) and not outOfRange:
                    nextPart = parts[j]
                    # if currPart.encoding != nextPart.encoding and len(currPart.children) == len(nextPart.children) \
                    #         and abs(currPart.dist - nextPart.dist) < AMBIGUITY_THRESHOLD:
                    #     ambiguousPairs.append([currPart, nextPart])
                    if partOrderMode == 'distance':
                        absDif = abs(currPart.dist - nextPart.dist)
                        percentDif = float(absDif) / min(currPart.dist, nextPart.dist)
                        if percentDif < AMBIGUITY_PERCENT or absDif < AMBIGUITY_THRESHOLD:
                            if (currPart.encoding != nextPart.encoding or currPart.bitsRepresented != nextPart.bitsRepresented)\
                                    and nextPart.bitsRepresented > 0:
                                ambiguousPairs.append([currPart, nextPart])
                        else:
                            outOfRange = True
                    elif partOrderMode == 'area':
                        absDif = abs(currPart.area - nextPart.area)
                        percentDif = float(absDif) / min(currPart.area, nextPart.area)
                        if percentDif < AMBIGUITY_PERCENT or absDif < AMBIGUITY_THRESHOLD*10:
                            if (currPart.encoding != nextPart.encoding or currPart.bitsRepresented != nextPart.bitsRepresented)\
                                    and nextPart.bitsRepresented > 0:
                                ambiguousPairs.append([currPart, nextPart])
                        else:
                            outOfRange = True
                    j += 1
    return ambiguousPairs


def findEncList(encoding, bitsRepresented=-1):
    returnList = []
    listElemSize = int(math.pow(2, BITS_PER_BLOB))
    if bitsRepresented == -1:
        while encoding > 0:
            returnList = [encoding % listElemSize] + returnList
            encoding /= listElemSize
    else:
        for i in range(bitsRepresented / BITS_PER_BLOB):
            returnList = [encoding % listElemSize] + returnList
            encoding /= listElemSize
    return returnList


def getPartStructure(root):
    partList = sortParts(root)
    returnList = [len(partList[i].children) for i in range(len(partList))]
    return returnList


def canChangeOrder(partStructure, opType, encodingPosn):
    partIndex, blobIndex = findIndices(partStructure, encodingPosn)
    answer = False

    if opType == 'insert':
        # if partIndex - 1 >= 0:
        #    diff = partStructure[partIndex] - partStructure[partIndex-1]
        #    if diff == 0 and partStructure[partIndex] != 0:
        #        answer = True
        if partIndex + 1 < len(partStructure):
            diff = partStructure[partIndex + 1] - partStructure[partIndex]
            if diff == 0 or diff == 1:
                answer = True

    elif opType == 'delete':
        if partIndex - 1 >= 0:
            diff = partStructure[partIndex] - partStructure[partIndex - 1]
            if diff == 0 or diff == 1:
                answer = True
                # if partIndex + 1 < len(partStructure):
                #    diff = partStructure[partIndex+1] - partStructure[partIndex]
                #    if diff == 0:
                #        answer = True

    elif opType == 'substitute':
        pass
    else:
        print "ERROR: opType not recognized in canChangeOrder"
    return answer


def findIndices(partStructure, encodingPosn):
    partIndex = 0
    blobIndex = 0
    posnSoFar = 0
    stopLoop = False

    while not stopLoop:
        if (posnSoFar + partStructure[partIndex] > encodingPosn):
            blobIndex = encodingPosn - posnSoFar
            stopLoop = True
        else:
            posnSoFar += partStructure[partIndex]
            partIndex += 1
            if partIndex >= len(partStructure):
                partIndex = len(partStructure) - 1
                blobIndex = partStructure[partIndex]
                stopLoop = True
    return partIndex, blobIndex


def numDifferent(currEncList, targetEncList):
    numDif = 0
    i = 0
    while i < len(currEncList) and i < len(targetEncList):
        if currEncList[i] != targetEncList[i]:
            numDif += 1
        i += 1
    if i < len(currEncList):
        numDif += len(currEncList) - i
    if i < len(targetEncList):
        numDif += len(targetEncList) - i
    return numDif


def tryInsertions(currEncList, targetEncList, partStructure):
    bestSuggestion = []
    bestScore = sys.maxint
    numBlobVals = int(math.pow(2, BITS_PER_BLOB))
    for i in range(len(currEncList) + 1):
        if not canChangeOrder(partStructure, 'insert', i):
            for j in range(numBlobVals):
                tryList = currEncList[0:i] + [j] + currEncList[i:]
                tryScore = numDifferent(tryList, targetEncList)
                if tryScore <= bestScore:
                    bestSuggestion = ['insert', i, j, tryList]
                    bestScore = tryScore
    return bestSuggestion


def tryDeletions(currEncList, targetEncList, partStructure):
    bestSuggestion = []
    bestScore = sys.maxint
    numBlobVals = int(math.pow(2, BITS_PER_BLOB))
    for i in range(len(currEncList)):
        if not canChangeOrder(partStructure, 'delete', i):
            removedVal = currEncList[i]
            tryList = currEncList[0:i] + currEncList[(i + 1):]
            tryScore = numDifferent(tryList, targetEncList)
            if tryScore <= bestScore:
                bestSuggestion = ['delete', i, removedVal, tryList]
                bestScore = tryScore
    return bestSuggestion


def trySubstitutions(currEncList, targetEncList, partStructure):
    bestSuggestion = []
    bestScore = sys.maxint
    numBlobVals = int(math.pow(2, BITS_PER_BLOB))
    for i in range(len(currEncList)):
        if not canChangeOrder(partStructure, 'substitute', i):
            for j in range(numBlobVals):
                tryList = currEncList[0:i] + [j] + currEncList[(i + 1):]
                tryScore = numDifferent(tryList, targetEncList)
                if tryScore < bestScore:
                    bestSuggestion = ['substitute', i, j, tryList]
                    bestScore = tryScore
    return bestSuggestion


def findSuggestions(root, targetEncoding):
    suggestions = []
    if root.encoding == sys.maxint:
        determineEncoding(root)
    currEncoding = root.encoding
    currEncList = findEncList(currEncoding, root.bitsRepresented)
    targetEncList = findEncList(targetEncoding)
    partStructure = getPartStructure(root)

    while currEncList != targetEncList:
        if len(currEncList) < len(targetEncList):
            currSuggestion = tryInsertions(currEncList, targetEncList, partStructure)
            partIndex, blobIndex = findIndices(partStructure, currSuggestion[1])
            partStructure[partIndex] += 1
        elif len(currEncList) > len(targetEncList):
            currSuggestion = tryDeletions(currEncList, targetEncList, partStructure)
            partIndex, blobIndex = findIndices(partStructure, currSuggestion[1])
            partStructure[partIndex] -= 1
        else:
            currSuggestion = trySubstitutions(currEncList, targetEncList, partStructure)
        suggestions.append(currSuggestion)
        currEncList = currSuggestion[3]

    return suggestions


def addContour(contours, hierarchy, levels, cNum, parent, currLevel, img):
    cont = contours[cNum]
    newComponent = None

    if cv2.contourArea(cont) > CONTOUR_AREA_THRESHOLD:
        newComponent = Component(cNum, cont, parent, currLevel, img)

        if len(levels) <= currLevel:
            levels.append([])
        levels[currLevel].append(newComponent)

        currChild = hierarchy[0][cNum][2]
        while currChild != -1:
            newChild = addContour(contours, hierarchy, levels, currChild, newComponent, currLevel + 1, img)
            if newChild != None:
                newComponent.children.append(newChild)
            currChild = hierarchy[0][currChild][0]

    return newComponent


def printLevels(levels):
    for i in range(len(levels)):
        print "Level " + str(i) + ":"
        for comp in levels[i]:
            print comp
        print "\n"


def genLevels(img, expPhase, blobMode, blobOrderMode, partOrderMode):
    levels = [[]]  # [[] for i in range(3)]

    # mask for everything not white
    mask = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # ret, mask = cv2.threshold(mask, WHITE_ABOVE, 255, cv2.THRESH_BINARY_INV)
    ret, mask = cv2.threshold(mask, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, None, iterations=1)
    #cv2.imshow('Mask', mask)
    # find contours
    mask, contours, hierarchy = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    for c in range(len(contours)):
        if hierarchy[0][c][3] == -1:
            addContour(contours, hierarchy, levels, c, None, 0, img)

    for root in levels[0]:
        determineExpEncoding(root, expPhase, blobMode, blobOrderMode, partOrderMode)
        # if mode == 'dtouch':
        #     determineDtouchEncoding(root)
        # else:
        #     determineEncoding(root)


    # printLevels(levels)

    # for i in range(len(contours)):
    #    cv2.drawContours(img, contours, i, (0,255,0), 2)
    #    imshow(img)
    # cv2.drawContours(img, contours, -1, (0,255,0), 2)

    # imshow(img)
    # imshow(mask)
    return levels