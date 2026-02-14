import os
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# Path to store the database
CHROMA_PATH = "app/db/chroma_expert"
DATA_PATH = "app/knowledge_base"

def load_and_index_docs():
    # 1. Load documents from your folder
    loader = DirectoryLoader(DATA_PATH, glob="**/*.pdf", loader_cls=PyPDFLoader)
    documents = loader.load()

    # 2. Split text into chunks (perfect for step-by-step logic)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=100,
        add_start_index=True,
    )
    chunks = text_splitter.split_documents(documents)

    # 3. Create Embeddings (Turning text into math coordinates)
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    # 4. Save to ChromaDB
    db = Chroma.from_documents(
        chunks, embeddings, persist_directory=CHROMA_PATH
    )
    print(f"Saved {len(chunks)} chunks to {CHROMA_PATH}")