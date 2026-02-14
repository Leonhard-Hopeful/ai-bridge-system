import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

def upload_and_index_pdf(file_path, subject):
    """
    Processes a PDF and saves it to the ChromaDB with subject metadata.
    """
    # 1. Load the PDF
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} not found.")
        return

    loader = PyPDFLoader(file_path)
    documents = loader.load()

    # 2. Split into chunks (Optimized for technical notes)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=600, 
        chunk_overlap=100
    )
    chunks = text_splitter.split_documents(documents)

    # 3. Tag each chunk with the subject (Crucial for your Strict RAG)
    for chunk in chunks:
        chunk.metadata["subject"] = subject

    # 4. Embed and store
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vector_db = Chroma.from_documents(
        chunks, 
        embeddings, 
        persist_directory="app/db/chroma_expert"
    )
    
    print(f"✅ Successfully indexed {len(chunks)} chunks for {subject}.")

# --- RUN THIS TO UPLOAD ---
if __name__ == "__main__":
    # Example: Update these paths to your actual files
    upload_and_index_pdf("notes\Discrete-mathematics-Notes.pdf", "Discrete Mathematics")
    # upload_and_index_pdf("notes/Operations_Research.pdf", "Operations Research")