from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from squadUtils import locateContext
from langchain.docstore.document import Document
from langchain_mistralai.embeddings import MistralAIEmbeddings
from langchain_community.vectorstores import FAISS
from os import environ
from langchain_mistralai.chat_models import ChatMistralAI
from langchain.text_splitter import RecursiveCharacterTextSplitter


# Define Question Asking Function
def questionAsker(mqf:dict, sourcepub:str, model, retriever):
    mistralAnswers = {}
    for num in mqf.keys():
        question = mqf[num]["question"]
        reference = mqf[num]["reference"]

        # Define prompt template
        prompt = ChatPromptTemplate.from_template("""Answer the following question as concisely as possible based only on the provided context.
                    If you are not sure of the answer, your answer should be "Insufficient context provided." 
                    Keep your answer short and to the point. Avoid using the words "the context" in your answer.
                    Provide the paragraph reference (example: 1.1. or 1.1.1.) where you found your answer.
                                                
        <context>
        {context}
        </context>

        Question: {input}""")

        # Create a retrieval chain to answer questions
        document_chain = create_stuff_documents_chain(model, prompt)
        retrieval_chain = create_retrieval_chain(retriever, document_chain)
        response = retrieval_chain.invoke({"input": question})
        if sourcepub == f'{reference}.txt':
            mistralAnswers[num] = response["answer"]
        else: 
            mistralAnswers[num] = "This question references a different document;  " + response["answer"]
    return mistralAnswers


def singleQuestionAsker(question, reference, sourcepub, sentenceDict, sectionDict, needsReference=False, localizedContext=True, fullText=None):
    if localizedContext == False and fullText == None:
        print(f'If localizedContext=False, fullText must be provided.')
        exit()
    docList = []
    contextList = locateContext([], sourcepub, reference, sentenceDict, sectionDict, forceSection=False)
    if len(contextList) > 0:
        for context, metadata in contextList:
            contextLen = len(context)
            if contextLen >= 4000: 
                rec_text_splitter = RecursiveCharacterTextSplitter(chunk_size=4000, chunk_overlap = 50)
                chunks = rec_text_splitter.split_text(context)
                for chunk in chunks:
                    chunkDoc = Document(page_content=chunk, metadata=metadata)
                    docList.append(chunkDoc)
            else: 
                contextDocument = Document(page_content=context, metadata=metadata)
                docList.append(contextDocument)
    else:
        print('contextList empty')
        answer = None
        return answer
        
    # Define LLM
    api_key = environ["MISTRALAI_KEY"]
    model = ChatMistralAI(mistral_api_key=api_key)
    embeddings = MistralAIEmbeddings(model="mistral-embed", mistral_api_key=api_key)

    # Create the vector store 
    try:
        vector = FAISS.from_documents(docList, embeddings)
    except KeyError:
        print('keyerror')
        return None

    # Define a retriever interface
    retriever = vector.as_retriever()

    # Define prompt template
    prompt_input = """Answer the following question as concisely as possible based only on the provided context.
                    If you are not sure of the answer, your answer should be "Insufficient context provided." 
                    Keep your answer short and to the point. Avoid using the words "the context" in your answer.
                                            
    <context>
    {context}
    </context>

    Question: {input}"""

    if needsReference == True:
        prompt_input = """Answer the following question as concisely as possible based only on the provided context.
                        If you are not sure of the answer, your answer should be "Insufficient context provided." 
                        Keep your answer short and to the point. Avoid using the words "the context" in your answer.
                        Provide the paragraph reference number after your answer in parantheses if there is one available. 
                        Example: Here is the answer to the question. (1.1.2.)
                                            
    <context>
    {context}
    </context>

    Question: {input}"""
        
    prompt = ChatPromptTemplate.from_template(prompt_input)

    # Create a retrieval chain to answer questions
    document_chain = create_stuff_documents_chain(model, prompt)
    retrieval_chain = create_retrieval_chain(retriever, document_chain)
    response = retrieval_chain.invoke({"input": question})
    answer = response["answer"]
    return answer