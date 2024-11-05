from langchain.docstore.document import Document
from langchain_mistralai.chat_models import ChatMistralAI
from langchain_mistralai.embeddings import MistralAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from os import environ

def genSQUAD(sentenceDict):
    # Restructures sentenceDict for function
    indexOrgDict = {}
    index = 0
    for paraRef in sentenceDict.keys():
        for sentenceIndex in sentenceDict[paraRef].keys():
            splitSentence = sentenceDict[paraRef][sentenceIndex]["sentences"].split(" ")
            if len(splitSentence) >= 5: # Used to only generate sentences longer than 5 words. Modify this value if different min length desired.
                indexOrgDict[index] = {}
                indexOrgDict[index]["sentence"] = sentenceDict[paraRef][sentenceIndex]["sentences"]
                indexOrgDict[index]["reference"] = paraRef
                indexOrgDict[index]["waiver"] = sentenceDict[paraRef][sentenceIndex]["waiver"]
                index += 1

    # Define the embedding model
    api_key = environ["MISTRALAI_KEY"]
    embeddings = MistralAIEmbeddings(model="mistral-embed", mistral_api_key=api_key)
    # Define LLM
    model = ChatMistralAI(mistral_api_key=api_key)
    # Define prompt template
    prompt = ChatPromptTemplate.from_template("""Answer the following question based only on the provided context:
                                            
    <context>
    {context}
    </context>

    Question: {input}""")

    # Create empty dictionary for question generation
    questionGenDict = {}
    questionGenDict[index] = {}

    for totalSentenceIndex in range(len(indexOrgDict)):
        docs = []
        questionGenDict[totalSentenceIndex] = {}
        newDoc = Document(page_content=indexOrgDict[totalSentenceIndex]["sentence"])
        docs.append(newDoc)
        # Create the vector store 
        vector = FAISS.from_documents(docs, embeddings) 
        # Define a retriever interface
        retriever = vector.as_retriever()
        # Create a retrieval chain to answer questions
        document_chain = create_stuff_documents_chain(model, prompt)
        retrieval_chain = create_retrieval_chain(retriever, document_chain)
        response = retrieval_chain.invoke({"input": """You are given context that contains information. Generate a 
                                        question and answer pair that tests the reader's understanding of the information 
                                        contained within the prompt. Each question should provide sufficient context so 
                                        that the question does not require the context to be fully understood. Do not 
                                        reference the word 'context' in the question or answer. The question should have 
                                        a straightforward answer that can be easily verified with the context. In addition 
                                        to the question, provide the answer that is succinctly taken from the prompt. 
                                        Provide the question and answer in the following format:
                                        Question: Provide the question here.
                                        Answer: Provide the Answer here. Make the answer as concise as possible."""})
        fullAnswer = response["answer"]
        answerParts = fullAnswer.split("Answer:")
        question = answerParts[0][10:].lstrip().rstrip()
        reference = indexOrgDict[totalSentenceIndex]["reference"]
        if len(answerParts) > 1:
            answer = answerParts[1].lstrip().rstrip()
        else:
            answer = None
        questionGenDict[index]["question"] = question
        questionGenDict[index]["answer"] = answer
        questionGenDict[index]["reference"] = reference
        colonSplit = fullAnswer.split(":")
        if len(colonSplit) > 3:
            questionGenDict[index]["extra"] = colonSplit[3].lstrip().rstrip()
        else:
            questionGenDict[index]["extra"] = None
        extra = questionGenDict[index]["extra"]    
        
        # print(f'Question: {question}')
        # print(f'Answer: {answer}')
        # print(f'Reference: {reference}')
        # print(f'Extra Info: {extra}')
        
    return questionGenDict
