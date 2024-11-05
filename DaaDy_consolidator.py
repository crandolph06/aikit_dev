from InputFile import InputFile
import os

def consolidateDaadyTsvs(directory_path): # Point to input directory of .tsv files
    # Create high-level dictionary
    bigDaaDy = {} # Sentence-level
    sectionDaaDy = {} # Section-level

    # Bring in files from directory
    cwd = os.path.abspath(directory_path) 
    file_list = os.listdir(cwd)

    # Write lines from input file to bigDaaDy 
    for file in file_list:
        file_path = cwd + '/' + file
        docTitle = file.split(".")[0]
        bigDaaDy[docTitle] = {}
        sectionDaaDy[docTitle] = {}
        ifile = InputFile()
        ifile.setFileName(file_path)
        ifile.openFile()
        line = ifile.nextLine()
        while ifile.isEndOfFile() == 0:
            if line == '\n' or line == "" or line == '\t':
                line = ifile.nextLine()
            lineParts = line.split('\t')
            if len(lineParts) == 4:
                # print(lineParts)
                paraRef = lineParts[0]
                sentenceIndex = lineParts[1]
                text = lineParts[2]
                waiverAuth = lineParts[3]
                try:
                    bigDaaDy[docTitle][paraRef][sentenceIndex] = {}
                    bigDaaDy[docTitle][paraRef][sentenceIndex]["sentences"] = text
                    bigDaaDy[docTitle][paraRef][sentenceIndex]["waiver"] = waiverAuth
                except KeyError:
                    bigDaaDy[docTitle][paraRef] = {}
                    bigDaaDy[docTitle][paraRef][sentenceIndex] = {}
                    bigDaaDy[docTitle][paraRef][sentenceIndex]["sentences"] = text
                    bigDaaDy[docTitle][paraRef][sentenceIndex]["waiver"] = waiverAuth
                line = ifile.nextLine()

    ifile.closeFile()
    
    # Write sections to sectionDaaDy
    for docTitle in bigDaaDy.keys():
        sectionDaaDy[docTitle] = {}
        shortenedParaRefList = []
        for paraRef in bigDaaDy[docTitle].keys():
            paraRefParts = paraRef.split(".")
            shortenedRef = paraRefParts[0] + "." + paraRefParts[1] + "."
            shortenedRefLen = len(shortenedRef)
            if shortenedRef not in shortenedParaRefList:
                shortenedParaRefList.append(shortenedRef)
                sectionDaaDy[docTitle][shortenedRef] = ""
            if shortenedRef[:shortenedRefLen] == paraRef[:shortenedRefLen]:
                for sentenceIndex in bigDaaDy[docTitle][paraRef].keys():
                    sentence = bigDaaDy[docTitle][paraRef][sentenceIndex]["sentences"].lstrip().rstrip() + " "
                    sectionDaaDy[docTitle][shortenedRef] += sentence
    
    # Returns tuple of dictionaries
    return bigDaaDy, sectionDaaDy

