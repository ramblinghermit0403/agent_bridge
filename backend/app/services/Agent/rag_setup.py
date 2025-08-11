import os
import pinecone
from langchain_community.document_loaders import TextLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_pinecone import PineconeVectorStore

_retriever = None

def setup_rag_retriever() -> VectorStoreRetriever:
    """
    Sets up a RAG retriever using Pinecone, with robust logic for re-indexing.
    """
    global _retriever
    if _retriever is not None:
        return _retriever

    print("Setting up Pinecone retriever...")

    # --- Credentials and Embeddings (No change) ---
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")
    PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "company-kb")
    
    if not all([PINECONE_API_KEY, PINECONE_ENVIRONMENT]):
        raise ValueError("Pinecone environment variables are not set.")

    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )
    
    # --- NEW AND IMPROVED LOGIC ---
    pc = pinecone.Pinecone(api_key=PINECONE_API_KEY)

    if PINECONE_INDEX_NAME not in pc.list_indexes().names():
        print(f"Index '{PINECONE_INDEX_NAME}' does not exist. Creating it now...")
        pc.create_index(
            name=PINECONE_INDEX_NAME,
            dimension=768, 
            metric='cosine'
        )
        print("Index created successfully.")

    index = pc.Index(PINECONE_INDEX_NAME)

    # Check the stats BEFORE any operations
    stats = index.describe_index_stats()
    vector_count = stats.total_vector_count

    # Check for the force re-index flag
    if os.getenv("FORCE_REINDEX") == "true":
        # Only try to delete if there are vectors to delete
        if vector_count > 0:
            print(f"FORCE_REINDEX flag is set. Deleting all vectors from index '{PINECONE_INDEX_NAME}'...")
            # THE FIX: Explicitly target the default namespace to avoid the 404 error
            index.delete(delete_all=True, namespace="")
            print("All vectors deleted. The index will now be repopulated.")
            # Update the count after deletion
            vector_count = 0 
        else:
            print("FORCE_REINDEX flag is set, but index is already empty. Proceeding to populate.")
    
    # Now, check if the index is empty
    if vector_count == 0:
        print(f"Pinecone index '{PINECONE_INDEX_NAME}' is empty. Populating from source file...")
        
        # --- File loading logic with absolute path (BEST PRACTICE) ---
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # Assuming knowledge_base.txt is in the parent directory of the 'agent' folder
            file_path = os.path.join(current_dir, "..", "..", "knowledge_base.txt")
            loader = TextLoader(file_path, encoding="utf-8")
            docs = loader.load()
        except Exception as e:
            raise RuntimeError(f"Could not find or load knowledge_base.txt. Please ensure it exists. Error: {e}")
        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        splits = text_splitter.split_documents(docs)

        # Populate the index
        PineconeVectorStore.from_documents(
            splits,
            index_name=PINECONE_INDEX_NAME,
            embedding=embeddings,
            namespace="" # Be explicit about the namespace here too
        )
        print("Pinecone has been populated successfully.")
    else:
        print(f"Pinecone index is already populated with {vector_count} vectors.")

    # Connect to the populated store to create the retriever object
    vectorstore = PineconeVectorStore.from_existing_index(
        index_name=PINECONE_INDEX_NAME,
        embedding=embeddings,
        namespace="" # And be explicit here for consistency
    )
    _retriever = vectorstore.as_retriever()
    print("Pinecone retriever setup complete.")
    return _retriever