import os
import shutil
import numpy as np
import scipy.stats as stats
import conversions
from voting import condorcet, borda
from datetime import datetime
from datetime import timedelta
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from statsmodels.stats.multicomp import MultiComparison
from statsmodels.stats.libqsturng import psturng

BASE_PATH = "C:/Users/j35jung/Documents/OpenCVWork/auto-sketch"
SESSION_PATH = "C:/Users/j35jung/Documents/OpenCVWork/auto-sketch/experiment_sessions"
SURVEY_PATH = "C:/Users/j35jung/Documents/OpenCVWork/auto-sketch/questionnaire_data.txt"
DEMO_PATH = "C:/Users/j35jung/Documents/OpenCVWork/auto-sketch/demographics.txt"
SORTED_IMAGE_ADDITION = 'sorted_images'
SORTED_IMAGE_PATH = BASE_PATH + '/' + SORTED_IMAGE_ADDITION

NUM_METHODS = 3
NUM_LABEL_STATES = 2
NUM_ORDER_STATES = 2
NUM_PARTICIPANTS = 24
OBVIOUS_SENTINEL = -9999999
CONDITION_NAMES = ['Dividers', 'Helper', 'Auto']
CONDITION_IDS = [0,1,2]
DIGITS = 2

sessions = []
conditions = {}
participants = {}
fixed_auto = []
allPrefs = {}


class SessionInfo():
    def __init__(self, id):
        self.id = id
        self.events = []

    def __str__(self):
        return 'Session ' + str(self.id) + ' events: ' + str(self.events)


class ParticipantInfo():
    def __init__(self):
        self.id = -1
        self.gender = ''
        self.age = OBVIOUS_SENTINEL
        self.right_handed = None
        self.computer_hours = OBVIOUS_SENTINEL
        self.computer_hours_comments = ''
        self.stylus_experience = None
        self.stylus_experience_comments = ''
        self.art_courses = None
        self.art_courses_comments = ''
        self.art_work = None
        self.art_work_comments = ''

        self.order = ''
        self.tenBitUnderstanding = []
        self.tenBitExpression = []
        self.twentyBitUnderstanding = []
        self.twentyBitExpression = []
        self.usefulness = []
        self.ranking = []
        self.whyRanking = ''
        self.comments = ''

    def __str__(self):
        return 'ID: ' + str(self.id) + '\n' \
               + 'Gender: ' + self.gender + '\n' \
               + 'Age: ' + str(self.age) + '\n' \
               + 'Right handed: ' + str(self.right_handed) + '\n' \
               + 'Daily computer hours: ' + str(self.computer_hours) + '\n' \
               + 'Comments: ' + self.computer_hours_comments + '\n' \
               + 'Experience with stylus: ' + str(self.stylus_experience) + '\n' \
               + 'Comments: ' + self.stylus_experience_comments + '\n' \
               + 'Has taken art courses: ' + str(self.art_courses) + '\n' \
               + 'Comments: ' + self.art_courses_comments + '\n' \
               + 'Has done art-related work: ' + str(self.art_work) + '\n' \
               + 'Comments: ' + self.art_work_comments + '\n' + '\n' \
               + 'Order: ' + self.order + '\n' \
               + '10 Bit Understanding: ' + str(self.tenBitUnderstanding) + '\n' \
               + '10 Bit Expression: ' + str(self.tenBitExpression) + '\n' \
               + '20 Bit Understanding: ' + str(self.twentyBitUnderstanding) + '\n' \
               + '20 Bit Expression: ' + str(self.twentyBitExpression) + '\n' \
               + 'Usefulness Scores: ' + str(self.usefulness) + '\n' \
               + 'Ranking: ' + str(self.ranking) + '\n' \
               + 'Ranking Explanation: ' + self.whyRanking + '\n' \
               + 'Additional Comments: ' + self.comments + '\n'


class ConditionInfo():
    def __init__(self):
        self.id = None
        self.name = ''
        self.tenBitUnderstanding = []
        self.tenBitExpression = []
        self.twentyBitUnderstanding = []
        self.twentyBitExpression = []
        self.usefulness = []
        self.ranking = []

    def rankCounts(self):
        counts = [0,0,0]
        for val in self.ranking:
            counts[val-1] += 1
        return counts

    def __str__(self):
        return 'ID: ' + str(self.id) + '\n' \
               'Name: ' + self.name + '\n' \
               + '10 Bit Understanding: ' + str(self.tenBitUnderstanding) + '\n' \
               + '10 Bit Expression: ' + str(self.tenBitExpression) + '\n' \
               + '20 Bit Understanding: ' + str(self.twentyBitUnderstanding) + '\n' \
               + '20 Bit Expression: ' + str(self.twentyBitExpression) + '\n' \
               + 'Usefulness Scores: ' + str(self.usefulness) + '\n' \
               + 'Ranking Counts: ' + str(self.rankCounts()) + '\n'


# def condIndexToID(phase, number):
#     return 'p' + str(phase + 1) + '-' + str(number)

def pNumToID(participantNum):
    return int(participantNum[1:]) - 1

def IDToPNum(participantID):
    return 'p' + str(participantID + 1)


def initConditions():
    global conditions, fixed_auto
    fixed_auto = []
    for i in range(NUM_METHODS):
        currCondition = ConditionInfo()
        currCondition.id = i
        currCondition.name = CONDITION_NAMES[i]
        # currCondition.index = j
        conditions[currCondition.id] = currCondition

def initParticipants():
    global participants
    for i in range(NUM_PARTICIPANTS):
        currParticipant = ParticipantInfo()
        currParticipant.id = i
        participants[currParticipant.id] = currParticipant

def readDemographics():
    global participants

    demoFile = open(DEMO_PATH, 'r')
    currParticipantID = -1
    lineNum = 0
    for line in demoFile:
        tokens = line.split()
        if len(tokens) == 0:
            pass
        elif tokens[0] == '$':
            lineNum = 0
        else:
            if lineNum == 0:
                currParticipantID = pNumToID(tokens[0])
            elif lineNum == 1:
                participants[currParticipantID].gender = tokens[0]
            elif lineNum == 2:
                participants[currParticipantID].age = float(tokens[0])
            elif lineNum == 3:
                if tokens[0] == 'y' or tokens[0] == 'Y':
                    participants[currParticipantID].right_handed = True
                else:
                    participants[currParticipantID].right_handed = False
            elif lineNum == 4:
                participants[currParticipantID].computer_hours = float(tokens[0])
                participants[currParticipantID].computer_hours_comments = line[len(tokens[0])+1:]
            elif lineNum == 5:
                if tokens[0] == 'y' or tokens[0] == 'Y':
                    participants[currParticipantID].stylus_experience = True
                else:
                    participants[currParticipantID].stylus_experience = False
                participants[currParticipantID].stylus_experience_comments = line[len(tokens[0])+1:]
            elif lineNum == 6:
                if tokens[0] == 'y' or tokens[0] == 'Y':
                    participants[currParticipantID].art_courses = True
                else:
                    participants[currParticipantID].art_courses = False
                participants[currParticipantID].art_courses_comments = line[len(tokens[0])+1:]
            else:
                if tokens[0] == 'y' or tokens[0] == 'Y':
                    participants[currParticipantID].art_work = True
                else:
                    participants[currParticipantID].art_work = False
                participants[currParticipantID].art_work_comments = line[len(tokens[0])+1:]
            lineNum += 1


def readFullSurveys():
    global conditions, participants, fixed_auto

    surveyFile = open(SURVEY_PATH, 'r')
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
                participants[currParticipantID].order = tokens[0]
            elif lineNum == 2:
                participants[currParticipantID].tenBitUnderstanding = [int(tok) for tok in tokens]
            elif lineNum == 3:
                participants[currParticipantID].tenBitExpression = [int(tok) for tok in tokens]
            elif lineNum == 4:
                participants[currParticipantID].twentyBitUnderstanding = [int(tok) for tok in tokens]
            elif lineNum == 5:
                participants[currParticipantID].twentyBitExpression = [int(tok) for tok in tokens]
            elif lineNum == 6:
                participants[currParticipantID].usefulness = [int(tok) for tok in tokens]
            elif lineNum == 7:
                participants[currParticipantID].ranking = [int(tok) for tok in tokens]
            elif lineNum == 8:
                participants[currParticipantID].whyRanking = line[:-1]
            else:
                participants[currParticipantID].comments = line[:-1]
            lineNum += 1

    for i in range(len(participants)):
        p = participants[i]
        for j in range(len(p.tenBitUnderstanding)):
            val = p.tenBitUnderstanding[j]
            conditions[j].tenBitUnderstanding.append(val)
        for j in range(len(p.tenBitExpression)):
            val = p.tenBitExpression[j]
            conditions[j].tenBitExpression.append(val)
        for j in range(len(p.twentyBitUnderstanding)):
            val = p.twentyBitUnderstanding[j]
            conditions[j].twentyBitUnderstanding.append(val)
        for j in range(len(p.twentyBitExpression)):
            val = p.twentyBitExpression[j]
            conditions[j].twentyBitExpression.append(val)
        for j in range(len(p.usefulness)):
            val = p.usefulness[j]
            if j < len(p.usefulness)-1:
                conditions[j].usefulness.append(val)
            else:
                fixed_auto.append(val)
        for j in range(len(p.ranking)):
            val = p.ranking[j]
            conditions[j].ranking.append(val)
        allPrefs[IDToPNum(p.id)] = p.ranking


def sort_images():
    global sessions

    #Make sure all target directories exist
    baseFiles = os.listdir(BASE_PATH)
    if SORTED_IMAGE_ADDITION not in baseFiles:
        os.makedirs(SORTED_IMAGE_PATH)
    allDirs = os.listdir(SORTED_IMAGE_PATH)
    for bitIndex in range(2):
        for methodIndex in range(NUM_METHODS):
            currDirName = str((bitIndex + 1) * 10) + '_' + str(methodIndex + 1)
            if currDirName not in allDirs:
                os.makedirs(SORTED_IMAGE_PATH + '/' + currDirName)

    for session in sessions:
        currBitIndex = -1
        currCondition = 0
        currTarget = ''
        currImgNum = 0

        for event in session.events:
            if event[1] == 'switchSuggestionMode':
                currCondition = (currCondition + 1) % NUM_METHODS
            elif event[1] == 'genNewTarget10':
                currBitIndex = 0
                currTarget = conversions.binaryString(int(event[2]))
            elif event[1] == 'genNewTarget20':
                currBitIndex = 1
                currTarget = conversions.binaryString(int(event[2]))
            elif event[1] == 'exit':
                currCondition = 0
                currBitIndex = -1
            elif event[1] == 'saveCanvas':
                if event[2] == '0' or event[2] == '1':
                    prevImgName = str(currImgNum)
                    while len(prevImgName) < 4:
                        prevImgName = '0' + prevImgName
                    folderNum = str(session.id)
                    while len(folderNum) < 4:
                        folderNum = '0' + folderNum
                    prevImgName = 'img_' + prevImgName + '.png'
                    prevImgPath = SESSION_PATH + '/' + 'session_' + folderNum + '/' + prevImgName

                    if event[2] == '0':
                        successStr = 's'
                    else:
                        successStr = 'f'
                    newImgName = folderNum + '_' + currTarget + '_' + successStr + '.png'
                    imgDirName = str((currBitIndex + 1) * 10) + '_' + str(currCondition + 1)
                    newImgPath = SORTED_IMAGE_PATH + '/' + imgDirName + '/' + newImgName

                    shutil.copyfile(prevImgPath, newImgPath)
                currImgNum += 1


def readLogs():
    global sessions

    sessionPath = SESSION_PATH
    sessionFolders = os.listdir(sessionPath)
    for sessionDir in sessionFolders:
        currPath = sessionPath + '/' + sessionDir
        sessionFiles = os.listdir(currPath)
        tokens = sessionDir.split('_')
        currSessionInfo = SessionInfo(int(tokens[1]))
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
        sessions.append(currSessionInfo)


def compareEvents(event1, event2):
    ans = True
    for i in range(min(len(event1), len(event2))):
        if event1[i] != None and event2[i] != None and event1[i] != event2[i]:
            ans = False
            break
    return ans


# occurrences[10 or 20 bit][condition][session (not necessarily id)]
def countOccurrencesPerSession(eventList):
    occ = [[[] for i in range(NUM_METHODS)] for j in range(2)]
    for session in sessions:
        currBitIndex = -1
        currCondition = 0
        used = [[False for i in range(NUM_METHODS)] for j in range(2)]
        sessionCount = [[0 for i in range(NUM_METHODS)] for j in range(2)]
        queuedCount = 0
        for event in session.events:
            if event[1] == 'switchSuggestionMode':
                currCondition = (currCondition + 1) % NUM_METHODS
            elif event[1] == 'genNewTarget10':
                currBitIndex = 0
                queuedCount = 0
            elif event[1] == 'genNewTarget20':
                currBitIndex = 1
                queuedCount = 0
            elif event[1] == 'exit':
                currCondition = 0
                currBitIndex = -1
                queuedCount = 0

            match = False
            for possibleEvent in eventList:
                if compareEvents(possibleEvent, event[1:]):
                    match = True
                    break
            if match:
                queuedCount += 1
                # if used[currBitIndex][currCondition] == True:
                #     print '******* Duplicate in session ' + IDToPNum(session.id) + ' at ' + str(event[0]) + ' **********'
                used[currBitIndex][currCondition] = True

            if event[1] == 'saveCanvas':
                if (event[2] == '0' or event[2] == '1'):
                    sessionCount[currBitIndex][currCondition] += queuedCount
                queuedCount = 0

        for i in range(2):
            for j in range(NUM_METHODS):
                occ[i][j].append(sessionCount[i][j])

    return occ


def countOccurrences(eventList):
    perSessionResult = countOccurrencesPerSession(eventList)
    occ = [[sum(perSessionResult[j][i]) for i in range(NUM_METHODS)] for j in range(2)]
    return occ

def printOccurrencePerSessionStats(eventList):
    perSessionResult = countOccurrencesPerSession(eventList)
    printString = ''

    for condKey in CONDITION_IDS:
        currCond = conditions[condKey]
        currMethod = condKey
        printString += str(condKey) + ' ' + currCond.name + '\n'
        for currBits in range(2):
            if currBits == 0:
                printString += '10 Bit '
            else:
                printString += '20 Bit '

            currSessionVals = perSessionResult[currBits][currMethod]
            printString += 'total: ' + str(sum(currSessionVals)) + \
                           ' mean: ' + str(round(np.mean(currSessionVals), DIGITS)) + \
                           ' std: ' + str(round(np.std(currSessionVals), DIGITS)) + '\n'
        printString += '\n'

    print printString


def measureTimePerSession(onEventList, offEventList, startOn, restartTimer):
    timeOn = [[[] for i in range(NUM_METHODS)] for j in range(2)]
    timeOff = [[[] for i in range(NUM_METHODS)] for j in range(2)]

    for session in sessions:
        currBitIndex = -1
        currCondition = 0
        sessionTimeOn = [[timedelta() for i in range(NUM_METHODS)] for j in range(2)]
        sessionTimeOff = [[timedelta() for i in range(NUM_METHODS)] for j in range(2)]
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
            if event[1] == 'switchSuggestionMode':
                currCondition = (currCondition + 1) % NUM_METHODS
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
            for j in range(NUM_METHODS):
                if sessionTimeOn[i][j].total_seconds() > 300:
                    sessionTimeOn[i][j] = timedelta(seconds=300)
                if sessionTimeOff[i][j].total_seconds() > 300:
                    sessionTimeOff[i][j] = timedelta(seconds=300)
                timeOn[i][j].append(sessionTimeOn[i][j])
                timeOff[i][j].append(sessionTimeOff[i][j])

    return timeOn, timeOff

def printTimePerSessionStats(onEventList, offEventList, startOn, restartTimer):
    perSessionTimeOn, perSessionTimeOff = measureTimePerSession(onEventList, offEventList, startOn, restartTimer)
    printString = ''

    anovaVals = [[] for i in range(NUM_METHODS)]

    for condKey in CONDITION_IDS:
        currCond = conditions[condKey]
        currMethod = condKey
        printString += str(condKey) + ' ' + currCond.name + '\n'
        for currBits in range(2):
            if currBits == 0:
                printString += '10 Bit\n'
            else:
                printString += '20 Bit\n'

            currSessionOnVals = perSessionTimeOn[currBits][currMethod]
            currSessionOffVals = perSessionTimeOff[currBits][currMethod]
            currSessionOnVals = [currSessionOnVals[i].total_seconds() for i in range(len(currSessionOnVals))]
            currSessionOffVals = [currSessionOffVals[i].total_seconds() for i in range(len(currSessionOffVals))]

            anovaVals[condKey] = currSessionOnVals

            printString += 'On total: ' + str(sum(currSessionOnVals)) + \
                           ' mean: ' + str(round(np.mean(currSessionOnVals), DIGITS)) + \
                           ' std: ' + str(round(np.std(currSessionOnVals), DIGITS)) + '\n'
            printString += 'Off total: ' + str(sum(currSessionOffVals)) + \
                           ' mean: ' + str(round(np.mean(currSessionOffVals), DIGITS)) + \
                           ' std: ' + str(round(np.std(currSessionOffVals), DIGITS)) + '\n'
        printString += '\n'

    result = stats.f_oneway(*anovaVals)
    printString += 'ANOVA F: ' + str(result[0]) + ' p-val: ' + str(result[1]) + '\n'

    tukeyVals = []
    tukeyLabels = []
    for j in range(len(anovaVals)):
        currCondVals = anovaVals[j]
        for val in currCondVals:
            tukeyLabels.append(CONDITION_NAMES[j])
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
    timeOn = [[[] for i in range(NUM_METHODS)] for j in range(2)]
    timeOff = [[[] for i in range(NUM_METHODS)] for j in range(2)]

    for session in sessions:
        currBitIndex = 1
        currCondition = 0
        state = startState
        sessionTimeOn = [[timedelta() for i in range(NUM_METHODS)] for j in range(2)]
        sessionTimeOff = [[timedelta() for i in range(NUM_METHODS)] for j in range(2)]
        queuedTimeOn = timedelta()
        queuedTimeOff = timedelta()
        if state in interestStates:
            timeTurnedOn = session.events[0][0]
            timeTurnedOff = None
        else:
            timeTurnedOn = None
            timeTurnedOff = session.events[0][0]

        for event in session.events:
            if event[1] == 'switchSuggestionMode':
                currCondition = (currCondition + 1) % NUM_METHODS
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
                if state in interestStates:
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
                if numStates > 0:
                    newState = (state + 1) % numStates
                else:
                    newState = -1

                if newState in interestStates and state not in interestStates:
                    timeTurnedOn = event[0]
                    queuedTimeOff += timeTurnedOn - timeTurnedOff
                elif newState not in interestStates and state in interestStates:
                    timeTurnedOff = event[0]
                    queuedTimeOn += timeTurnedOff - timeTurnedOn
                state = newState

            if event[1] == 'saveCanvas':
                if state in interestStates:
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
            for j in range(NUM_METHODS):
                timeOn[i][j].append(sessionTimeOn[i][j])
                timeOff[i][j].append(sessionTimeOff[i][j])

    return timeOn, timeOff

def printStateTimePerSessionStats(eventList, startState, interestStates, numStates):
    perSessionTimeOn, perSessionTimeOff = measureStateTimePerSession(eventList, startState, interestStates, numStates)
    printString = ''

    for condKey in CONDITION_IDS:
        currCond = conditions[condKey]
        currMethod = condKey
        printString += str(condKey) + ' ' + currCond.name + '\n'
        for currBits in range(2):
            if currBits == 0:
                printString += '10 Bit\n'
            else:
                printString += '20 Bit\n'

            currSessionOnVals = perSessionTimeOn[currBits][currMethod]
            currSessionOffVals = perSessionTimeOff[currBits][currMethod]
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
    tenBitUndAnova = []
    tenBitExpAnova = []
    twentyBitUndAnova = []
    twentyBitExpAnova = []
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

        tenBitUndAnova.append(currCond.tenBitUnderstanding)
        tenBitExpAnova.append(currCond.tenBitExpression)
        twentyBitUndAnova.append(currCond.twentyBitUnderstanding)
        twentyBitExpAnova.append(currCond.twentyBitExpression)

    printString += 'ANOVA Tests\n'
    result = stats.f_oneway(*tenBitUndAnova)
    printString += '10 Bit Understanding - F: ' + str(round(result[0], DIGITS)) + ' p: ' + str(round(result[1], DIGITS+1)) + '\n'
    result = stats.f_oneway(*tenBitExpAnova)
    printString += '10 Bit Expression - F: ' + str(round(result[0], DIGITS)) + ' p: ' + str(round(result[1], DIGITS+1)) + '\n'
    result = stats.f_oneway(*twentyBitUndAnova)
    printString += '20 Bit Understanding - F: ' + str(round(result[0], DIGITS)) + ' p: ' + str(round(result[1], DIGITS+1)) + '\n'
    result = stats.f_oneway(*twentyBitExpAnova)
    printString += '20 Bit Expression - F: ' + str(round(result[0], DIGITS)) + ' p: ' + str(round(result[1], DIGITS+1)) + '\n'
    printString += '\n'

    # toolRatings = []
    # paperRatings = []
    # for pKey in participants:
    #     p = participants[pKey]
    #     if p.toolRating != OBVIOUS_SENTINEL:
    #         toolRatings.append(p.toolRating)
    #     if len(p.paperRating) > 0:
    #         paperRatings[i].append(p.paperRating)
    #
    # printString += 'Tool Rating\n'
    # printString += 'mean: ' + str(round(np.mean(toolRatings), DIGITS)) + ' std.: ' + str(round(np.std(toolRatings), DIGITS)) + '\n'
    # printString += '\n'
    #
    # printString += 'On Paper Rating\n'
    # printString += '10 Bit - mean: ' + str(round(np.mean(paperRatings[0]), DIGITS)) + ' std.: ' + str(round(np.std(paperRatings[0]), DIGITS)) + '\n'
    # printString += '20 Bit - mean: ' + str(round(np.mean(paperRatings[1]), DIGITS)) + ' std.: ' + str(round(np.std(paperRatings[1]), DIGITS)) + '\n'
    # printString += '36 Bit - mean: ' + str(round(np.mean(paperRatings[2]), DIGITS)) + ' std.: ' + str(round(np.std(paperRatings[2]), DIGITS)) + '\n'
    # result = stats.f_oneway(*paperRatings)
    # printString += 'ANOVA - F: ' + str(round(np.mean(result[0]), DIGITS)) + ' p: ' + str(round(np.mean(result[1]), DIGITS+1)) + '\n'

    print printString


def countMethodAtRank(methodNum, rank):
    global conditions
    coi = conditions[methodNum]
    counter =  0
    for val in coi.ranking:
        if val == rank:
            counter += 1
    return counter

if __name__ == "__main__":
    initConditions()
    initParticipants()
    readFullSurveys()
    readDemographics()
    readLogs()

    # for session in sessions:
    #     print session
    # print '********************************************************'
    for key in conditions.keys():
        print conditions[key]
    print 'Usefulness if Auto was unchangeable: ' + str(fixed_auto)
    print ''
    print '********************************************************'
    for key in participants.keys():
        print participants[key]
        # p = participants[key]
        # if p.ranking[0] == 1:
        #     print p

    # condorcet(allPrefs)
    # borda(allPrefs)

    # sort_images()

    # print countMethodAtRank(0,2)

    # printRatingInfo()
    # print "Success: " + str(countOccurrences([['saveCanvas', '0', None, None]])) + '\n'
    # print "Failure: " + str(countOccurrences([['saveCanvas', '1', None, None]])) + '\n'
    # print "# Undos: " + str(countOccurrences([['buttonUndo', None, None, None]])) + '\n'
    # print "# Erase Toggles: " + str(countOccurrences([['smallWhiteBrush', None, None, None], ['medWhiteBrush', None, None, None], ['largeWhiteBrush', None, None, None]])) + '\n'

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