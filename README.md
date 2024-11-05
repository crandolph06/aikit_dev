# AIKIT Dev
Development code for AIKIT Research Paper. 
https://doi.org/10.21203/rs.3.rs-5038817/v1

## Overview
#### This repository includes code used for research and development of our research paper (see above). This readme will describe how this code takes you from a text file to a Document as a Dictionary (DaaDy) and how to use Structured Question-Answer Dictionary Generation, and Assessment (SQUAD-G, SQUAD-A).

### Utilities
#### Input File and Output File are utilities from Darrell Ricke, Ph.D, of MIT Lincoln Laboratories. Thanks Darrell!!

### Parsers and Consolidator
#### AFSplitter is a recursive parser written to turn Air Force Instructions (AFIs) or Air Force Manuals (AFMANs) into a DaaDy. The DaaDy is a nested dictionary where the top level keys are the high-level numerical paragraph designators (e.g. 1.1., 1.2., etc.) and the low level values are the sentence text and waiver authority for each sentence. This parser uses re patterns. 
#### The DaaDy Consolidator takes multiple DaaDys (in .tsv format) and consolidates them into a consolidated DaaDy where the highest level key is the document title.
#### MQF Parser, should you choose to use master question files (MQFs), parses your MQF into a .tsv file.

### Basic Question Asker/Assessor
#### QuestionAsker contains the code where a single question is asked using Mistral RAG. Thanks Mistral!!
#### mistralQuestionAssessor contains code where pre-written questions (in our research, these came from MQFs and our own generated questions from SQUAD-G) are used as the question prompt in the QuestionAsker.

### SQUAD!
#### SQUAD-G code is contained in mistralRAGSquad. This function iterates through a DaaDy and, with our prompt, generates a question, answer, reference (QAR) triplet for each sentence of the document.
#### SQUAD-A code is contained in mistralSQUADAssessor. This function iterates through a dictionary of QARs and assesses whether the answer to the question is found in the referenced sentence of the text. 

### Research
#### In our paper we reference the true number of sentences in any string of characters. This was computed using the questionCounterbyCharacter code in this repo. 

### Contact
#### If you have questions or need help with this code, don't hesitate to contact me! Thank you and happy learning!
