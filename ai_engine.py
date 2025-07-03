import os
import json
import requests
from dotenv import load_dotenv
from logger import get_logger
from token_utils import log_token_usage
from rag_engine import get_rag_context

load_dotenv()
logger = get_logger("ai_engine", "logs/backend.log")

EURIAI_API_KEY = os.getenv("EURIAI_API_KEY")
EURIAI_API_URL = "https://api.euron.one/api/v1/euri/alpha/chat/completions"

HEADERS = {
    "Authorization": f"Bearer {EURIAI_API_KEY}",
    "Content-Type": "application/json"
}

def call_euriai_api(model: str, messages: list, temperature: float = 0.7, stream: bool = False):
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "stream": stream
    }
    logger.info(f"📡 Sending to Euriai API: {payload}")
    response = requests.post(EURIAI_API_URL, headers=HEADERS, json=payload, stream=stream)
    response.raise_for_status()
    return response

def explain_code(language: str, topic: str, level: str) -> str:
    try:
        log_token_usage("euriai")
        prompt = f"You are a coding instructor. Explain the concept '{topic}' in {language} for a {level} level developer. Use markdown with headings, paragraphs, code blocks, and tables."
        messages = [{"role": "user", "content": prompt}]
        res = call_euriai_api("gpt-4.1-nano", messages)
        return res.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.exception("❌ Error in explain_code")
        return f"Error: {e}"

def explain_code_stream(language: str, topic: str, level: str):
    try:
        log_token_usage("euriai")
        prompt = f"Explain '{topic}' in {language} for a {level} level developer. Use markdown formatting: # Headings, ```python code blocks```, tables, and visuals."
        messages = [{"role": "user", "content": prompt}]
        res = call_euriai_api("gpt-4.1-nano", messages, stream=True)

        buffer = ""
        yield "💬 Typing...\n\n"
        for line in res.iter_lines():
            if line:
                decoded = line.decode("utf-8")
                if decoded.strip().startswith("data: "):
                    decoded = decoded[6:]
                if decoded.strip() == "[DONE]":
                    break
                try:
                    parsed = json.loads(decoded)
                    delta = parsed["choices"][0].get("delta")
                    if delta and "content" in delta:
                        token = delta["content"]
                        buffer += token
                        yield token
                except Exception as parse_err:
                    logger.warning(f"⚠️ Could not parse line: {decoded}")
                    continue
        logger.info("✅ Full stream complete")
    except Exception as e:
        logger.exception("❌ Streaming Explanation Failed")
        yield f"❌ Error: {e}"

def debug_code(language: str, topic: str) -> str:
    try:
        log_token_usage("euriai")
        prompt = f"You're a senior developer. Help debug this {language} code issue: {topic}"
        messages = [{"role": "user", "content": prompt}]
        res = call_euriai_api("gpt-4.1-nano", messages)
        return res.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.exception("❌ Error in debug_code")
        return f"Error: {e}"

def generate_code(language: str, topic: str, level: str) -> str:
    try:
        log_token_usage("euriai")
        prompt = f"Generate {level} {language} code for topic: {topic} with best practices and comments."
        messages = [{"role": "user", "content": prompt}]
        res = call_euriai_api("gpt-4.1-nano", messages)
        return res.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.exception("❌ Error in generate_code")
        return f"Error: {e}"

def ask_generic_question(question: str) -> str:
    try:
        log_token_usage("euriai")
        messages = [{"role": "user", "content": question}]
        res = call_euriai_api("gpt-4.1-nano", messages)
        return res.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.exception("❌ Error in ask_generic_question")
        return f"Error: {e}"

def document_code(code: str) -> str:
    try:
        log_token_usage("euriai")
        prompt = f"Document this code clearly:\n\n{code}"
        messages = [{"role": "user", "content": prompt}]
        res = call_euriai_api("gpt-4.1-nano", messages)
        return res.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.exception("❌ Error in document_code")
        return f"Error: {e}"

def modularize_code(code: str) -> str:
    try:
        log_token_usage("euriai")
        prompt = f"Refactor this code into modular functions with clear docstrings:\n\n{code}"
        messages = [{"role": "user", "content": prompt}]
        res = call_euriai_api("gpt-4.1-nano", messages)
        return res.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.exception("❌ Error in modularize_code")
        return f"Error: {e}"

def explain_with_rag(document_text: str, question: str) -> str:
    try:
        log_token_usage("euriai")
        context = get_rag_context(document_text, question)
        prompt = f"Use this context to answer:\n\n{context}\n\nQuestion: {question}"
        messages = [{"role": "user", "content": prompt}]
        res = call_euriai_api("gpt-4.1-nano", messages)
        return res.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.exception("❌ Error in RAG explanation")
        return f"Error: {e}"
