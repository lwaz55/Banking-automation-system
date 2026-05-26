import os
from app.logger import logger

# Suppress chromadb telemetry and tokenizers warnings
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import chromadb
from chromadb.utils import embedding_functions

KNOWLEDGE_BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "knowledge_base")

# Use a lightweight sentence-transformer model
sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

_client = None
_collection = None

def _get_collection():
    """Gets or creates the ChromaDB in-memory collection, thread-safe."""
    global _client, _collection
    if _client is None:
        # EphemeralClient is in-memory — avoids all tenant/persistence threading issues
        _client = chromadb.EphemeralClient()
    if _collection is None:
        _collection = _client.get_or_create_collection(
            name="bct_policies",
            embedding_function=sentence_transformer_ef
        )
    return _collection


def initialize_rag():
    """Initializes the in-memory vector database with the BCT Circular."""
    collection = _get_collection()

    if collection.count() > 0:
        logger.info("[RAG] Vector database already initialized.")
        return

    logger.info("[RAG] Initializing Vector Database with BCT Circulars...")

    policy_path = os.path.join(KNOWLEDGE_BASE_DIR, "BCT_Circular_2024_01.md")
    if not os.path.exists(policy_path):
        logger.error(f"[RAG] Policy document not found at {policy_path}")
        return

    with open(policy_path, "r", encoding="utf-8") as f:
        content = f.read()

    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        # Advanced chunking using RecursiveCharacterTextSplitter
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            is_separator_regex=False,
        )
        chunks = text_splitter.split_text(content)
    except ImportError:
        logger.warning("[RAG] langchain-text-splitters not installed. Falling back to naive chunking.")
        # Fallback if package is not installed (e.g. before pip install)
        chunks = []
        current_chunk = []
        for line in content.split("\n"):
            if line.startswith("### Chapitre") or line.startswith("**Article"):
                if current_chunk:
                    chunks.append("\n".join(current_chunk))
                current_chunk = [line]
            else:
                if line.strip():
                    current_chunk.append(line)
        if current_chunk:
            chunks.append("\n".join(current_chunk))

    if not chunks:
        logger.warning("[RAG] No chunks extracted from policy document.")
        return

    # Insert chunks into ChromaDB
    ids = [f"bct_2024_01_chunk_{i}" for i in range(len(chunks))]
    metadatas = [{"source": "BCT Circular 2024-01"} for _ in chunks]

    collection.add(
        documents=chunks,
        metadatas=metadatas,
        ids=ids
    )
    logger.info(f"[RAG] Successfully loaded {len(chunks)} policy chunks into the knowledge base.")


def retrieve_policy(query: str, n_results: int = 2) -> str:
    """Searches the vector DB for the most relevant policy rules. Fault-tolerant."""
    try:
        collection = _get_collection()

        if collection.count() == 0:
            initialize_rag()

        if collection.count() == 0:
            return "No banking policies loaded."

        results = collection.query(
            query_texts=[query],
            n_results=min(n_results, collection.count())
        )

        if not results["documents"] or not results["documents"][0]:
            return "No specific banking policies found for this query."

        retrieved_texts = results["documents"][0]
        sources = results["metadatas"][0] if results.get("metadatas") else []

        formatted_rules = []
        for i, text in enumerate(retrieved_texts):
            source = sources[i].get("source", "BCT Circular 2024-01") if i < len(sources) else "BCT Circular 2024-01"
            formatted_rules.append(f"--- Rule from {source} ---\n{text}")

        return "\n\n".join(formatted_rules)

    except Exception as e:
        logger.warning(f"[RAG] retrieve_policy failed (will continue without citations): {e}")
        return "Policy retrieval temporarily unavailable."
