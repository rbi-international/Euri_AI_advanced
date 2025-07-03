# app.py
import streamlit as st
import requests
import base64
import pandas as pd
import json
from logger import get_logger
from token_utils import summarize_token_usage
from streamlit.components.v1 import html

logger = get_logger("frontend", "logs/frontend.log")

# ---------- Model Configuration ----------
MODEL_OPTIONS = {
    "gpt-3.5": {"tokens_per_call": 150, "cost_per_1k": 0.0015},
    "gpt-4.1-nano": {"tokens_per_call": 300, "cost_per_1k": 0.0025},
    "gpt-4": {"tokens_per_call": 500, "cost_per_1k": 0.03}
}

# ---------- Session State ----------
if "calls" not in st.session_state:
    st.session_state.calls = 0
if "total_cost" not in st.session_state:
    st.session_state.total_cost = 0.0
if "selected_model" not in st.session_state:
    st.session_state.selected_model = "gpt-4.1-nano"
if "rag_chat_history" not in st.session_state:
    st.session_state.rag_chat_history = []

# ---------- Sidebar ----------
st.set_page_config(page_title="Euriai AI Assistant", layout="wide")
st.sidebar.image("https://img.icons8.com/external-flat-juicy-fish/64/000000/external-coding-coding-and-development-flat-flat-juicy-fish.png", width=60)
st.sidebar.title("🤖 Euriai AI Assistant")

st.sidebar.markdown("### 🤖 Model Settings")
st.session_state.selected_model = st.sidebar.selectbox("Choose Model", list(MODEL_OPTIONS.keys()))

st.sidebar.markdown("---")
st.sidebar.markdown("### 💸 Usage Tracker")
st.sidebar.markdown(f"🔢 API Calls: **{st.session_state.calls}**")
st.sidebar.markdown(f"💰 Total Estimated Cost: **${st.session_state.total_cost:.4f}**")

# ---------- API URL ----------
API_URL = "http://127.0.0.1:8000"

# ---------- Streaming Function ----------
def fetch_streaming_explanation(payload):
    try:
        model_info = MODEL_OPTIONS[st.session_state.selected_model]
        tokens_used = model_info["tokens_per_call"]
        cost = (tokens_used / 1000) * model_info["cost_per_1k"]

        st.session_state.calls += 1
        st.session_state.total_cost += cost
        logger.info(f"🔁 Streaming with model: {st.session_state.selected_model}, Cost: ${cost:.4f}")

        response = requests.post(f"{API_URL}/explain_stream", json=payload, stream=True)
        placeholder = st.empty()

        is_code_block = False
        output_code = ""
        output_md = ""

        for line in response.iter_lines(decode_unicode=True):
            if not line or line.strip() == "" or line.strip() == "data: [DONE]":
                continue

            if line.startswith("data: "):
                line = line[6:]

            if not line.strip().startswith("{"):
                continue

            try:
                parsed = json.loads(line)
                token = parsed["choices"][0]["delta"].get("content", "")

                if "```" in token:
                    is_code_block = not is_code_block
                    if not is_code_block and output_code:
                        placeholder.code(output_code, language="python")
                        output_code = ""
                    continue

                if is_code_block:
                    output_code += token
                else:
                    output_md += token
                    placeholder.markdown(output_md, unsafe_allow_html=True)

            except Exception as ee:
                logger.warning(f"⚠️ Could not parse stream line: {line} — {ee}")
                continue

    except Exception as e:
        logger.exception("🚨 Streaming error")
        st.error(f"❌ Error during streaming: {e}")
        return None

# ---------- Request Wrapper ----------
def fetch_response(endpoint, payload):
    try:
        model_info = MODEL_OPTIONS[st.session_state.selected_model]
        tokens_used = model_info["tokens_per_call"]
        cost = (tokens_used / 1000) * model_info["cost_per_1k"]

        response = requests.post(f"{API_URL}/{endpoint}", json=payload)
        response.raise_for_status()
        data = response.json()

        st.session_state.calls += 1
        st.session_state.total_cost += cost

        logger.info(f"✅ Model: {st.session_state.selected_model}, Tokens: {tokens_used}, Cost: ${cost:.4f}")
        return data.get("response", "⚠️ Unexpected format")

    except Exception as e:
        logger.exception(f"❌ Error in /{endpoint}")
        return f"❌ API Error: {e}"

# ---------- Navigation ----------
choice = st.sidebar.radio(
    "Choose Action",
    ["📖 Explain Code", "🛠 Debug Code", "💡 Generate Code", "🧠 Ask Anything", "📂 Upload & Analyze", "📊 Usage Dashboard"]
)

# ---------- Explain Code ----------
if choice == "📖 Explain Code":
    st.header("📖 Explain Code")
    col1, col2 = st.columns(2)
    language = col1.selectbox("Language", ["Python", "JavaScript", "Java", "C++", "Go"])
    level = col2.selectbox("Level", ["Beginner", "Intermediate", "Advanced"])
    topic = st.text_input("🔍 Topic to Explain")

    if st.button("Explain"):
        st.subheader("🧠 Euriai Streaming Explanation")
        fetch_streaming_explanation({"language": language, "topic": topic, "level": level})

# ---------- Debug Code ----------
elif choice == "🛠 Debug Code":
    st.header("🛠 Debug Code")
    language = st.selectbox("Language", ["Python", "JavaScript", "Java", "C++", "Go"])
    topic = st.text_input("💣 Code topic to debug")

    if st.button("Debug"):
        result = fetch_response("debug", {"language": language, "topic": topic, "level": "Intermediate"})
        with st.expander("🐞 Debug Results"):
            st.markdown(result)

# ---------- Generate Code ----------
elif choice == "💡 Generate Code":
    st.header("💡 Code Generator")
    language = st.selectbox("Language", ["Python", "JavaScript", "Java", "C++", "Go"])
    topic = st.text_input("🧠 Topic for code generation")
    level = st.selectbox("Complexity", ["Beginner", "Intermediate", "Advanced"])

    if st.button("Generate"):
        result = fetch_response("generate", {"language": language, "topic": topic, "level": level})
        with st.expander("💡 Generated Code"):
            st.code(result, language=language.lower())

# ---------- Ask Anything ----------
elif choice == "🧠 Ask Anything":
    st.header("🧠 Ask AI Anything")
    question = st.text_area("Ask a concept or AI doubt")

    if st.button("Ask"):
        result = fetch_response("ask", {"question": question})
        with st.expander("🤖 AI Answer"):
            st.markdown(result)

# ---------- Upload & Analyze ----------
elif choice == "📂 Upload & Analyze":
    st.header("📂 Upload Code or Doc File")
    uploaded_file = st.file_uploader("Upload File", type=["py", "txt", "md", "pdf"])
    action = st.selectbox("Choose AI Action", ["explain", "debug", "document", "modularize", "rag"])

    if uploaded_file and st.button("Run AI Analysis"):
        try:
            files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
            data = {"action": action}
            with st.spinner("Analyzing with LLM..."):
                response = requests.post(f"{API_URL}/analyze_file", files=files, data=data)
                result = response.json()

            if "response" in result:
                output = result["response"]
                with st.expander(f"✅ {action.title()} Result"):
                    if action == "rag":
                        st.session_state.rag_chat_history.append({"question": uploaded_file.name, "answer": output})
                        for i, chat in enumerate(st.session_state.rag_chat_history):
                            st.markdown(f"**Q{i+1}:** {chat['question']}")
                            st.markdown(f"**A{i+1}:** {chat['answer']}")
                    else:
                        st.code(output, language="python")

                b64 = base64.b64encode(output.encode()).decode()
                href = f'<a href="data:file/txt;base64,{b64}" download="result_{action}.txt">📥 Download Result</a>'
                st.markdown(href, unsafe_allow_html=True)
            else:
                st.error(result.get("error", "❌ Unexpected error"))
        except Exception as e:
            logger.exception("❌ File Analysis Failed")
            st.error(f"❌ {e}")

# ---------- Usage Dashboard ----------
elif choice == "📊 Usage Dashboard":
    st.header("📊 Token Usage Summary")
    usage = summarize_token_usage()

    if usage:
        df = pd.DataFrame([
            {"Model": model, "Total Tokens": data["tokens"], "Total Cost ($)": round(data["cost"], 4)}
            for model, data in usage.items()
        ])

        df.sort_values("Total Cost ($)", ascending=False, inplace=True)
        st.dataframe(df.style.background_gradient(cmap='Blues'), use_container_width=True)

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download Usage Report CSV",
            data=csv,
            file_name="token_usage_report.csv",
            mime="text/csv"
        )
    else:
        st.warning("No usage data logged yet.")

# ---------- Footer ----------
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; font-size: 0.9em; color: gray;'>
        🔧 Built by <b>Rohit Bharti</b> • Powered by LLMs ⚙️<br><br>
        🙏 Special thanks to the <b>Euriai API</b> from 
        <a href='https://euron.one/' target='_blank'>Euron.one</a>,<br>
        managed by <a href='https://www.linkedin.com/in/-sudhanshu-kumar/?originalSubdomain=in' target='_blank'>
        <b>Sudhanshu Kumar</b></a> and his fantastic team 🌟<br>
        ❤️ Thanks to <a href='https://www.linkedin.com/in/boktiarahmed73/overlay/about-this-profile/' target='_blank'>Bappy Ahmed</a> for inspiration
    </div>
    """,
    unsafe_allow_html=True
)
