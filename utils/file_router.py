import os
from logger import get_logger
from ai_engine import (
    explain_code, debug_code, document_code, modularize_code
)
from rag_engine import get_rag_context

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
                # ✅ Fixed: get_rag_context needs (document_text, question)
                default_question = "What is this document about? Please summarize the main points."
                return get_rag_context(document_text=content, question=default_question)
            elif action == "explain":
                # Use AI to explain the document content
                return explain_code("Text", content, "Intermediate")
            elif action == "document":
                # Add documentation to the text file
                return document_code(content)
            else:
                return f"❌ Unsupported action '{action}' for document type"

        else:
            return f"❌ Unsupported file format: {ext}"

    except FileNotFoundError:
        logger.error(f"❌ File not found: {file_path}")
        return f"❌ File not found: {file_path}"
    except UnicodeDecodeError:
        logger.error(f"❌ Cannot decode file: {file_path}")
        return f"❌ Cannot read file '{file_path}' - file contains non-text data"
    except Exception as e:
        logger.exception("❌ Error handling uploaded file")
        return f"❌ File processing error: {e}"