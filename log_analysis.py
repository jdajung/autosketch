import os
import shutil
import numpy as np
import scipy.stats as stats
import conversions
from datetime import datetime
from datetime import timedelta
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from statsmodels.stats.multicomp import MultiComparison
from statsmodels.stats.libqsturng import psturng

SESSION_PATHS = []
SURVEY_PATHS = []
SESSION_PATHS.append("C:/Users/j35jung/Documents/OpenCVWork/sketchncode/phase_1_sessions")
SURVEY_PATHS.append("C:/Users/j35jung/Documents/OpenCVWork/sketchncode/phase1_full.txt")
SESSION_PATHS.append("C:/Users/j35jung/Documents/OpenCVWork/sketchncode/phase_2_sessions")
SURVEY_PATHS.append("C:/Users/j35jung/Documents/OpenCVWork/sketchncode/phase2_full.txt")
SESSION_PATHS.append("C:/Users/j35jung/Documents/OpenCVWork/sketchncode/phase_3_sessions")
SURVEY_PATHS.append("C:/Users/j35jung/Documents/OpenCVWork/sketchncode/phase3_full.txt")
SORTED_IMAGE_PATH = "C:/Users/j35jung/Documents/OpenCVWork/sketchncode/sorted_images"

NUM_METHODS = [4,5,5]
NUM_LABEL_STATES = [2,3,3]
NUM_ORDER_STATES = [0,2,3]
NUM_PARTICIPANTS = 16
OBVIOUS_SENTINEL = -9999999
CONDITION_NAMES = [['Number', 'Convexity', 'Hollow', 'Dual'],
                   ['Number', 'Hollow/Area', 'Hollow/Dist', 'Dual/Area', 'Dual/Dist'],
                   ['Number/Area', 'Number/Dist', 'Hollow/Area/Area', 'Hollow/Dist/Area', 'Hollow/Dist/Dist']]
CONDITION_IDS = [(0,0),(0,1),(0,2),(0,3),(1,0),(1,1),(1,2),(1,3),(1,4),(2,0),(2,1),(2,2),(2,3),(2,4)]
DIGITS = 2

sessions = [[] for i in range(3)]
conditions = {}
participants = {}


class SessionInfo():
    def __init__(self, id):
        self.id = id
        self.events = []

    def __str__(self):
        return 'Session ' + str(self.id) + ' events: ' + str(self.events)


class ParticipantInfo():
    def __init__(self):
        self.id = -1
        self.order = ['' for i in range(3)]
        self.tenBitUnderstanding = [[] for i in range(3)]
        self.tenBitExpression = [[] for i in range(3)]
        self.twentyBitUnderstanding = [[] for i in range(3)]
        self.twentyBitExpression = [[] for i in range(3)]
        self.imagineRanking = [[] for i in range(3)]
        self.presentRanking = [[] for i in range(3)]
        self.toolRating = OBVIOUS_SENTINEL
        self.paperRating = []
        self.comments = ['' for i in range(3)]

    def __str__(self):
        return str(self.id) + '\n' + str(self.order) + '\n' + str(self.tenBitUnderstanding) + '\n' + \
            str(self.tenBitExpression) + '\n' + str(self.twentyBitUnderstanding) + '\n' + str(self.twentyBitExpression) + '\n' + \
            str(self.imagineRanking) + '\n' + str(self.presentRanking) + '\n' + str(self.toolRating) + '\n' + \
            str(self.paperRating) + '\n' + self.comments[0] + '\n' + self.comments[1] + '\n' + self.comments[2] + '\n'


class ConditionInfo():
    def __init__(self):
        self.id = None
        self.name = ''
        self.tenBitUnderstanding = []
        self.tenBitExpression = []
        self.twentyBitUnderstanding = []
        self.twentyBitExpression = []
        self.imagineRanking = []
        self.presentRanking = []

    def __str__(self):
        return str(self.id) + '\n' + self.name + '\n' + str(self.tenBitUnderstanding) + '\n' + str(self.tenBitExpression) + '\n' + \
            str(self.twentyBitUnderstanding) + '\n' + str(self.twentyBitExpression) + '\n' + str(self.imagineRanking) + '\n' + \
            str(self.presentRanking) + '\n'


# def condIndexToID(phase, number):
#     return 'p' + str(phase + 1) + '-' + str(number)

def pNumToID(participantNum):
    return int(participantNum[1:]) - 1

def IDToPNum(participantID):
    return 'p' + str(participantID + 1)


def initConditions():
    global conditions
    for i in range(3):
        for j in range(NUM_METHODS[i]):
            currCondition = ConditionInfo()
            currCondition.id = (i, j) #condIndexToID(i, j)
            currCondition.name = CONDITION_NAMES[i][j]
            # currCondition.index = j
            conditions[currCondition.id] = currCondition

def initParticipants():
    global participants
    for i in range(NUM_PARTICIPANTS):
        currParticipant = ParticipantInfo()
        currParticipant.id = i
        participants[currParticipant.id] = currParticipant


def readFullSurveys():
    global conditions, participants

    for currPhase in range(3):
        surveyFile = open(SURVEY_PATHS[currPhase], 'r')
        currParticipantID = -1
        lineNum = 0
        for line in surveyFile:
            tokens = line.split()
            if len(tokens) == 0:
                pass
            elif tokens[0] == '$':
                lineNum = 0
            else:
                if lineNum == 0:
                    currParticipantID = pNumToID(tokens[0])
                elif lineNum == 1:
                    participants[currParticipantID].order[currPhase] = tokens[0]
                elif lineNum == 2:
                    participants[currParticipantID].tenBitUnderstanding[currPhase] = [int(tok) for tok in tokens]
                elif lineNum == 3:
                    participants[currParticipantID].tenBitExpression[currPhase] = [int(tok) for tok in tokens]
                elif lineNum == 4:
                    participants[currParticipantID].twentyBitUnderstanding[currPhase] = [int(tok) for tok in tokens]
                elif lineNum == 5:
                    participants[currParticipantID].twentyBitExpression[currPhase] = [int(tok) for tok in tokens]
                elif lineNum == 6:
                    participants[currParticipantID].imagineRanking[currPhase] = [int(tok) for tok in tokens]
                elif lineNum == 7:
                    participants[currParticipantID].presentRanking[currPhase] = [int(tok) for tok in tokens]
                elif lineNum == 8 and currPhase == 2:
                    participants[currParticipantID].toolRating = int(tokens[0])
                elif lineNum == 9:
                    participants[currParticipantID].paperRating = [int(tok) for tok in tokens]
                else:
                    participants[currParticipantID].comments[currPhase] = line[:-1]
                lineNum += 1

    for currPhase in range(3):
        for i in range(len(participants)):
            p = participants[i]
            for j in range(len(p.tenBitUnderstanding[currPhase])):
                val = p.tenBitUnderstanding[currPhase][j]
                conditions[(currPhase, j)].tenBitUnderstanding.append(val)
            for j in range(len(p.tenBitExpression[currPhase])):
                val = p.tenBitExpression[currPhase][j]
                conditions[(currPhase, j)].tenBitExpression.append(val)
            for j in range(len(p.twentyBitUnderstanding[currPhase])):
                val = p.twentyBitUnderstanding[currPhase][j]
                conditions[(currPhase, j)].twentyBitUnderstanding.append(val)
            for j in range(len(p.twentyBitExpression[currPhase])):
                val = p.twentyBitExpression[currPhase][j]
                conditions[(currPhase, j)].twentyBitExpression.append(val)
            for j in range(len(p.imagineRanking[currPhase])):
                val = p.imagineRanking[currPhase][j]
                conditions[(currPhase, j)].imagineRanking.append(val)
            for j in range(len(p.presentRanking[currPhase])):
                val = p.presentRanking[currPhase][j]
                conditions[(currPhase, j)].presentRanking.append(val)


def sort_images():
    global sessions

    #Make sure all target directories exist
    allDirs = os.listdir(SORTED_IMAGE_PATH)
    for currPhase in range(3):
        for bitIndex in range(2):
            for methodIndex in range(NUM_METHODS[currPhase]):
                currDirName = str(currPhase + 1) + '_' + str((bitIndex + 1) * 10) + '_' + str(methodIndex + 1)
                if currDirName not in allDirs:
                    os.makedirs(SORTED_IMAGE_PATH + '/' + currDirName)

    for currPhase in range(3):
        for session in sessions[currPhase]:
            sessionName = IDToPNum(session.id)
            sessionPath = SESSION_PATHS[currPhase] + '/' + sessionName + '_session/'
            currBitIndex = 1
            currCondition = 0
            currTarget = ''
            currImgNum = 0

            for event in session.events:
                if event[1] == 'switchExpMode':
                    currCondition = (currCondition + 1) % NUM_METHODS[currPhase]
                elif event[1] == 'genNewTarget10':
                    currBitIndex = 0
                    currTarget = conversions.binaryString(int(event[2]))
                elif event[1] == 'genNewTarget20':
                    currBitIndex = 1
                    currTarget = conversions.binaryString(int(event[2]))
                elif event[1] == 'exit':
                    currCondition = 0
                    currBitIndex = 0
                elif event[1] == 'saveCanvas':
                    if event[2] == '0' or event[2] == '1':
                        if event[2] == '0':
                            successStr = 's'
                        else:
                            successStr = 'f'
                        newImgName = currTarget + '_' + successStr + '.png'
                        imgDirName = str(currPhase + 1) + '_' + str((currBitIndex + 1) * 10) + '_' + str(currCondition + 1)
                        newImgPath = SORTED_IMAGE_PATH + '/' + imgDirName + '/' + newImgName

                        prevImgName = str(currImgNum)
                        while len(prevImgName) < 4:
                            prevImgName = '0' + prevImgName
                        prevImgName = 'img_' + prevImgName + '.png'
                        prevImgPath = SESSION_PATHS[currPhase] + '/' + IDToPNum(session.id) + '_session/' + prevImgName
                        shutil.copyfile(prevImgPath, newImgPath)
                    currImgNum += 1


def readLogs():
    global sessions

    for currPhase in range(3):
        sessionPath = SESSION_PATHS[currPhase]
        sessionFolders = os.listdir(sessionPath)
        for sessionDir in sessionFolders:
            currPath = sessionPath + '/' + sessionDir
            sessionFiles = os.listdir(currPath)
            tokens = sessionDir.split('_')
            currSessionInfo = SessionInfo(pNumToID(tokens[0]))
            currEventDict = {}
            for fileName in sessionFiles:
                if fileName[:3] == 'log':
                    logNum = int(fileName[4:8])
                    logFile = open(currPath + '/' + fileName, 'r')
                    currEventDict[logNum] = []
                    for line in logFile:
                        if line[-1:] == '\n':
                            line = line[:-1]
                        eventTokens = line.split(' ')
                        if len(eventTokens[1]) == 8:
                            eventTokens[1] += '.000000'
                        eventDateTime = datetime.strptime(eventTokens[0] + ' ' + eventTokens[1], '%Y-%m-%d %H:%M:%S.%f')
                        currEventDict[logNum].append([eventDateTime] + eventTokens[2:])
                    logFile.close()

            logKeys = currEventDict.keys()
            logKeys.sort()
            for key in logKeys:
                currSessionInfo.events += currEventDict[key]
            sessions[currPhase].append(currSessionInfo)


def compareEvents(event1, event2):
    ans = True
    for i in range(min(len(event1), len(event2))):
        if event1[i] != None and event2[i] != None and event1[i] != event2[i]:
            ans = False
            break
    return ans


# occurrences[phase][10 or 20 bit][condition][session (not necessarily id)]
def countOccurrencesPerSession(eventList):
    occ = [[[[] for i in range(NUM_METHODS[k])] for j in range(2)] for k in range(3)]
    for currPhase in range(3):
        for session in sessions[currPhase]:
            currBitIndex = 1
            currCondition = 0
            # used = [[[False for i in range(NUM_METHODS[k])] for j in range(2)] for k in range(3)]
            sessionCount = [[0 for i in range(NUM_METHODS[currPhase])] for j in range(2)]
            queuedCount = 0
            for event in session.events:
                if event[1] == 'switchExpMode':
                    currCondition = (currCondition + 1) % NUM_METHODS[currPhase]
                elif event[1] == 'genNewTarget10':
                    currBitIndex = 0
                    queuedCount = 0
                elif event[1] == 'genNewTarget20':
                    currBitIndex = 1
                    queuedCount = 0
                elif event[1] == 'exit':
                    currCondition = 0
                    currBitIndex = 0
                    queuedCount = 0

                match = False
                for possibleEvent in eventList:
                    if compareEvents(possibleEvent, event[1:]):
                        match = True
                        break
                if match:
                    queuedCount += 1

                    # if used[currPhase][currBitIndex][currCondition] == True:
                    #     print '******* Duplicate in phase ' + str(currPhase+1) + ' session ' + IDToPNum(session.id) + ' at ' + str(event[0]) + ' **********'
                    # used[currPhase][currBitIndex][currCondition] = True

                if event[1] == 'saveCanvas':
                    if (event[2] == '0' or event[2] == '1'):
                        sessionCount[currBitIndex][currCondition] += queuedCount
                    queuedCount = 0

            for i in range(2):
                for j in range(NUM_METHODS[currPhase]):
                    occ[currPhase][i][j].append(sessionCount[i][j])

    return occ


def countOccurrences(eventList):
    perSessionResult = countOccurrencesPerSession(eventList)
    occ = [[[sum(perSessionResult[k][j][i]) for i in range(NUM_METHODS[k])] for j in range(2)] for k in range(3)]
    return occ

def printOccurrencePerSessionStats(eventList):
    perSessionResult = countOccurrencesPerSession(eventList)
    printString = ''

    for condKey in CONDITION_IDS:
        currCond = conditions[condKey]
        currPhase = condKey[0]
        currMethod = condKey[1]
        printString += str(condKey) + ' ' + currCond.name + '\n'
        for currBits in range(2):
            if currBits == 0:
                printString += '10 Bit '
            else:
                printString += '20 Bit '

            currSessionVals = perSessionResult[currPhase][currBits][currMethod]
            printString += 'total: ' + str(sum(currSessionVals)) + \
                           ' mean: ' + str(round(np.mean(currSessionVals), DIGITS)) + \
                           ' std: ' + str(round(np.std(currSessionVals), DIGITS)) + '\n'
        printString += '\n'

    print printString


def measureTimePerSession(onEventList, offEventList, startOn, restartTimer):
    timeOn = [[[[] for i in range(NUM_METHODS[k])] for j in range(2)] for k in range(3)]
    timeOff = [[[[] for i in range(NUM_METHODS[k])] for j in range(2)] for k in range(3)]

    for currPhase in range(3):
        for session in sessions[currPhase]:
            currBitIndex = 1
            currCondition = 0
            sessionTimeOn = [[timedelta() for i in range(NUM_METHODS[currPhase])] for j in range(2)]
            sessionTimeOff = [[timedelta() for i in range(NUM_METHODS[currPhase])] for j in range(2)]
            queuedTimeOn = timedelta()
            queuedTimeOff = timedelta()
            if startOn:
                timeTurnedOn = session.events[0][0]
                timeTurnedOff = None
                currOn = True
            else:
                timeTurnedOn = None
                timeTurnedOff = session.events[0][0]
                currOn = False

            for event in session.events:
                if event[1] == 'switchExpMode':
                    currCondition = (currCondition + 1) % NUM_METHODS[currPhase]
                elif event[1] == 'genNewTarget10':
                    currBitIndex = 0
                    queuedTimeOn = timedelta()
                    queuedTimeOff = timedelta()
                    timeTurnedOff = event[0]
                    timeTurnedOn = event[0]
                elif event[1] == 'genNewTarget20':
                    currBitIndex = 1
                    queuedTimeOn = timedelta()
                    queuedTimeOff = timedelta()
                    timeTurnedOff = event[0]
                    timeTurnedOn = event[0]
                elif event[1] == 'exit':
                    if startOn:
                        if not currOn:
                            currOn = True
                            # timeTurnedOn = event[0]
                    else:
                        if currOn:
                            currOn = False
                            # timeTurnedOff = event[0]
                    currCondition = 0
                    currBitIndex = 0
                    queuedTimeOn = timedelta()
                    queuedTimeOff = timedelta()
                    timeTurnedOff = event[0]
                    timeTurnedOn = event[0]

                matchOn = False
                matchOff = False

                for possibleEvent in offEventList:
                    if compareEvents(possibleEvent, event[1:]):
                        matchOff = True
                        break
                for possibleEvent in onEventList:
                    if compareEvents(possibleEvent, event[1:]):
                        matchOn = True
                        break

                if matchOff:
                    if currOn:
                        currOn = False
                        timeTurnedOff = event[0]
                        queuedTimeOn += timeTurnedOff - timeTurnedOn
                        # sessionTimeOn[currBitIndex][currCondition] += timeTurnedOff - timeTurnedOn
                    elif restartTimer:
                        timeTurnedOff = event[0]
                if matchOn:
                    if not currOn:
                        currOn = True
                        timeTurnedOn = event[0]
                        queuedTimeOff += timeTurnedOn - timeTurnedOff
                        # sessionTimeOff[currBitIndex][currCondition] += timeTurnedOn - timeTurnedOff
                    elif restartTimer:
                        timeTurnedOn = event[0]

                if event[1] == 'saveCanvas':
                    if currOn:
                        # timeTurnedOff = event[0]
                        # queuedTimeOn += timeTurnedOff - timeTurnedOn
                        queuedTimeOn += event[0] - timeTurnedOn
                        timeTurnedOn = event[0]
                    else:
                        # timeTurnedOn = event[0]
                        # queuedTimeOff += timeTurnedOn - timeTurnedOff
                        queuedTimeOff += event[0] - timeTurnedOff
                        timeTurnedOff = event[0]
                    if (event[2] == '0' or event[2] == '1'):
                        sessionTimeOn[currBitIndex][currCondition] += queuedTimeOn
                        sessionTimeOff[currBitIndex][currCondition] += queuedTimeOff
                    queuedTimeOn = timedelta()
                    queuedTimeOff = timedelta()
                    timeTurnedOff = event[0]
                    timeTurnedOn = event[0]

            for i in range(2):
                for j in range(NUM_METHODS[currPhase]):
                    if sessionTimeOn[i][j].total_seconds() > 300:
                        sessionTimeOn[i][j] = timedelta(seconds=300)
                    if sessionTimeOff[i][j].total_seconds() > 300:
                        sessionTimeOff[i][j] = timedelta(seconds=300)
                    timeOn[currPhase][i][j].append(sessionTimeOn[i][j])
                    timeOff[currPhase][i][j].append(sessionTimeOff[i][j])

    return timeOn, timeOff

def printTimePerSessionStats(onEventList, offEventList, startOn, restartTimer):
    perSessionTimeOn, perSessionTimeOff = measureTimePerSession(onEventList, offEventList, startOn, restartTimer)
    printString = ''

    anovaVals = [[[] for i in range(NUM_METHODS[i])] for i in range(3)]

    for condKey in CONDITION_IDS:
        currCond = conditions[condKey]
        currPhase = condKey[0]
        currMethod = condKey[1]
        printString += str(condKey) + ' ' + currCond.name + '\n'
        for currBits in range(2):
            if currBits == 0:
                printString += '10 Bit\n'
            else:
                printString += '20 Bit\n'

            currSessionOnVals = perSessionTimeOn[currPhase][currBits][currMethod]
            currSessionOffVals = perSessionTimeOff[currPhase][currBits][currMethod]
            currSessionOnVals = [currSessionOnVals[i].total_seconds() for i in range(len(currSessionOnVals))]
            currSessionOffVals = [currSessionOffVals[i].total_seconds() for i in range(len(currSessionOffVals))]

            anovaVals[condKey[0]][condKey[1]] = currSessionOnVals

            printString += 'On total: ' + str(sum(currSessionOnVals)) + \
                           ' mean: ' + str(round(np.mean(currSessionOnVals), DIGITS)) + \
                           ' std: ' + str(round(np.std(currSessionOnVals), DIGITS)) + '\n'
            printString += 'Off total: ' + str(sum(currSessionOffVals)) + \
                           ' mean: ' + str(round(np.mean(currSessionOffVals), DIGITS)) + \
                           ' std: ' + str(round(np.std(currSessionOffVals), DIGITS)) + '\n'
        printString += '\n'

    for i in range(3):
        result = stats.f_oneway(*anovaVals[i])
        printString += 'ANOVA Phase ' + str(i+1) + ' - F: ' + str(result[0]) + ' p-val: ' + str(result[1]) + '\n'

        tukeyVals = []
        tukeyLabels = []
        for j in range(len(anovaVals[i])):
            currCondVals = anovaVals[i][j]
            for val in currCondVals:
                tukeyLabels.append(CONDITION_NAMES[i][j])
                tukeyVals.append(val)
        mc = MultiComparison(tukeyVals, tukeyLabels)
        res = mc.tukeyhsd() #alpha=0.1)
        printString += str(res)
        printString += '\n'
        printString += str(mc.groupsunique)
        printString += '\n'
        pVals = psturng(np.abs(res.meandiffs / res.std_pairs), len(res.groupsunique), res.df_total)
        printString += str(pVals)
        printString += '\n'


        #np.asarray(someListOfLists, dtype=np.float32)

    print printString


# Deals with toggles with more than one setting
def measureStateTimePerSession(eventList, startState, interestStates, numStates):
    timeOn = [[[[] for i in range(NUM_METHODS[k])] for j in range(2)] for k in range(3)]
    timeOff = [[[[] for i in range(NUM_METHODS[k])] for j in range(2)] for k in range(3)]

    for currPhase in range(3):
        for session in sessions[currPhase]:
            currBitIndex = 1
            currCondition = 0
            state = startState
            sessionTimeOn = [[timedelta() for i in range(NUM_METHODS[currPhase])] for j in range(2)]
            sessionTimeOff = [[timedelta() for i in range(NUM_METHODS[currPhase])] for j in range(2)]
            queuedTimeOn = timedelta()
            queuedTimeOff = timedelta()
            if state in interestStates[currPhase]:
                timeTurnedOn = session.events[0][0]
                timeTurnedOff = None
            else:
                timeTurnedOn = None
                timeTurnedOff = session.events[0][0]

            for event in session.events:
                if event[1] == 'switchExpMode':
                    currCondition = (currCondition + 1) % NUM_METHODS[currPhase]
                elif event[1] == 'genNewTarget10':
                    currBitIndex = 0
                    queuedTimeOn = timedelta()
                    queuedTimeOff = timedelta()
                    timeTurnedOff = event[0]
                    timeTurnedOn = event[0]
                elif event[1] == 'genNewTarget20':
                    currBitIndex = 1
                    queuedTimeOn = timedelta()
                    queuedTimeOff = timedelta()
                    timeTurnedOff = event[0]
                    timeTurnedOn = event[0]
                elif event[1] == 'exit':
                    state = startState
                    if state in interestStates[currPhase]:
                        timeTurnedOn = event[0]
                    else:
                        timeTurnedOff = event[0]
                    currCondition = 0
                    currBitIndex = 0
                    queuedTimeOn = timedelta()
                    queuedTimeOff = timedelta()
                    timeTurnedOff = event[0]
                    timeTurnedOn = event[0]

                match = False
                for possibleEvent in eventList:
                    if compareEvents(possibleEvent, event[1:]):
                        match = True
                        break

                if match:
                    if numStates[currPhase] > 0:
                        newState = (state + 1) % numStates[currPhase]
                    else:
                        newState = -1

                    if newState in interestStates[currPhase] and state not in interestStates[currPhase]:
                        timeTurnedOn = event[0]
                        queuedTimeOff += timeTurnedOn - timeTurnedOff
                    elif newState not in interestStates[currPhase] and state in interestStates[currPhase]:
                        timeTurnedOff = event[0]
                        queuedTimeOn += timeTurnedOff - timeTurnedOn
                    state = newState

                if event[1] == 'saveCanvas':
                    if state in interestStates[currPhase]:
                        queuedTimeOn += event[0] - timeTurnedOn
                        # timeTurnedOn = event[0]
                    else:
                        queuedTimeOff += event[0] - timeTurnedOff
                        # timeTurnedOff = event[0]
                    if event[2] == '0' or event[2] == '1':
                        sessionTimeOn[currBitIndex][currCondition] += queuedTimeOn
                        sessionTimeOff[currBitIndex][currCondition] += queuedTimeOff
                    queuedTimeOn = timedelta()
                    queuedTimeOff = timedelta()
                    timeTurnedOff = event[0]
                    timeTurnedOn = event[0]

            for i in range(2):
                for j in range(NUM_METHODS[currPhase]):
                    timeOn[currPhase][i][j].append(sessionTimeOn[i][j])
                    timeOff[currPhase][i][j].append(sessionTimeOff[i][j])

    return timeOn, timeOff

def printStateTimePerSessionStats(eventList, startState, interestStates, numStates):
    perSessionTimeOn, perSessionTimeOff = measureStateTimePerSession(eventList, startState, interestStates, numStates)
    printString = ''

    for condKey in CONDITION_IDS:
        currCond = conditions[condKey]
        currPhase = condKey[0]
        currMethod = condKey[1]
        printString += str(condKey) + ' ' + currCond.name + '\n'
        for currBits in range(2):
            if currBits == 0:
                printString += '10 Bit\n'
            else:
                printString += '20 Bit\n'

            currSessionOnVals = perSessionTimeOn[currPhase][currBits][currMethod]
            currSessionOffVals = perSessionTimeOff[currPhase][currBits][currMethod]
            currSessionOnVals = [currSessionOnVals[i].total_seconds() for i in range(len(currSessionOnVals))]
            currSessionOffVals = [currSessionOffVals[i].total_seconds() for i in range(len(currSessionOffVals))]

            printString += 'On total: ' + str(sum(currSessionOnVals)) + \
                           ' mean: ' + str(round(np.mean(currSessionOnVals), DIGITS)) + \
                           ' std: ' + str(round(np.std(currSessionOnVals), DIGITS)) + '\n'
            printString += 'Off total: ' + str(sum(currSessionOffVals)) + \
                           ' mean: ' + str(round(np.mean(currSessionOffVals), DIGITS)) + \
                           ' std: ' + str(round(np.std(currSessionOffVals), DIGITS)) + '\n'
        printString += '\n'

    print printString


def avgMethodTimes(numMethods):
    global sessions
    methodTimes = [0 for i in range(numMethods)]
    numFails = [0 for i in range(numMethods)]
    numSuccesses = [0 for i in range(numMethods)]

    for currSession in sessions:
        startTime = None
        prevTime = None
        for event in currSession.events:
            if event[1][:12] == 'genNewTarget':
                startTime = event[0]
            elif event[1] == 'saveCanvas':
                if prevTime != None and startTime != None:
                    timeDiff = prevTime - startTime
                    methodNum = int(event[3])
                    if event[2] == '0':
                        numSuccesses[methodNum] += 1
                        methodTimes[methodNum] += timeDiff.total_seconds()
                    elif event[2] == '1':
                        numFails[methodNum] += 1
                        methodTimes[methodNum] += timeDiff.total_seconds()

                    startTime == None
                    prevTime == None
            else:
                prevTime = event[0]

    for i in range(len(methodTimes)):
        numTotal = numFails[i] + numSuccesses[i]
        methodTimes[i] /= float(numTotal)

    return methodTimes, numSuccesses, numFails


def printRatingInfo():
    global participants, conditions

    printString = ''
    tenBitUndAnova = [[] for i in range(3)]
    tenBitExpAnova = [[] for i in range(3)]
    twentyBitUndAnova = [[] for i in range(3)]
    twentyBitExpAnova = [[] for i in range(3)]
    for condKey in CONDITION_IDS:
        currCond = conditions[condKey]
        printString += str(condKey) + ' ' + currCond.name + '\n'
        printString += '10 Bit Understanding - mean: ' + str(round(np.mean(currCond.tenBitUnderstanding), DIGITS)) + ' std: ' + \
            str(round(np.std(currCond.tenBitUnderstanding), DIGITS)) + '\n'
        printString += '10 Bit Expression - mean: ' + str(round(np.mean(currCond.tenBitExpression), DIGITS)) + ' std: ' + \
            str(round(np.std(currCond.tenBitExpression), DIGITS)) + '\n'
        printString += '20 Bit Understanding - mean: ' + str(round(np.mean(currCond.twentyBitUnderstanding), DIGITS)) + ' std: ' + \
                       str(round(np.std(currCond.twentyBitUnderstanding), DIGITS)) + '\n'
        printString += '20 Bit Expression - mean: ' + str(round(np.mean(currCond.twentyBitExpression), DIGITS)) + ' std: ' + \
                       str(round(np.std(currCond.twentyBitExpression), DIGITS)) + '\n'
        printString += '\n'

        tenBitUndAnova[condKey[0]].append(currCond.tenBitUnderstanding)
        tenBitExpAnova[condKey[0]].append(currCond.tenBitExpression)
        twentyBitUndAnova[condKey[0]].append(currCond.twentyBitUnderstanding)
        twentyBitExpAnova[condKey[0]].append(currCond.twentyBitExpression)

    printString += 'ANOVA Tests\n'
    for i in range(3):
        printString += 'Phase ' + str(i+1) + '\n'
        result = stats.f_oneway(*tenBitUndAnova[i])
        printString += '10 Bit Understanding - F: ' + str(round(result[0], DIGITS)) + ' p: ' + str(round(result[1], DIGITS+1)) + '\n'
        result = stats.f_oneway(*tenBitExpAnova[i])
        printString += '10 Bit Expression - F: ' + str(round(result[0], DIGITS)) + ' p: ' + str(round(result[1], DIGITS+1)) + '\n'
        result = stats.f_oneway(*twentyBitUndAnova[i])
        printString += '20 Bit Understanding - F: ' + str(round(result[0], DIGITS)) + ' p: ' + str(round(result[1], DIGITS+1)) + '\n'
        result = stats.f_oneway(*twentyBitExpAnova[i])
        printString += '20 Bit Expression - F: ' + str(round(result[0], DIGITS)) + ' p: ' + str(round(result[1], DIGITS+1)) + '\n'
        printString += '\n'

    toolRatings = []
    paperRatings = [[] for i in range(3)]
    for pKey in participants:
        p = participants[pKey]
        if p.toolRating != OBVIOUS_SENTINEL:
            toolRatings.append(p.toolRating)
        if len(p.paperRating) > 0:
            for i in range(3):
                paperRatings[i].append(p.paperRating[i])

    printString += 'Tool Rating\n'
    printString += 'mean: ' + str(round(np.mean(toolRatings), DIGITS)) + ' std.: ' + str(round(np.std(toolRatings), DIGITS)) + '\n'
    printString += '\n'

    printString += 'On Paper Rating\n'
    printString += '10 Bit - mean: ' + str(round(np.mean(paperRatings[0]), DIGITS)) + ' std.: ' + str(round(np.std(paperRatings[0]), DIGITS)) + '\n'
    printString += '20 Bit - mean: ' + str(round(np.mean(paperRatings[1]), DIGITS)) + ' std.: ' + str(round(np.std(paperRatings[1]), DIGITS)) + '\n'
    printString += '36 Bit - mean: ' + str(round(np.mean(paperRatings[2]), DIGITS)) + ' std.: ' + str(round(np.std(paperRatings[2]), DIGITS)) + '\n'
    result = stats.f_oneway(*paperRatings)
    printString += 'ANOVA - F: ' + str(round(np.mean(result[0]), DIGITS)) + ' p: ' + str(round(np.mean(result[1]), DIGITS+1)) + '\n'

    print printString

if __name__ == "__main__":
    initConditions()
    initParticipants()
    readFullSurveys()
    readLogs()
    # sort_images()

    # printRatingInfo()
    # print "Success: " + str(countOccurrences([['saveCanvas', '0', None]])) + '\n'
    # print "Failure: " + str(countOccurrences([['saveCanvas', '1', None]])) + '\n'
    # print "# Undos: " + str(countOccurrences([['buttonUndo', None, None]])) + '\n'
    # print "# Erase Toggles: " + str(countOccurrences([['smallWhiteBrush', None, None], ['medWhiteBrush', None, None], ['largeWhiteBrush', None, None]])) + '\n'

    # print "# Undo Stats"
    # printOccurrencePerSessionStats([['buttonUndo', None, None]])
    #
    # print "# Erase Toggle Stats"
    # printOccurrencePerSessionStats([['smallWhiteBrush', None, None], ['medWhiteBrush', None, None], ['largeWhiteBrush', None, None]])

    # print "# Erase/Undo/Clear Toggle Stats"
    # printOccurrencePerSessionStats([['buttonClear', None, None], ['buttonUndo', None, None], ['smallWhiteBrush', None, None],
    #                                 ['medWhiteBrush', None, None], ['largeWhiteBrush', None, None]])

    printTimePerSessionStats([['genNewTarget10', None, None], ['genNewTarget20', None, None]],
                             [['saveCanvas', '0', None], ['saveCanvas', '1', None]], False, True)

    # print "Label Tool Stats"
    # printStateTimePerSessionStats([['buttonToggleLabeller', None, None], ['keyboardToggleLabeller', None, None]], 0, [[1], [1,2], [1, 2]], NUM_LABEL_STATES)
    # print "Order Tool Stats"
    # printStateTimePerSessionStats([['buttonToggleOrder', None, None], ['keyboardToggleOrder', None, None]], 0, [[],[1],[1, 2]], NUM_ORDER_STATES)

    # readLogs(SESSION_PATHS[0])
    # print avgMethodTimes(NUM_METHODS[0])