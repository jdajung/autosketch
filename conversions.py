import math
import random

BASE_2_CHARS = "01"
BASE_10_CHARS = "0123456789"
BASE_36_CHARS = "0123456789abcdefghijklmnopqrstuvwxyz"

def validBase2String(string):
    ans = True
    for i in range(len(string)):
        if string[i] not in BASE_2_CHARS:
            ans = False
    return ans

def validBase10String(string):
    ans = True
    for i in range(len(string)):
        if string[i] not in BASE_10_CHARS:
            ans = False
    return ans

def validBase36String(string):
    ans = True
    for i in range(len(string)):
        if string[i] not in BASE_36_CHARS:
            ans = False
    return ans

def decToBase36String(decVal):
    outString = ""
    remaining = decVal
    while remaining > 0:
        currVal = remaining % 36
        outString = BASE_36_CHARS[currVal] + outString
        remaining /= 36
    return outString


def base36StringToDec(string):
    outVal = 0
    digitsRepresented = len(string)
    for i in range(len(string)):
        currChar = string[i]
        outVal += int(BASE_36_CHARS.index(currChar) * math.pow(36, digitsRepresented - i - 1))
    return outVal, digitsRepresented


def binaryStringToDec(string):
    outVal = 0
    digitsRepresented = len(string)
    for i in range(len(string)):
        currChar = string[i]
        outVal += int(int(currChar) * math.pow(2, digitsRepresented - i - 1))
    return outVal, digitsRepresented


def binaryString(encoding, bitsRepresented=-1):
    outString = ""
    if bitsRepresented == -1:
        while encoding > 0:
            outString = str(encoding % 2) + outString
            encoding /= 2
    else:
        for i in range(bitsRepresented):
            outString = str(encoding % 2) + outString
            encoding /= 2
    return outString

def rand36BitString(numBits):
    outString = ''
    for i in range(numBits):
        outString += (BASE_36_CHARS[random.randint(0,len(BASE_36_CHARS)-1)])
    return outString