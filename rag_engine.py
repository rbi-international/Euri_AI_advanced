import re
import nltk
from logger import get_logger

logger = get_logger("rag_engine", "logs/backend.log")

# Try to import optional dependencies with error handling
try:
    from sentence_transformers import SentenceTransformer, util
    from sklearn.feature_extraction.text import TfidfVectorizer
    import numpy as np
    
    # Download required NLTK data
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt')
    
    model = SentenceTransformer("all-MiniLM-L6-v2")
    logger.info("✅ RAG engine initialized successfully")
    
except ImportError as e:
    logger.error(f"❌ RAG dependencies missing: {e}")
    model = None

# Optional: fallback if embedding fails
def clean_text(text):
    text = re.sub(r"[^\w\s]", "", text)
    return text.lower()

def chunk_text(text, max_tokens=200):
    from nltk.tokenize import sent_tokenize
    sentences = sent_tokenize(text)
    chunks, current_chunk = [], ""
    for sent in sentences:
        if len(current_chunk) + len(sent) < max_tokens:
            current_chunk += " " + sent
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sent
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks

def get_rag_context(document_text: str, question: str, top_k: int = 3) -> str:
    try:
        chunks = chunk_text(document_text)
        chunk_embeddings = model.encode(chunks, convert_to_tensor=True)
        question_embedding = model.encode(question, convert_to_tensor=True)

        similarities = util.pytorch_cos_sim(question_embedding, chunk_embeddings)[0]
        top_indices = similarities.argsort(descending=True)[:top_k]
        top_chunks = [chunks[i] for i in top_indices]

        return "\n\n".join(top_chunks)
    except Exception as e:
        return f"\u274c RAG Context Error: {e}"



