from InputFile import InputFile
import re

class MqfParser(InputFile):
    def initialize(self):
        self.name = ""              # MQF Name
        self.creation = ""	    	# Master Creation Date
        self.squadron = ""		    # Squadron
        self.source = ""			# Source
        self.modified = ""      	# Last Modified Date
        self.numQuestions = ""      # Number of Questions
        
    def __init__(self):
        self.initialize()			# initialize

    def getName(self):
       return self.name             # return MQF name
    
    def getSource(self):
        return self.source			# return the source
    
    def getCreation(self):
       return self.creation         # return the creation date
    
    def getModified(self):
       return self.modified         # return last modified date
    
    def getSquadron(self):
       return self.squadron         # return squadron
    
    def getNumQuestions(self):
       return self.numQuestions     # return number of questions
    
    def parseHeaderOne(self, mqf_file, keyname):
        line = mqf_file.nextLine()
        key_length = len(keyname)
        while len(line) < 1 and mqf_file.isEndOfFile() == 0:
            line = mqf_file.nextLine()
        return line[key_length+1:].rstrip().lstrip()
    
    def parseHeaderTwo(self, mqf_file, keyname1, keyname2):
        line = mqf_file.nextLine()
        key1_length = len(keyname1)
        while len(line) < 1 and mqf_file.isEndOfFile() == 0:
            line = mqf_file.nextLine()
        tokens = line.split(keyname2)
        value1 = tokens[0][key1_length+1:].rstrip().lstrip()
        value2 = tokens[1].rstrip().lstrip()
        return value1, value2


    def parseHeader(self, mqf_file):
        self.name, self.squadron = self.parseHeaderTwo(mqf_file, 'Name:', 'Squadron:')
        self.creation = self.parseHeaderOne(mqf_file, 'Master Creation Date:')
        self.modified = self.parseHeaderOne(mqf_file, 'Last Modified Date:')
        self.source, self.questions = self.parseHeaderTwo(mqf_file, 'Source:', 'Number of Questions:')

    def parseOption(self, line):
       tokens = line.split(". ")
       return tokens[0].lstrip().rstrip(), tokens[1].lstrip().rstrip()

    def skipBlankLines(self, line, mqf_file):
        while len(line) < 1:
            line = mqf_file.nextLine()
        return line
    
    def regexParseQuestion(self, mqf_file):
        # Regex Patterns
        questionStartRegex = r'\d{1,4}\(\d{1,4}\)\.\s'
        questionRegex = r'\d{1,4}\(\d{1,4}\)\.\s(.*)'
        questionNumRegex = r'\d{1,4}\((.*)\)\.\s'
        testquestionNumRegex = r'(.*)\(\d+\)\.\s'
        referenceStartRegex = r'Ref\:\s'
        # referenceRegex = r'Ref\:\s(.*)'
        optionStartRegex = r'\s+[A-F]\.\s'
        # optionRegex = r'\s+[A-F]\.(.*)'
        # Skip leading blank lines
        line = mqf_file.getLine()
        while (len(line) < 1) and mqf_file.isEndOfFile() == 0:
            line = mqf_file.nextLine()
        # In Question
        if re.match(questionStartRegex, line):
            in_question = True
            num = re.search(testquestionNumRegex, line).group(1).lstrip().rstrip()
            # print(f'num is {num}')
            question = re.search(questionRegex, line).group(1).lstrip().rstrip()
            line = mqf_file.nextLine()
            if re.match(referenceStartRegex, line):
                in_question = False
            while len(line) > 0 and in_question:
                question += line.lstrip().rstrip()
                line = mqf_file.nextLine()
                if re.match(referenceStartRegex, line):
                    in_question = False
            while len(line) < 1 and mqf_file.isEndOfFile() == 0:
                line = mqf_file.nextLine()
            # print(f'{num}. Q: {question}')
            # In Reference
            fullref = line[5:].lstrip().rstrip()
            tokens = fullref.split(": ")
            if len(tokens) == 1:
                ref = tokens[0].lstrip().rstrip()
                para = None
            elif len(tokens) == 2:
                ref = tokens[0].removesuffix(" Para").lstrip().rstrip()
                para = tokens[1].lstrip().rstrip() + "."
            elif len(tokens) == 3:
                ref = tokens[0].removesuffix(" Chap").lstrip().rstrip()
                para = tokens[2].lstrip().rstrip()
            else:
                ref = ref = tokens[0].removesuffix(" Pg").lstrip().rstrip()
                para = tokens[3].lstrip().rstrip() + "."
            # print(f'Ref: {ref}, Para: {para}')
            # In Options
            options = {}
            in_options = True
            while mqf_file.isEndOfFile() == 0 and in_options:
                line = mqf_file.nextLine()
                if len(line) > 0:
                    if re.match(questionStartRegex, line):
                        in_options = False
                    else:
                        if re.match(optionStartRegex, line):
                            a, b = self.parseOption(line)
                            options[a] = b
                            while len(line) > 0 and re.match(optionStartRegex, line) == None and in_options:
                                options[a] += " " + line
                                line = mqf_file.nextLine()
            # print(f'Options: {options}')
            return num, question, ref, para, options
        else: 
           line = mqf_file.nextLine()
           return None, None, None, None, None

    def parseMqf (self, filename):
        mqf_file = InputFile()
        mqf_file.setFileName ( filename )
        mqf_file.openFile()
        self.parseHeader(mqf_file)
        answers = {}
        while ( mqf_file.isEndOfFile () == 0 ):
           num, question, ref, para, options = self.regexParseQuestion(mqf_file)
           if num != None:
              answers[num] = {}
              answers[num]["question"] = question
              answers[num]["reference"] = ref
              answers[num]["paragraph"] = para
              answers[num]["options"] = options
        mqf_file.closeFile()
        return answers

    def printQuestions(self, answers):
       for num in answers.keys():
          question = answers[num]["question"]
          ref = answers[num]["reference"]
          para = answers[num]["paragraph"]
          options = answers[num]["options"]
          print(f'{num}. Q: {question}')
          print(f'{num}. Ref: {ref}')
          for choice in options.keys():
             print(f'    {choice} :: {options[choice]}')

    def toTsv(self, answers):
        print(f'num\tquestion\treference\tparagraph\tA\tB\tC\tD\tE')
        for num in answers.keys():
            question = answers[num]["question"]
            ref = answers[num]["reference"]
            para = answers[num]["paragraph"]
            options = answers[num]["options"]
            print(f'{num}\t{question}\t{ref}\t{para}', end="")
            for choice in options.keys():
                print(f'\t{options[choice]}', end="")
            print()

def squadGenTSVtoDict(file_path, sourcepub):

    def checkForFullDict(num, questionDict):
        if not questionDict[num]["question"]:
            questionDict[num]["question"] == None
        if not questionDict[num]["answer"]:
            questionDict[num]["answer"] == None
        if not questionDict[num]["reference"]:
            questionDict[num]["reference"] == None
        if not questionDict[num]["paragraph"]:
            questionDict[num]["paragraph"] == None
        return questionDict[num]
    
    ifile = InputFile()
    ifile.setFileName(file_path)
    ifile.openFile()
    questionDict = {}
    line = ifile.nextLine()
    # print(line)
    num = 0
    while ifile.isEndOfFile() == 0:
        # print(num)
        if line == "" or line == '\n' or line == '\t':
            line = ifile.nextLine()
        if line[:10] == 'Question: ':
            question = line[10:]
            num += 1
            questionDict[num] = {}
            questionDict[num]['question'] = question
            questionDict[num]['reference'] = sourcepub
        elif line[:8] == 'Answer: ':
            answer = line[8:]
            questionDict[num]['answer'] = answer
        elif line[:11] == 'Reference: ':
            pararef = line[11:]
            questionDict[num]['paragraph'] = pararef
        else:
            extra = line
            questionDict[num]['extra'] = extra
            # print(f'{num}\n{question}\n{sourcepub}\n{answer}\n{pararef}\n{extra}')
            # checkForFullDict(num, questionDict)
        line = ifile.nextLine()
    ifile.closeFile()

    for num in questionDict.keys():
        try:
            question = questionDict[num]['question']
        except KeyError:
            questionDict[num]['question'] = None
        try:
            answer = questionDict[num]['answer']
        except KeyError:
            questionDict[num]['answer'] = None
        try:
            reference = questionDict[num]['reference']
        except KeyError:
            questionDict[num]['reference'] = None
        try:
            pararef = questionDict[num]['paragraph']
        except KeyError:
            questionDict[num]['paragraph'] = None
        try:
            extra = questionDict[num]['extra']
        except KeyError:
            questionDict[num]['extra'] = None
    return questionDict


# if ( __name__ == "__main__" ):
#     app = MqfParser()
#     # answers = app.parseMqf("local_mqf.txt")
#     # answers = app.parseMqf("instrument_exam_mqf.txt")
#     answers = app.parseMqf("acc_closed_book_mqf.txt")
# #     # app.printQuestions(answers)
#     app.toTsv(answers)

# file_path = '/Users/clairebieber/ai-kit/RAG/tools/QA/11-250_v5_full.txt'
# sourcepub = 'SHAWAFBI 11-250'

# questionDict = squadGenTSVtoDict(file_path, sourcepub)

