from langchain_community.document_loaders import TextLoader
from langchain_mistralai.chat_models import ChatMistralAI
from langchain_mistralai.embeddings import MistralAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from MqfParserRegex import MqfParser
from questionAsker import questionAsker

import os

file_path = '/current_library/AFI 11-2F16V3_SHAWAFBSUP1.txt' # Point to input .txt file

# Load data
loader = TextLoader(file_path) 
docs = loader.load()

# Split text into chunks 
text_splitter = RecursiveCharacterTextSplitter()
documents = text_splitter.split_documents(docs)

# Define the embedding model
api_key = os.environ["API_KEY"]
embeddings = MistralAIEmbeddings(model="mistral-embed", mistral_api_key=api_key)

# Create the vector store 
vector = FAISS.from_documents(documents, embeddings)

# Define a retriever interface
retriever = vector.as_retriever()

# Define LLM
model = ChatMistralAI(mistral_api_key=api_key)

# Parse TSV
app = MqfParser()
answers = app.parseMqf("local_mqf.txt")
sourcepub = 'AFI 11-2F16V3_SHAWAFBSUP1'

# Call Question Asking Function and output dictionary
mistralAnswers = questionAsker(answers, sourcepub, model, retriever)

# # Print in Useful Format if desired
# print(f'num\tquestion\tmistralAnswer')
# for num in mistralAnswers.keys():
#     print(f'{num}\t{answers[num]["question"]}\t{mistralAnswers[num]}')

