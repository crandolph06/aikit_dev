from AFsplitter import afmanParser
from mistralRAG import standardRagQuestionGen
import re
import time
from OutputFile import OutputFile

# File location info
text_only_file_path = '/cleantxts/SHAWAFBI11-250 (CAO 1 Aug 21) (1).txt' # Point to txt only file path, equivalent to body from AFMAN Parser
file_path = '/current_library/SHAWAFBI 11-250.txt' # Point to txt file to be converted to dictionary
tocContainsSeparators = False
footerTitle = r'SHAWAFBI11\-250'

# Create and open output file
fulldatatitle = 'test.txt' # Title of desired output file
ofile = OutputFile(fulldatatitle)
ofile.openFile()

# For doc length comparison
characterIncrement = 1000 # Increment by which text will be increased
characterCount = 100952 # Total length of document in characters, not automated

# For time comparison
startTime = time.time()
print(f'Start Time: {startTime}')

with open(text_only_file_path, 'r') as file:
    file_content = file.read()
characterMax = len(file_content)

# Create empty dictionary to store question quantities 
questionQuantityDict = {}

# Start clock
t0 = time.time()

# Parse publication into sentence, section dictionaries
sentenceDict, sectionDict = afmanParser(file_path, tocContainsSeparators, footerTitle)

# Counts number of valid sentences in sentence dictionary greater than numWords long
def countValidSentences(numWords:int, sentenceDict:dict, lastReference:str):
    validSentenceCount = 0
    for paragraphRef in sentenceDict.keys():
        if paragraphRef != lastReference:
            for sentence in sentenceDict[paragraphRef].keys():
                if len(sentenceDict[paragraphRef][sentence]["sentences"]) > numWords:
                    validSentenceCount += 1
        else: 
            return validSentenceCount 
    return validSentenceCount

# Finds average location for provided reference in text of length characterCount
def findReferenceAvgLocation(references, text, characterCount):
    spanAvgPercentageList = []
    for reference in references:
        if re.findall(r'[0-9]+\.[0-9]+', reference) != []:
            shortRef = re.search(r'[0-9]+(.*)[0-9]+\.', reference).group()
            search = re.search(shortRef, text)
            if search != None:
                average = (search.start() + search.end())/2
                percentage = average/characterCount
                spanAvgPercentageList.append(percentage)
            else:
                spanAvgPercentageList.append("Unknown -- no match for reference")
        else: 
            spanAvgPercentageList.append("Unknown -- non-numerical reference")
    return spanAvgPercentageList

# Create dictionary for references
referenceDict = {}

while characterCount <= characterMax:
    questionQuantityDict[characterCount] = {}
    referenceDict[characterCount] = {}
    timeCount = 1
    timeLabel = 't' + str(timeCount)
    current_file_content = file_content[:characterCount]
    allSeparators = re.findall(r'\n[0-9]\.[0-9]+\.', current_file_content)
    if allSeparators == []:
        contextRoughSentenceCount = current_file_content.split(".")
        lastSeparator = None
        validSentences = len(contextRoughSentenceCount) # HACK Presumed - might not be accurate.
    else:
        lastSeparator = allSeparators[-1].lstrip().rstrip()
        validSentences = countValidSentences(5, sentenceDict, lastSeparator)
        if validSentences == 0:
            contextRoughSentenceCount = current_file_content.split(".")
            validSentences = len(contextRoughSentenceCount) # HACK Presumed - might not be accurate.
    questionsGenerated = standardRagQuestionGen(True, current_file_content)
    ofile.write(questionsGenerated)
    newReferences = re.findall(r'Reference\:\s(.*)', questionsGenerated)
    referenceAvgLocations = findReferenceAvgLocation(newReferences, current_file_content, characterCount)
    questions = re.findall(r'Question\:\s', questionsGenerated)
    timeLabel = time.time()
    questionQuantityDict[characterCount]["question count"] = len(questions)
    questionQuantityDict[characterCount]["valid sentences"] = validSentences
    if validSentences == 0:
        percentageCovered = 0
    else:
        percentageCovered = len(questions) / validSentences
    characterCount += characterIncrement
    if characterCount > characterMax:
        exit()
    timeCount += 1

endTime = time.time()

totalTime = startTime - endTime
timePerQuestion = totalTime/len(questions)
ofile.write(f'Start time: {startTime}.\nEnd time: {endTime}\nTotal Time: {totalTime}\nTime per Question: {timePerQuestion}')
