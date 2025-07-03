# main.py
from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from ai_engine import (
    explain_code, explain_code_stream, debug_code, generate_code,
    ask_generic_question, document_code, modularize_code
)
from rag_engine import get_rag_context
from logger import get_logger
from token_utils import log_token_usage
import os

logger = get_logger("main", "logs/backend.log")
app = FastAPI()

rag_session = {"document_text": "", "filename": ""}

class CodeRequest(BaseModel):
    language: str
    topic: str
    level: str

class AskRequest(BaseModel):
    question: str

class RAGRequest(BaseModel):
    question: str
    document_id: str = None

@app.post("/explain")
def explain(req: CodeRequest):
    logger.info("📖 /explain request")
    return {"response": explain_code(req.language, req.topic, req.level)}

from fastapi.responses import StreamingResponse, JSONResponse

@app.post("/explain_stream")
def explain_stream(req: CodeRequest):
    try:
        logger.info(f"🌊 Streaming explanation for: {req.topic}")
        stream = explain_code_stream(req.language, req.topic, req.level)
        return StreamingResponse(stream, media_type="text/plain")  # ✅ Corrected
    except Exception as e:
        logger.exception("❌ Error in /explain_stream")
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/debug")
def debug(req: CodeRequest):
    logger.info(f"🐞 Debug requested: {req.topic}")
    return {"response": debug_code(req.language, req.topic)}

@app.post("/generate")
def generate(req: CodeRequest):
    logger.info(f"💡 Generate code for: {req.topic}")
    return {"response": generate_code(req.language, req.topic, req.level)}

@app.post("/ask")
def ask(req: AskRequest):
    logger.info(f"🧠 Generic question: {req.question}")
    return {"response": ask_generic_question(req.question)}

@app.post("/analyze_file")
async def analyze_file(action: str = Form(...), file: UploadFile = File(...)):
    try:
        code = (await file.read()).decode("utf-8")
        logger.info(f"📄 Received file for action: {action}")

        if action == "explain":
            result = document_code(code)
        elif action == "debug":
            result = debug_code("Python", code)
        elif action == "document":
            result = document_code(code)
        elif action == "modularize":
            result = modularize_code(code)
        elif action == "rag":
            rag_session["document_text"] = code
            rag_session["filename"] = file.filename
            result = "✅ File ready for RAG. Now you can ask questions."
        else:
            result = "❌ Invalid action."

        return {"response": result}

    except Exception as e:
        logger.exception("❌ Error analyzing file")
        return {"error": f"Error analyzing file: {e}"}

@app.post("/rag_chat")
async def rag_chat(request: RAGRequest):
    try:
        document_text = rag_session.get("document_text", "")
        if not document_text:
            return {"error": "❌ No document uploaded for RAG."}

        logger.info(f"💬 RAG question received: {request.question}")
        context = get_rag_context(document_text, request.question, top_k=3)
        logger.debug(f"📚 Context used:\n{context[:500]}...")

        combined_prompt = f"Context:\n{context}\n\nQuestion: {request.question}"
        answer = ask_generic_question(combined_prompt)
        return {"response": answer}
    except Exception as e:
        logger.exception("❌ RAG chat error")
        return {"error": f"RAG chat failed: {e}"}
