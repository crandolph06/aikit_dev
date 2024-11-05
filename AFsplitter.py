import re

# Recursive Parser made for Air Force Instruction format

def afmanParser(file_path:str , tocContainsSeparators: bool, footerTitle: str):
    with open(file_path, 'r') as file:
        file_content = file.read()

    def parseTOC(text):
        # re pattern that provides text for full table of contents
        tocPattern = r'\nSUMMARY\sOF\sCHANGES\s+(\n|.)*Chapter\s1\s+\n'
        toc = re.search(tocPattern, text).group().lstrip().rstrip()
        return toc

    def parseBody(text):
        # re pattern that provides text for document body
        bodyPattern = r'\nChapter\s1\s+\n(\n|.)*Attachment\s1\s+\n'
        try: 
            body = re.search(bodyPattern, text).group(0).lstrip().rstrip()
        except AttributeError:
            body = text
        return body

    body = parseBody(file_content)
    # Fake end chapter added to ensure re pattern exists to capture last sentence of document
    fake_end_chapter = "1000.1. "

    # Recursively searches section of text for separators (e.g. 1.1., 1.2.) and returns dictionary of separators for that "level" 
    def separatorsToDict(layer, text, regexHeader, headerDelta):
        def createSeparators(layer, text, regexHeader, headerDelta):
            if re.findall(regexHeader, text) != []:
                separatorDict[layer] = regexHeader + r'\s'
                layer += 1
                regexHeader += headerDelta
                createSeparators(layer, text, regexHeader, headerDelta)
            else:
                separatorDict[layer] = regexHeader + r'\s'
        separatorDict = {}
        createSeparators(layer, text, regexHeader, headerDelta)
        return separatorDict
    
    # Removes separators from text
    def removeSeparators(text, separatorDict):
        for separatorDepth in separatorDict.keys():
            try:    
                matches = re.findall(separatorDict[separatorDepth], text)
                for match in matches:
                    text = text.replace(match, "")
            except AttributeError:
                pass
        return text

    # Key re Patterns 
    separatorMatch = r'\s+[0-9]+\.[0-9]+\.\s' # Base separator with end space (e.g. 1.1. , 3.1. )
    separatorFind = r'\s+[0-9]+\.[0-9]+\.' # Base separator without end space (e.g. 1.1., 3.1.)
    subseparator = r'[0-9]+\.' # Additive piece for separator (e.g. 1.)
    footerLeftRegex = r'[0-9]+\s+' + footerTitle + r'\s+' # re pattern for footer on left side
    footerRightRegex = r'\n' + footerTitle + r'\s+[0-9]+' # re pattern for footer on right side
    chapterHeadingRegex = r'Chapter\s[0-9]+\s+\b[A-Z]+(?:\s+[A-Z]+)*\b\s+' # re pattern for chapter heading

    # Generate dictionary of separators
    separatorDict = separatorsToDict(0, body, separatorFind, subseparator)

    # Text Processing
    body = body.replace(" -", "-") # Corrects punctuation errors from PDF parser
    body = body.replace("- ", "-") # Corrects punctuation errors from PDF parser
    leftFooterOccurrences = re.findall(footerLeftRegex, body)
    rightFooterOccurrences = re.findall(footerRightRegex, body)
    chapterOccurrences = re.findall(chapterHeadingRegex, body)
    removeOccurrences = rightFooterOccurrences + leftFooterOccurrences + chapterOccurrences 
    for occurrence in removeOccurrences: # Removes all footers and chapter headings
        body = body.replace(occurrence, "")
    split_text = body.split("\n")
    join_body = "".join(split_text)
    join_body = " " + join_body + "  " + fake_end_chapter 

    # Parse TOC and return list of top-level separators (i.e. two digit matches -- 1.1., 2.1., etc.)
    def findTopLevelMatches(topLevelRegex, tocContainsSeparators, text):
        toc = parseTOC(file_content)
        
        def tocToSeparators(toc, text):
            titlePattern = r'Chapter\s(.*)'
            chapterPattern = r'[0-9]+'
            chapterTitleList = re.findall(titlePattern, toc)
            chapterList = []
            twoDigMatchList = []
            for title in chapterTitleList:
                chapter = re.search(chapterPattern, title).group()
                if chapter not in chapterList:
                    subRegex = r'\s+' + chapter + r'\.[0-9]+\.\s+'
                    chapterSubsections = re.findall(subRegex, text)
                    for subsection in chapterSubsections:
                        subsection = subsection.lstrip().rstrip()
                        if subsection not in twoDigMatchList:
                            twoDigMatchList.append(subsection)
            return twoDigMatchList
        
        if tocContainsSeparators == True:
            fullTwodigMatches = re.findall(topLevelRegex, toc) 
        else:
            fullTwodigMatches = tocToSeparators(toc, text)
        return fullTwodigMatches

    fullTwodigMatches = findTopLevelMatches(separatorMatch, tocContainsSeparators, join_body)

    # Sorts two digit matches for typical order of AFIs (i.e. 10 after 9, not after 1)
    def sortTwoDigMatches(matches):
        listOfPairs = []
        for match in matches:
            match = match.lstrip().rstrip().removesuffix(".")
            # print(f'match is {match}')
            pieces = match.split(".")
            pieces[0] = int(pieces[0])
            pieces[1] = int(pieces[1])
            listOfPairs.append(pieces)
        sortedPairs = sorted(listOfPairs, key=lambda x: x[1])
        forRealSortedPairs = sorted(sortedPairs, key=lambda x: x[0])
        sortedMatches = []
        for pair in forRealSortedPairs:
            pair[0] = str(pair[0])
            pair[1] = str(pair[1])
            newMatch = pair[0] + "." + pair[1] + "."
            if newMatch not in sortedMatches:
                sortedMatches.append(newMatch)
        return sortedMatches
    
    fullTwodigMatches = sortTwoDigMatches(fullTwodigMatches)
    fullTwodigMatches.append(fake_end_chapter)

    # Creates new regex search pattern for next section
    def makeFullRegex(firstSegment, secondSegment):
        currentMatch = firstSegment.lstrip().rstrip()
        currentRegex = r'\s+' + re.escape(currentMatch)+ r'\s'
        nextMatch = secondSegment.lstrip().rstrip()
        nextRegex = r'\s+' + re.escape(nextMatch) + r'\s'
        subFullRegex = currentRegex + r'+(.*)' + nextRegex + "+"
        return subFullRegex

    # Cleans and saves sentences to docDict
    def makeSentences(docDict, match, section):
        waiverRegex = r'\s\(T(.*)\)'
        section = section.replace('. (T-', ' (T-')
        section = section.replace('.  (T-', ' (T-')
        sentences = section.split(". ") 
        for n, sentence in enumerate(sentences):
            docDict[match][n] = {}
            docDict[match][n]["sentences"] = sentence
            try:
                waiverAuth = re.search(waiverRegex, sentence)
                waiver = waiverAuth.group()
                docDict[match][n]["waiver"] = waiver
                if docDict[match][n]["sentences"][-1:] == ".":
                    waiver = waiver + "."
                    sentenceNoWaiver = sentence.removesuffix(waiver)
                    docDict[match][n]["sentences"] = sentenceNoWaiver
                else:
                    waiverAuth = waiver
                    sentenceNoWaiver = sentence.removesuffix(waiver)
                    docDict[match][n]["sentences"] = sentenceNoWaiver
            except AttributeError:
                docDict[match][n]["waiver"] = None

    # Takes full text and list of separators and returns tuple of sentenceDict, sectionDict
    def docParseToDict(firstMatchList:list, fullText:str):
        docDict = {}
        sectionsDict = {}        
        separatorCounter = 0
        
        # Start with full text, known headings and sections from TOC.
        for i, match in enumerate(firstMatchList): 
            if re.findall(separatorDict[separatorCounter], fullText) != [] and i < (len(firstMatchList) - 1): 
                currentMatchForSection = match.lstrip().rstrip() # e.g. 1.1.
                currentRegexForSection = r'\s+' + re.escape(currentMatchForSection)+ r'\s+'
                nextMatchForSection = firstMatchList[i+1].lstrip().rstrip() # e.g. 1.2.
                nextRegexForSection = r'\s+' + re.escape(nextMatchForSection) + r'\s+'
                fullRegexForSection = currentRegexForSection + r'(.*?)' + nextRegexForSection

                try:
                    section = " " + currentMatchForSection + " " + re.search(fullRegexForSection, fullText).group(1).lstrip().rstrip() + " " + nextMatchForSection + " "
                    cleanSection = removeSeparators(section, separatorDict)
                    sectionsDict[currentMatchForSection] = cleanSection

                except AttributeError:
                    # print(f'Regex search failed for {currentMatchForSection}. Regex was {fullRegexForSection}')
                    continue

                # Define recursive function to move from known sections to max separator length
                def recursiveDocParse(bracketedMatchList:list, separatorDict:dict, separatorCounter:int):

                    if bracketedMatchList != [] and separatorCounter < len(separatorDict):    

                        # Iterate through lower level headings to assess presence of new subsections
                        for x, subMatch in enumerate(bracketedMatchList):
                            if x <= (len(bracketedMatchList) - 2):        
                                # Create regex pattern from lower-level heading list
                                # Edge case from higher level to lower level (ex. X.X. to X.X.X.)
                                currentMatch = bracketedMatchList[x].lstrip().rstrip()
                                nextMatch = bracketedMatchList[x+1].lstrip().rstrip()
                                subFullRegex = makeFullRegex(currentMatch, nextMatch)

                                # Generate subsection between first and second heading.
                                # If subsection exists, create new heading list and recurse.
                                try:
                                    subsection = " " + currentMatch + " " + re.search(subFullRegex, section).group(1).lstrip().rstrip()

                                    # Search subsection for next level lower headings.
                                    if re.findall(separatorDict[separatorCounter + 2], subsection) != [] and separatorCounter < len(separatorDict):
                                        anotherSubSubMatchList = re.findall(separatorDict[separatorCounter + 2], subsection)
                                        anotherFullMatchList = [bracketedMatchList[x]]
                                        for anotherSubSubMatch in anotherSubSubMatchList:
                                            anotherFullMatchList.append(anotherSubSubMatch)
                                        anotherFullMatchList.append(bracketedMatchList[x+1])
                                        recursiveDocParse(x, lowMatchList, anotherFullMatchList, separatorDict, subsection, separatorCounter + 1)
                                    
                                    # If no further subsections exist:
                                    subsectionForPrinting = subsection.replace(currentMatch, "").lstrip().rstrip()

                                    try:
                                        if len(docDict[currentMatch]) != 0:
                                            pass
                                    except KeyError:
                                        docDict[currentMatch] = {}
                                        makeSentences(docDict, currentMatch, subsectionForPrinting)
                                except AttributeError:
                                    # print(f'Error: No subsection found between {currentMatch} and {nextMatch}.')
                                    pass

                # Create first sub-match list
                lowMatchList = re.findall(separatorDict[separatorCounter + 1], section)

                # Create full match list (current upper match, all submatches, next upper match)
                fullMatchList = [firstMatchList[i]]
                for match in lowMatchList:
                    fullMatchList.append(match)
                fullMatchList.append(firstMatchList[i + 1])

                # Call recursion
                recursiveDocParse(i, firstMatchList, fullMatchList, separatorDict, section, separatorCounter)

        return docDict, sectionsDict

    workingDict, sectionsDict = docParseToDict(fullTwodigMatches, separatorDict, join_body)
    return workingDict, sectionsDict