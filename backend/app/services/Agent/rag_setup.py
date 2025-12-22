import os
import pinecone
from langchain_community.document_loaders import TextLoader
# from langchain_google_genai import GoogleGenerativeAIEmbeddings # REMOVED
from langchain_pinecone import PineconeEmbeddings # ADDED
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_pinecone import PineconeVectorStore

_retriever = None

def setup_rag_retriever() -> VectorStoreRetriever:
    """
    Sets up a RAG retriever using Pinecone with hosted embeddings.
    Auto-ingestion is DISABLED to prevent quota loops.
    """
    global _retriever
    if _retriever is not None:
        return _retriever

    print("Setting up Pinecone retriever with hosted embeddings...")

    # --- Credentials ---
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT") # legacy, might not be needed for new client
    PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "company-kb")
    
    if not PINECONE_API_KEY:
        raise ValueError("PINECONE_API_KEY is not set.")

    # --- Hosted Embeddings (using Pinecone Inference) ---
    # Using 'multilingual-e5-large' as a strong default for hosted models.
    # If the user has a specific model configured in their index, 
    # they should ensure this matches or use the inference API directly.
    embeddings = PineconeEmbeddings(
        model="llama-text-embed-v2", 
        pinecone_api_key=PINECONE_API_KEY,
        query_params={"input_type": "query"},
        document_params={"input_type": "passage"}
    )
    
    # --- Initialization ---
    pc = pinecone.Pinecone(api_key=PINECONE_API_KEY)

    # Ensure index exists (idempotent check)
    if PINECONE_INDEX_NAME not in pc.list_indexes().names():
         print(f"Index '{PINECONE_INDEX_NAME}' does not exist. Please create it in the Pinecone console with hosted embeddings enabled.")
         # We do NOT auto-create here to avoid misconfiguration of hosted models.

    index = pc.Index(PINECONE_INDEX_NAME)
    
    # --- AUTO-POPULATION LOGIC DISABLED ---
    # The user requested to "not reembedd every time".
    # Existing data in the index is assumed to be sufficient.
    # To re-ingest, run a separate script or uncomment/flag this block temporarily.
    
    # stats = index.describe_index_stats()
    # vector_count = stats.total_vector_count
    # if vector_count == 0:
    #     print("Index is empty. Auto-ingestion is DISABLED by default.")
    # else:
    #     print(f"Index contains {vector_count} vectors.")

    # Connect to the store
    vectorstore = PineconeVectorStore.from_existing_index(
        index_name=PINECONE_INDEX_NAME,
        embedding=embeddings,
        namespace="" 
    )
    _retriever = vectorstore.as_retriever()
    print("Pinecone retriever setup complete (Hosted Embeddings).")
    return _retriever