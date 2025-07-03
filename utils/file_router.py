# utils/file_router.py
import os
from logger import get_logger
from ai_engine import (
    explain_code, debug_code, document_code, modularize_code
)
from rag_engine import query_rag

logger = get_logger("file_router", "logs/backend.log")

def handle_uploaded_file(file_path: str, action: str) -> str:
    ext = os.path.splitext(file_path)[-1].lower()

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        logger.info(f"📂 Handling file: {file_path} | Action: {action} | Extension: {ext}")

        # Python file logic
        if ext == ".py":
            if action == "explain":
                return explain_code("Python", content, "Intermediate")
            elif action == "debug":
                return debug_code("Python", content)
            elif action == "document":
                return document_code(content)
            elif action == "modularize":
                return modularize_code(content)
            else:
                return f"❌ Unknown action for Python file: {action}"

        # RAG for .txt, .md, or .pdf (extracted to text)
        elif ext in [".txt", ".md", ".pdf"]:
            if action == "rag":
                return query_rag(question=content)  # Treat entire content as question or pass context
            else:
                return f"❌ Unsupported action for document: {action}"

        else:
            return "❌ Unsupported file format"

    except Exception as e:
        logger.exception("❌ Error handling uploaded file")
        return f"❌ File processing error: {e}"
