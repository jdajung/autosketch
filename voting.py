from copy import deepcopy

READ_VOTE_FILE = "phase1_20BitVotes.txt"

def readVoteFile(fileName):
    readFile = open(fileName, 'r')
    allPrefs = {}
    for line in readFile:
        toks = line.split()
        for i in range(len(toks)-1):
            toks[i+1] = int(toks[i+1])
        allPrefs[toks[0]] = toks[1:]
    return allPrefs

def getAllPairs(numVals):
    pairs = []
    for i in range(numVals):
        for j in range(i+1,numVals):
            pairs.append([i,j])
    return pairs

def findPairWinner(allPrefs, first, second):
    numFirst = 0
    numSecond = 0
    winner = first
    loser = second

    for pref in allPrefs.values():
        if pref[first] < pref[second]:
            numFirst += 1
        elif pref[second] < pref[first]:
            numSecond += 1
        else:
            print "ERROR: Equal preferences detected"

    if numFirst == numSecond:
        winner = -1
        loser = -1
    elif numFirst < numSecond:
        winner = second
        loser = first

    print "In the match between " + str(first) + " and " + str(second) + ", the winner is " + str(winner) + ", " + \
        str(numFirst) + "-" + str(numSecond)

    return winner, loser


def condorcet(allPrefs):
    numVals = len(allPrefs[allPrefs.keys()[0]])
    allPairs = getAllPairs(numVals)
    wins = []
    winnerIndex = -1
    maxWinsIndex = 0
    for i in range(numVals):
        wins.append([])

    for pair in allPairs:
        winner, loser = findPairWinner(allPrefs, pair[0], pair[1])
        if winner != -1:
            wins[winner].append(loser)
        else:
            print "NO STRICT WINNER"
            print "Tie between " + str(pair[0]) + " and " + str(pair[1])
            #return

    for i in range(len(wins)):
        if len(wins[i]) == numVals-1:
            print "Winner found!"
            winnerIndex = i
        if len(wins[i]) > len(wins[maxWinsIndex]):
            maxWinsIndex == i

    if winnerIndex != -1:
        print "The Condorcet winner is at index " + str(winnerIndex) + " (counting from 0) with " + str(len(wins[winnerIndex])) + " pairwise wins!"
    else:
        print "No Concorcet winner exists!"
        if maxWinsIndex != -1:
            print "(One of) the closest was at index " + str(maxWinsIndex) + " with " + str(len(wins[maxWinsIndex])) + " pairwise wins."

    print "All Matchups:"
    print wins

    print "All Scores:"
    print [len(wins[i]) for i in range(len(wins))]


def borda(allPrefs):
    numVals = len(allPrefs[allPrefs.keys()[0]])
    increment = 1.0 / numVals
    scores = [0 for i in range(numVals)]

    for pref in allPrefs.values():
        for i in range(len(pref)):
            scores[i] += (numVals - pref[i] + 1) * increment

    print "Borda scores:"
    print scores
    return scores

def bordaOffByOne(allPrefs):
    numVals = len(allPrefs[allPrefs.keys()[0]])
    increment = 1.0 / (numVals - 1)
    scores = [0 for i in range(numVals)]

    for pref in allPrefs.values():
        for i in range(len(pref)):
            scores[i] += (numVals - pref[i]) * increment

    print "Borda (0 for last) scores:"
    print scores
    return scores

def bordaProportional(allPrefs):
    numVals = len(allPrefs[allPrefs.keys()[0]])
    scores = [0 for i in range(numVals)]

    for pref in allPrefs.values():
        for i in range(len(pref)):
            scores[i] += 1.0 / pref[i]

    print "Borda (proportional) scores:"
    print scores
    return scores

def findMins(l):
    minIndex = 0
    minVal = l[0]
    for i in range(len(l)):
        if l[i] < minVal:
            minIndex = i
            minVal = l[i]
    return minIndex, minVal

def baldwin(origAllPrefs):
    allPrefs = deepcopy(origAllPrefs)
    numVals = len(allPrefs[allPrefs.keys()[0]])
    elimIndices = []

    for i in range(numVals-1):
        scores = borda(allPrefs)
        minIndex, minVal = findMins(scores)
        elimIndices.append(minIndex)
        print minIndex
        allPrefs = eliminateVal(allPrefs, minIndex)
        print allPrefs
        print elimIndices


def eliminateVal(allPrefs, elimIndex):
    newAllPrefs = {}

    for key in allPrefs.keys():
        currPrefs = allPrefs[key]
        elimRank = currPrefs[elimIndex]
        newPrefs = []
        for i in range(len(currPrefs)):
            if i == elimIndex:
                pass
            elif currPrefs[i] > elimRank:
                newPrefs.append(currPrefs[i] - 1)
            else:
                newPrefs.append(currPrefs[i])
        newAllPrefs[key] = newPrefs
    return newAllPrefs


if __name__ == "__main__":
    allPrefs = readVoteFile(READ_VOTE_FILE)
    condorcet(allPrefs)
    borda (allPrefs)
    # bordaOffByOne(allPrefs)
    # bordaProportional(allPrefs)
    # baldwin(allPrefs)