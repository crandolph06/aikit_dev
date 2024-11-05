from MqfParserRegex import MqfParser
from questionAsker import singleQuestionAsker
from DaaDy_consolidator import consolidateDaadyTsvs
from OutputFile import OutputFile
import os
import time

# Load dictionary
file_path = '/current_library/SHAWAFBI 11-250.txt' # text to be converted to dictionary
tocContainsSeparators = False
footerTitle = r'SHAWAFBI11\-250'

# Create combined dictionary
directory_path = '/Users/clairebieber/ai-kit/RAG/tools/QA/DaaDy_results'
# print('before consolidate daady tsvs')
bigDaaDy, sectionDaaDy = consolidateDaadyTsvs(directory_path)
# print('DaaDy consolidation, complete.')
 
# Output File setup
ofile = OutputFile('SQUADAssess_06_03_v1.tsv')
ofile.write('Status\tNum\tQuestion\n')

def getValidResponse(selection, numPubs):
    numericalLegalResponses = []
    for num in range(numPubs):
        numericalLegalResponses.append(num)
    if selection == 'B':
        return selection
    try:
        testNum = int(selection)
        selection = testNum
    except ValueError:
        selectionInput = input('>>>Invalid response provided. Response should be an integer or B with no additional spaces or punctuation.')
        return getValidResponse(selectionInput, numPubs)
    if selection in numericalLegalResponses:
        return selection
    else:
        selectionInput = input('>>>Invalid response provided. Response should be an integer or B with no additional spaces or punctuation.')
        return getValidResponse(selectionInput, numPubs)

def checkForPubTitle(mqfSourcePub, currentPubList):
    # Bypass = set replacementPub is previous doc title. Unable to search DaaDy add to docOffenders.
    # Skip = set replacementPub to 'SKIP'. Skip question entirely.
    numPubs = len(currentPubList)
    if mqfSourcePub not in currentPubList:
        options = [(index, currentPub) for index, currentPub in enumerate(currentPubList)]
        print(f'Error. {mqfSourcePub} not in current library.\nAvailable options are: {options}.\nType B to bypass pub replacement.\n')
        selectionInput = input('>>>Type selection for pub replacement. Type B to bypass.')
        selection = getValidResponse(selectionInput, numPubs)
        if selection == 'B':
            return None
        for option in options:
            if selection == option[0]:
                pubReplacement = option[1]
                return pubReplacement
            elif selection not in [option[0] for option in options]:
                selectionInput = input('>>>Invalid selection provided. Resubmit replacement.')
                selection = getValidResponse(selectionInput)
                pubReplacement = checkForPubTitle(mqfSourcePub, currentPubList)
    else:
        pubReplacement = mqfSourcePub
        return pubReplacement

# Create comobined text file from doc directory
library_path = '/Users/clairebieber/ai-kit/Library/1_focused_library/assessorLib'
combinedTextDoc = ""
file_list = os.listdir(library_path)
current_lib_file_names = []
for single in file_list:
    # print(f'Adding {single} to full context doc.')
    path = library_path + '/' + single
    fileParts = single.split(".tx")
    if fileParts[0] not in current_lib_file_names:
        current_lib_file_names.append(fileParts[0])
    with open(path, 'r') as file:
        file_content = file.read()
        combinedTextDoc += file_content
numCurrentPubs = len(current_lib_file_names)
# print('Combined Text Doc creation complete.')

# Retrieve question/reference from MQF data
parser = MqfParser()
mqfDict = parser.parseMqf("local_mqf.txt")
numQuestions = len(mqfDict)
        

# Create dict for QA Assessment
mqfAssessmentDict = {}
sentenceOffenders = []
docOffenders = []
totalOffenders = []
skippedQuestions = []
brokenQuestions = []

# Outline Error Messages
contextError = 'Insufficient context provided' # Must be programmed into LLM prompt
errorLen = len(contextError)

# Get list of source pubs from MQF 
mqfSourcePubList = []
for num in mqfDict.keys():
    sourcePub = mqfDict[num]["reference"]
    if sourcePub not in mqfSourcePubList:
        mqfSourcePubList.append(sourcePub)

# Create dictionary of current pub replacements
pubReplaceDict = {}
options = [(index, currentPub) for index, currentPub in enumerate(current_lib_file_names)]
for mqfPub in mqfSourcePubList:
    if mqfPub not in current_lib_file_names:
        replacement = checkForPubTitle(mqfPub, current_lib_file_names)
        pubReplaceDict[mqfPub] = replacement

# Ask questions to smallest available context
print('Working on mqfDict.')
mqfDictStartTime = time.time()
for num in mqfDict.keys():
        # Pull useful data from mqfDict (from MQF Parser)
        question = mqfDict[num]["question"] 
        paraRef = mqfDict[num]["paragraph"]
        # options = mqfDict[num]["options"] # Currently not in use
        mqfSourcePub = mqfDict[num]["reference"]

        # Check to see if sourcePub is in DaaDy library
        if mqfSourcePub in pubReplaceDict:
            sourcePub = pubReplaceDict[mqfSourcePub]
        elif mqfSourcePub not in current_lib_file_names:
            sourcePub = None
        else:
            sourcePub = mqfSourcePub
        
        # Print data for user
        print(f'question is {question}')
        print(f'Source: {paraRef}, {sourcePub}')
        answer = singleQuestionAsker(question, paraRef, sourcePub, bigDaaDy, sectionDaaDy)
        print(f'Answer: {answer}')
        if answer == None:
            brokenQuestions.append(num)
            continue

        # Create dictionary for mqf assessment
        mqfAssessmentDict[num] = {}
        mqfAssessmentDict[num]["question"] = question
        mqfAssessmentDict[num]["sourcepub"] = sourcePub
        mqfAssessmentDict[num]["paragraph"] = paraRef
        mqfAssessmentDict[num]["answer"] = answer
        ofile.write(f'mqfDict\t{num}\t{mqfAssessmentDict[num]["question"]}\t{mqfAssessmentDict[num]["answer"]}\t{mqfAssessmentDict[num]["paragraph"]}\n')

        # Check to see if answer begins with context Error.
        if answer[:errorLen] == contextError:
            sentenceOffenders.append(num)
        

# Asks unanswered questions to assigned Doc by setting reference to None
print('Working on sentenceOffenders.')
print(sentenceOffenders)
if len(sentenceOffenders) != 0:
    for sentenceNum in sentenceOffenders:
        if sentenceNum not in skippedQuestions:
            # Pull useful data from mqfDict (from MQF Parser)
            question = mqfDict[sentenceNum]["question"] 
            paraRef = mqfDict[sentenceNum]["paragraph"]
            # options = mqfDict[sentenceNum]["options"] # Currently not in use
            mqfSourcePub = mqfDict[sentenceNum]["reference"]

            # Check to see if sourcePub is in DaaDy library
            if mqfSourcePub in pubReplaceDict:
                sourcePub = pubReplaceDict[mqfSourcePub]
            elif mqfSourcePub not in current_lib_file_names:
                sourcePub = None
            else:
                sourcePub = mqfSourcePub

            # Print data for user
            print(f'question is {question}')
            print(f'Source: {paraRef}, {sourcePub}')
            answer = singleQuestionAsker(question, paraRef, sourcePub, bigDaaDy, sectionDaaDy)
            print(f'Answer: {answer}')

            # Create dictionary for mqf assessment
            mqfAssessmentDict[sentenceNum] = {}
            mqfAssessmentDict[sentenceNum]["question"] = question
            mqfAssessmentDict[sentenceNum]["sourcepub"] = sourcePub
            mqfAssessmentDict[sentenceNum]["paragraph"] = 'Unknown' # TODO pull from vector
            mqfAssessmentDict[sentenceNum]["answer"] = answer
            ofile.write(f'SentenceOffender\t{sentenceNum}\t{mqfAssessmentDict[sentenceNum]["question"]}\t{mqfAssessmentDict[sentenceNum]["answer"]}\t{mqfAssessmentDict[sentenceNum]["paragraph"]}\n')

            # Check to see if answer begins with context Error.
            if answer[:errorLen] == contextError:
                docOffenders.append(sentenceNum)
        
# Asks unanswered questions to entire corpus
print('Working on docOffenders.')
if len(docOffenders) != 0:
    for docNum in docOffenders:
        if docNum not in skippedQuestions:
            if docNum not in skippedQuestions:
                # Pull useful data from mqfDict (from MQF Parser)
                question = mqfDict[docNum]["question"] 
                paraRef = mqfDict[docNum]["paragraph"]
                # options = mqfDict[docNum]["options"] # Currently not in use
                mqfSourcePub = mqfDict[docNum]["reference"]

                # Check to see if sourcePub is in DaaDy library
                if mqfSourcePub in pubReplaceDict:
                    sourcePub = pubReplaceDict[mqfSourcePub]
                elif mqfSourcePub not in current_lib_file_names:
                    sourcePub = None
                else:
                    sourcePub = mqfSourcePub

                # Print data for user
                print(f'question is {question}')
                print(f'Source: {paraRef}, {sourcePub}')
                answer = singleQuestionAsker(question, paraRef, sourcePub, bigDaaDy, sectionDaaDy)
                print(f'Answer: {answer}')

                # Create dictionary for mqf assessment
                mqfAssessmentDict[docNum] = {}
                mqfAssessmentDict[docNum]["question"] = question
                mqfAssessmentDict[docNum]["sourcepub"] = 'Unknown' # TODO pull from vector
                mqfAssessmentDict[docNum]["paragraph"] = 'Unknown' # TODO pull from vector
                mqfAssessmentDict[docNum]["answer"] = answer
                ofile.write(f'docOffender\t{docNum}\t{mqfAssessmentDict[docNum]["question"]}\t{mqfAssessmentDict[docNum]["answer"]}\t{mqfAssessmentDict[docNum]["paragraph"]}\n')

                # Check to see if answer begins with context Error.
                if answer[:errorLen] == contextError:
                    totalOffenders.append(docNum)

    # Print results
    print(f'Status\tNum\tQuestion\tAnswer\tRef')
    for num in mqfAssessmentDict.keys():
        if num not in totalOffenders:
            # print(f'Answered\t{num}\t{mqfAssessmentDict[num]["question"]}\t{mqfAssessmentDict[num]["answer"]}\t{mqfAssessmentDict[num]["paragraph"]}')
            print(f'Answered\t{num}\t{mqfAssessmentDict[num]["question"]}\tAnswer\t{mqfAssessmentDict[num]["paragraph"]}')
            # ofile.write(f'Answered\t{num}\t{mqfAssessmentDict[num]["question"]}\tAnswer\t{mqfAssessmentDict[num]["paragraph"]}\n')
        else:
            # print(f'Unanswered\t{num}\t{mqfAssessmentDict[num]["question"]}\t{mqfAssessmentDict[num]["answer"]}\t{mqfAssessmentDict[num]["paragraph"]}')
            print(f'Unanswered\t{num}\t{mqfAssessmentDict[num]["question"]}\tAnswer\t{mqfAssessmentDict[num]["paragraph"]}')
            # ofile.write(f'Unanswered\t{num}\t{mqfAssessmentDict[num]["question"]}\tAnswer\t{mqfAssessmentDict[num]["paragraph"]}\n')
    print(f'Questions {totalOffenders} not answered due to insufficient context in the provided corpus.')

    ofile.closeFile()