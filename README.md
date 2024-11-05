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

### SQUAD

### Research
#### In our paper we reference the true number of sentences in any string of characters. This was computed using the questionCounterbyCharacter code in this repo. 
