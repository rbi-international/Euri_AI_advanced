# rag_engine.py - Properly Fixed
import re
import nltk
from logger import get_logger

logger = get_logger("rag_engine", "logs/backend.log")

# Global variables
model = None
util = None
sent_tokenize = None

# Try to import optional dependencies with error handling
try:
    from sentence_transformers import SentenceTransformer, util as st_util
    from sklearn.feature_extraction.text import TfidfVectorizer
    import numpy as np
    from nltk.tokenize import sent_tokenize
    
    # Download required NLTK data
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        logger.info("Downloading NLTK punkt tokenizer...")
        nltk.download('punkt')
    
    # Initialize model and util
    model = SentenceTransformer("all-MiniLM-L6-v2")
    util = st_util  # Now util is properly assigned
    logger.info("✅ RAG engine initialized successfully")
    
except ImportError as e:
    logger.error(f"❌ RAG dependencies missing: {e}")
    logger.error("Please install: pip install sentence-transformers scikit-learn nltk")
    model = None
    util = None
    
    # Fallback tokenizer
    def sent_tokenize(text):
        return text.split('. ')

def manual_cosine_similarity(query_embedding, chunk_embeddings):
    """Manual cosine similarity calculation as fallback"""
    try:
        import numpy as np
        
        # Normalize vectors
        query_norm = query_embedding / np.linalg.norm(query_embedding)
        chunk_norms = chunk_embeddings / np.linalg.norm(chunk_embeddings, axis=1, keepdims=True)
        
        # Calculate cosine similarity
        similarities = np.dot(chunk_norms, query_norm)
        return similarities
        
    except Exception as e:
        logger.error(f"Manual similarity calculation failed: {e}")
        return None

def get_rag_context(document_text: str, question: str, top_k: int = 3) -> str:
    """Get relevant context from document for RAG"""
    try:
        # Check if model and util are available
        if model is None or util is None:
            logger.warning("RAG model not available, using simple text search")
            return simple_text_search(document_text, question, top_k)
        
        # Normal RAG processing
        chunks = chunk_text(document_text)
        
        if not chunks:
            return "❌ No content found in document"
        
        # Encode chunks and question
        chunk_embeddings = model.encode(chunks, convert_to_tensor=True)
        question_embedding = model.encode(question, convert_to_tensor=True)

        # Calculate similarities using sentence-transformers util
        similarities = util.pytorch_cos_sim(question_embedding, chunk_embeddings)[0]
        top_indices = similarities.argsort(descending=True)[:top_k]
        top_chunks = [chunks[i] for i in top_indices]

        return "\n\n".join(top_chunks)
        
    except Exception as e:
        logger.error(f"RAG processing error: {e}")
        return simple_text_search(document_text, question, top_k)

def simple_text_search(document_text: str, question: str, top_k: int = 3) -> str:
    """Fallback text search when RAG model is unavailable"""
    try:
        # Simple keyword matching
        question_words = set(question.lower().split())
        chunks = chunk_text(document_text)
        
        if not chunks:
            return document_text[:1000]
        
        # Score chunks based on keyword overlap
        scored_chunks = []
        for chunk in chunks:
            chunk_words = set(chunk.lower().split())
            overlap = len(question_words.intersection(chunk_words))
            scored_chunks.append((overlap, chunk))
        
        # Sort by score and return top chunks
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        top_chunks = [chunk for _, chunk in scored_chunks[:top_k]]
        
        return "\n\n".join(top_chunks) if top_chunks else document_text[:1000]
        
    except Exception as e:
        logger.error(f"Fallback search error: {e}")
        return document_text[:1000]

def chunk_text(text, max_tokens=200):
    """Split text into chunks for RAG processing"""
    try:
        if sent_tokenize is None:
            # Fallback chunking
            words = text.split()
            chunks = []
            current_chunk = ""
            
            for word in words:
                if len(current_chunk) + len(word) < max_tokens:
                    current_chunk += " " + word
                else:
                    if current_chunk.strip():
                        chunks.append(current_chunk.strip())
                    current_chunk = word
            
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            
            return chunks
        
        # Normal NLTK tokenization
        sentences = sent_tokenize(text)
        chunks, current_chunk = [], ""
        
        for sent in sentences:
            if len(current_chunk) + len(sent) < max_tokens:
                current_chunk += " " + sent
            else:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = sent
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
        
    except Exception as e:
        logger.error(f"Chunking error: {e}")
        return [chunk.strip() for chunk in text.split('\n\n') if chunk.strip()]