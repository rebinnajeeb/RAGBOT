import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

load_dotenv()
working_dir = os.path.dirname(os.path.abspath((__file__)))

# Small + fast model keeps memory low on Streamlit's free tier
embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0
)

# In-memory vector store. Lives at module level so it stays populated across
# Streamlit reruns within the same process. No chromadb -> no protobuf/
# opentelemetry conflict, so the app actually boots on Streamlit Cloud.
vectorstore = InMemoryVectorStore(embedding)


def process_document_to_chroma_db(file_name):
    loader = PyPDFLoader(f"{working_dir}/{file_name}")
    documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=2000,
        chunk_overlap=200
    )
    texts = text_splitter.split_documents(documents)
    vectorstore.add_documents(texts)
    return 0


def answer_question(user_question):
    retriever = vectorstore.as_retriever()
    prompt = ChatPromptTemplate.from_template("""
    You are a helpful assistant answering questions about Muhammed Najeeb.

    Use the document context below to answer questions about his skills,
    projects, experience, and background.

    If the question is general (greetings, world knowledge),
    answer from your own knowledge.

    Context: {context}
    Question: {question}
    """)
    chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    return chain.invoke(user_question)
