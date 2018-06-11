import numpy as np
import math
import matplotlib.pyplot as plt
import cv2
import time
import sys
import requests
import webbrowser
import random
import statistics as stat

from helpers import imshow
from conversions import *


def findDividerPosns(binString):
    dividerPosns = []
    for i in range(len(binString)):
        if binString[i] == '1':
            dividerPosns.append(i)
    return dividerPosns


def divisionSum(binString, currDividers):
    runningSum = 0
    lastNum = 0
    for j in range(len(currDividers)):
        if j == len(currDividers) - 1:
            currNum = binString[currDividers[j]:]
        else:
            currNum = binString[currDividers[j]:currDividers[j + 1]]
        decNum = binaryStringToDec(currNum)[0]
        runningSum += decNum
        if decNum < lastNum:
            runningSum = -1
            break
        lastNum = decNum
    return runningSum


def partDivisionSum(binString, currDividers):
    runningSum = 0
    lastNum = 0
    for j in range(len(currDividers) - 1):
        currNum = binString[currDividers[j]:currDividers[j + 1]]
        decNum = binaryStringToDec(currNum)[0]
        runningSum += decNum
        if decNum < lastNum:
            runningSum = -1
            break
        lastNum = decNum
    return runningSum


def getQuartile(pairList, quartile):
    if quartile < 0 or quartile >= 4:
        print "ERROR: invalid quartile"
        return
    if len(pairList) < 4:
        print "ERROR: list too short"
        return

    quartileSize = len(pairList) / 4.0
    startPoint = int(round(quartile * quartileSize))
    endPoint = int(round((quartile + 1) * quartileSize))
    pairList.sort()
    return pairList[startPoint:endPoint]


def randomChoice(l):
    choice = random.randInt(0, len(l) - 1)
    return l[choice]


def bruteFindNumDtouchBlobs(encoding):
    binString = binaryString(encoding)
    dividerPosns = findDividerPosns(binString)

    lowVal = int(pow(2, (len(dividerPosns) - 1)))
    highVal = int(pow(2, len(dividerPosns)))
    bestSum = -1
    for i in range(lowVal, highVal):
        currDividers = []
        currPosn = len(dividerPosns) - 1
        while i > 0:
            if i % 2 > 0:
                currDividers = [dividerPosns[currPosn]] + currDividers
            currPosn -= 1
            i /= 2

        divSum = divisionSum(binString, currDividers)

        if divSum > 0 and (divSum < bestSum or bestSum == -1):
            bestSum = divSum
    return bestSum


def helper(binString, dividerPosns, currDividers, currPosn):
    global globalBestSum

    if currPosn == len(dividerPosns):
        currSum = divisionSum(binString, currDividers)
        if globalBestSum == -1 or currSum < globalBestSum:
            globalBestSum = currSum
        return currSum
    else:
        bestSum = -1

        # currPosn not used
        recSum = helper(binString, dividerPosns, currDividers, currPosn + 1)
        if recSum > 0:
            bestSum = recSum

        # currPosn used
        currDividers.append(dividerPosns[currPosn])
        partSum = partDivisionSum(binString, currDividers)
        if partSum != -1 or (globalBestSum != -1 and partSum >= globalBestSum):
            recSum = helper(binString, dividerPosns, currDividers, currPosn + 1)
            if recSum > 0 and (recSum < bestSum or bestSum == -1):
                bestSum = recSum
        del currDividers[-1]
        return bestSum


def bnbFindNumDtouchBlobs(encoding):
    global globalBestSum
    globalBestSum = -1
    binString = binaryString(encoding)
    dividerPosns = findDividerPosns(binString)
    bestSum = helper(binString, dividerPosns, dividerPosns[:1], 1)
    return bestSum

def genExhaustivePairs(numBinDigits):
    highVal = int(pow(2,numBinDigits))
    lowVal = int(pow(2,(numBinDigits-1)))
    samples = range(lowVal,highVal)
    sampleBlobs = [bnbFindNumDtouchBlobs(samples[i]) for i in range(len(samples))]
    pairList = [[sampleBlobs[i],samples[i]] for i in range(len(samples))]
    return pairList


if __name__ == "__main__":
    # 78364164095 = zzzzzzz in base 36
    maxVal = 78364164095
    numSamples = 1000

    samples = [random.randint(1, maxVal) for i in range(numSamples)]
    sampleBlobs = [bnbFindNumDtouchBlobs(samples[i]) for i in range(numSamples)]

    print samples
    print sampleBlobs
    print "Mean: " + str(stat.mean(sampleBlobs))
    print "Median: " + str(stat.median(sampleBlobs))
    print "Min: " + str(min(sampleBlobs))
    print "Max: " + str(max(sampleBlobs))

    plt.yscale('log')
    plt.plot(samples, sampleBlobs, 'o')
    plt.show()

    # # 78364164095 = zzzzzzz in base 36
    # maxVal = 78364164095
    # numSamples = 1000
    #
    # samples = range(2048, 4096)  # [random.randint(1,maxVal) for i in range(numSamples)]
    # sampleBlobs = [bnbFindNumDtouchBlobs(samples[i]) for i in range(len(samples))]
    #
    # print samples
    # print sampleBlobs
    # print "Mean: " + str(stat.mean(sampleBlobs))
    # print "Median: " + str(stat.median(sampleBlobs))
    # print "Min: " + str(min(sampleBlobs))
    # print "Max: " + str(max(sampleBlobs))
    #
    # plt.yscale('log')
    # plt.plot(samples, sampleBlobs, 'o')
    # plt.show()