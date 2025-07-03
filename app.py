# app.py - Complete Version with Persistent Document Chat
import streamlit as st
import requests
import base64
import pandas as pd
import json
import io
import os
from datetime import datetime
from logger import get_logger
from token_utils import summarize_token_usage

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)
logger = get_logger("frontend", "logs/app.log")

# ---------- Configuration ----------
MODEL_OPTIONS = {
    "gpt-3.5-turbo": {"tokens_per_call": 150, "cost_per_1k": 0.0015, "description": "Fast & Cost-effective"},
    "gpt-4.1-nano": {"tokens_per_call": 300, "cost_per_1k": 0.0025, "description": "Balanced Performance"},
    "gpt-4": {"tokens_per_call": 500, "cost_per_1k": 0.03, "description": "Maximum Capability"}
}

API_URL = "http://127.0.0.1:8000"

# ---------- Session State Management ----------
def initialize_session_state():
    defaults = {
        "calls": 0,
        "total_cost": 0.0,
        "selected_model": "gpt-4.1-nano",
        "messages": [],
        "document_loaded": False,
        "document_name": "",
        "document_content": "",
        "rag_active": False,
        "chat_session_active": False,
        "show_dashboard": False,
        "current_page": "home"
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

initialize_session_state()

# ---------- Page Configuration ----------
st.set_page_config(
    page_title="Euriai AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- Utility Functions ----------
def extract_text_from_pdf(pdf_file):
    """Extract text from PDF file using multiple methods"""
    try:
        from pypdf import PdfReader
        pdf_file.seek(0)
        pdf_content = pdf_file.read()
        pdf_reader = PdfReader(io.BytesIO(pdf_content))
        text = ""
        
        for page_num, page in enumerate(pdf_reader.pages):
            try:
                page_text = page.extract_text()
                if page_text.strip():
                    text += f"--- Page {page_num + 1} ---\n{page_text}\n\n"
            except Exception as page_error:
                logger.warning(f"Could not extract page {page_num + 1}: {page_error}")
                continue
        
        return text if text.strip() else "⚠️ PDF appears to be empty"
    except ImportError:
        return "❌ PDF processing library not available. Please install: pip install pypdf"
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        return f"❌ PDF extraction failed: {str(e)}"

def update_usage_stats():
    """Update API usage statistics with better tracking"""
    try:
        model_info = MODEL_OPTIONS[st.session_state.selected_model]
        tokens_used = model_info["tokens_per_call"]
        cost = (tokens_used / 1000) * model_info["cost_per_1k"]
        
        # Update session state
        st.session_state.calls += 1
        st.session_state.total_cost += cost
        
        # Log the usage
        logger.info(f"API Call #{st.session_state.calls}: Model={st.session_state.selected_model}, Cost=${cost:.4f}")
        
        # Force sidebar refresh
        st.rerun()
        
        return cost
    except Exception as e:
        logger.error(f"Error updating usage stats: {e}")
        return 0.0

def make_api_request(endpoint, payload):
    """Make API request with consistent tracking"""
    try:
        # Update usage stats first
        cost = update_usage_stats()
        
        # Make the request
        response = requests.post(f"{API_URL}/{endpoint}", json=payload, timeout=30)
        response.raise_for_status()
        
        logger.info(f"✅ API call successful: {endpoint}")
        return response
        
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ API request failed: {e}")
        st.error(f"🚨 API Request Failed: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        st.error(f"🚨 Unexpected Error: {str(e)}")
        return None

def process_document_for_rag(file_content, filename):
    """Process document for RAG and start chat session"""
    try:
        files = {"file": (filename, file_content.encode('utf-8', errors='ignore'))}
        data = {"action": "rag"}
        
        response = requests.post(f"{API_URL}/analyze_file", files=files, data=data, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            if "response" in result:
                # Set up persistent chat session
                st.session_state.document_loaded = True
                st.session_state.document_name = filename
                st.session_state.document_content = file_content
                st.session_state.rag_active = True
                st.session_state.chat_session_active = True
                
                # Add system message
                st.session_state.messages = [{
                    "role": "assistant",
                    "content": f"✅ **Document '{filename}' loaded successfully!**\n\n{result['response']}\n\nI'm ready to help you with any questions about this document. You can ask me to:\n- Explain concepts\n- Summarize sections\n- Create content based on the document\n- Answer specific questions\n- Generate code or text\n\n**What would you like to know?**"
                }]
                
                logger.info(f"Document processed for RAG: {filename}")
                return True
            else:
                st.error(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
                return False
        else:
            st.error(f"❌ Server error: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"Error processing document: {e}")
        st.error(f"❌ Error processing document: {str(e)}")
        return False

def send_rag_question(question):
    """Send question to RAG system"""
    try:
        response = requests.post(
            f"{API_URL}/rag_chat",
            json={"question": question},
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            if "response" in result:
                return result["response"]
            else:
                return f"❌ Error: {result.get('error', 'Unknown error')}"
        else:
            return f"❌ Server error: {response.status_code}"
            
    except Exception as e:
        logger.error(f"RAG question failed: {e}")
        return f"❌ Connection error: {str(e)}"

# ---------- Sidebar with Fixed Tracking ----------
with st.sidebar:
    st.markdown("# 🤖 Euriai AI Assistant")
    st.markdown("*Professional AI-Powered Code Assistant*")
    st.markdown("---")
    
    # Home Navigation
    st.markdown("### 🏠 Navigation")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🏠 Home", type="primary"):
            st.session_state.document_loaded = False
            st.session_state.rag_active = False
            st.session_state.chat_session_active = False
            st.session_state.messages = []
            st.rerun()
    with col2:
        if st.button("📊 Dashboard", type="secondary"):
            st.session_state.show_dashboard = True
            st.rerun()
    
    st.markdown("---")
    
    # Model Selection
    st.markdown("### ⚙️ Model Configuration")
    selected_model = st.selectbox(
        "Choose AI Model",
        options=list(MODEL_OPTIONS.keys()),
        format_func=lambda x: f"{x} - {MODEL_OPTIONS[x]['description']}",
        key="model_selector"
    )
    st.session_state.selected_model = selected_model
    
    # Model Info
    model_info = MODEL_OPTIONS[selected_model]
    st.info(f"📊 **Est. Tokens:** {model_info['tokens_per_call']}\n💰 **Cost per 1K:** ${model_info['cost_per_1k']}")
    
    st.markdown("---")
    
    # Usage Statistics - Fixed Display
    st.markdown("### 📈 Usage Statistics")
    
    # Create containers for dynamic updates
    calls_container = st.container()
    cost_container = st.container()
    
    with calls_container:
        st.metric("API Calls", st.session_state.calls)
    
    with cost_container:
        st.metric("Total Cost", f"${st.session_state.total_cost:.4f}")
    
    # Progress bar
    if st.session_state.total_cost > 0:
        progress = min(st.session_state.total_cost / 1.0, 1.0)
        st.progress(progress)
        st.caption(f"Progress towards $1.00 limit")
    
    st.markdown("---")
    
    # Document Status
    if st.session_state.document_loaded:
        st.markdown("### 📄 Active Document")
        st.success(f"📄 **{st.session_state.document_name}**")
        st.info("🤖 RAG Chat Active")
        
        if st.button("🗑️ Clear Document", type="secondary"):
            st.session_state.document_loaded = False
            st.session_state.rag_active = False
            st.session_state.chat_session_active = False
            st.session_state.messages = []
            st.rerun()
    
    # Quick Actions
    st.markdown("### ⚡ Quick Actions")
    if st.button("🔄 Reset Statistics", type="secondary"):
        st.session_state.calls = 0
        st.session_state.total_cost = 0.0
        st.rerun()

# ---------- Main Interface ----------
st.title("🤖 Euriai AI Assistant")
st.markdown("*Professional AI-Powered Development Assistant*")

# ---------- Page Router ----------
if st.session_state.get("show_dashboard", False):
    # Dashboard Page
    st.header("📊 Analytics Dashboard")
    
    # Back button
    if st.button("⬅️ Back to Home", type="secondary"):
        st.session_state.show_dashboard = False
        st.rerun()
    
    st.markdown("---")
    
    # Usage Analytics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total API Calls", st.session_state.calls)
    with col2:
        st.metric("Total Cost", f"${st.session_state.total_cost:.4f}")
    with col3:
        avg_cost = st.session_state.total_cost / max(st.session_state.calls, 1)
        st.metric("Average Cost/Call", f"${avg_cost:.4f}")
    
    # Historical data
    st.subheader("📋 Historical Usage")
    usage = summarize_token_usage()
    
    if usage:
        df = pd.DataFrame([
            {"Model": model, "Total Tokens": data["tokens"], "Total Cost ($)": round(data["cost"], 4)}
            for model, data in usage.items()
        ])
        st.dataframe(df, use_container_width=True)
        
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Export Historical Data",
            data=csv,
            file_name="euriai_usage_history.csv",
            mime="text/csv"
        )
    else:
        st.info("No historical usage data found")

elif st.session_state.chat_session_active:
    # RAG Chat Page
    st.header(f"💬 Chat Session: {st.session_state.document_name}")
    
    # Navigation breadcrumb
    st.markdown("**📍 Navigation:** 🏠 Home → 📁 Document Analysis → 💬 Chat Session")
    
    # Chat container
    chat_container = st.container()
    
    with chat_container:
        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Chat input
        if prompt := st.chat_input("Ask questions, request summaries, or ask me to create content..."):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Get AI response
            with st.chat_message("assistant"):
                with st.spinner("🤖 Thinking..."):
                    # Send to RAG system
                    ai_response = send_rag_question(prompt)
                    st.markdown(ai_response)
                    
                    # Add to chat history
                    st.session_state.messages.append({"role": "assistant", "content": ai_response})
                    
                    # Update usage stats
                    update_usage_stats()
    
    # Chat controls
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🏠 Back to Home", type="primary"):
            st.session_state.document_loaded = False
            st.session_state.rag_active = False
            st.session_state.chat_session_active = False
            st.session_state.messages = []
            st.session_state.current_page = "home"
            st.rerun()
    
    with col2:
        if st.button("🔄 New Chat", type="secondary"):
            st.session_state.messages = [{
                "role": "assistant", 
                "content": f"✅ **Chat cleared!** Document '{st.session_state.document_name}' is still loaded.\n\n**What would you like to know?**"
            }]
            st.rerun()
    
    with col3:
        if st.button("📄 Upload New", type="secondary"):
            st.session_state.document_loaded = False
            st.session_state.rag_active = False
            st.session_state.chat_session_active = False
            st.session_state.messages = []
            st.rerun()
    
    with col4:
        if st.button("💾 Export Chat", type="secondary"):
            chat_export = {
                "document": st.session_state.document_name,
                "timestamp": datetime.now().isoformat(),
                "messages": st.session_state.messages
            }
            st.download_button(
                "📥 Download Chat",
                json.dumps(chat_export, indent=2),
                f"chat_{st.session_state.document_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

else:
    # Home Page
    st.markdown("### 🏠 Welcome to Euriai AI Assistant")
    st.markdown("Choose how you'd like to interact with AI:")
    
    # Main action cards
    col1, col2 = st.columns(2)
    
    with col1:
        with st.container():
            st.markdown("#### 📁 Document Analysis & Chat")
            st.markdown("Upload any document and have an ongoing conversation with AI about it.")
            
            if st.button("🚀 Start Document Chat", type="primary"):
                st.session_state.current_page = "document_upload"
                st.rerun()
    
    with col2:
        with st.container():
            st.markdown("#### 🧠 Quick AI Assistant")
            st.markdown("Ask quick questions or generate code without uploading documents.")
            
            if st.button("💬 Quick Chat", type="primary"):
                st.session_state.current_page = "quick_chat"
                st.rerun()

# ---------- Document Upload Section ----------
if st.session_state.get("current_page") == "document_upload" and not st.session_state.chat_session_active:
    st.header("📁 Upload Document for AI Chat")
    
    # Back button
    if st.button("⬅️ Back to Home", type="secondary"):
        st.session_state.current_page = "home"
        st.rerun()
    
    uploaded_file = st.file_uploader(
        "Upload a document to start chatting",
        type=["py", "js", "txt", "md", "pdf", "docx"],
        help="Upload any document and I'll help you understand, analyze, and create content based on it"
    )
    
    if uploaded_file:
        st.success(f"✅ File uploaded: {uploaded_file.name}")
        
        # Preview section
        with st.expander("👁️ Preview Content"):
            try:
                if uploaded_file.type == "application/pdf":
                    content = extract_text_from_pdf(uploaded_file)
                    if not content.startswith("❌"):
                        st.text_area("Content Preview", content[:1000] + "..." if len(content) > 1000 else content, height=200)
                    else:
                        st.error(content)
                else:
                    try:
                        content = uploaded_file.read().decode("utf-8")
                        st.text_area("Content Preview", content[:1000] + "..." if len(content) > 1000 else content, height=200)
                        uploaded_file.seek(0)
                    except UnicodeDecodeError:
                        st.error("❌ Cannot preview this file type")
            except Exception as e:
                st.error(f"❌ Preview error: {str(e)}")
        
        # Process button
        if st.button("🚀 Start AI Chat with Document", type="primary"):
            with st.spinner("🔍 Processing document for AI chat..."):
                try:
                    # Get file content
                    if uploaded_file.type == "application/pdf":
                        file_content = extract_text_from_pdf(uploaded_file)
                        if file_content.startswith("❌"):
                            st.error(file_content)
                            st.stop()
                    else:
                        file_content = uploaded_file.read().decode("utf-8")
                    
                    # Process for RAG
                    if process_document_for_rag(file_content, uploaded_file.name):
                        st.success("✅ Document processed! Chat interface is now active.")
                        st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Processing failed: {str(e)}")

# ---------- Quick Chat Section ---------- 
elif st.session_state.get("current_page") == "quick_chat":
    st.header("🧠 Quick AI Assistant")
    
    # Back button
    if st.button("⬅️ Back to Home", type="secondary"):
        st.session_state.current_page = "home"
        st.rerun()
    
    # Quick feature tabs
    tab1, tab2, tab3 = st.tabs(["💬 Chat", "💡 Code Generator", "📖 Explainer"])
    
    with tab1:
        st.subheader("💬 Quick Chat")
        st.markdown("*Ask any programming or technical question*")
        
        if "quick_messages" not in st.session_state:
            st.session_state.quick_messages = []
        
        for message in st.session_state.quick_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        if prompt := st.chat_input("Ask me anything..."):
            st.session_state.quick_messages.append({"role": "user", "content": prompt})
            
            with st.chat_message("user"):
                st.markdown(prompt)
            
            with st.chat_message("assistant"):
                with st.spinner("🤖 Thinking..."):
                    response = make_api_request("ask", {"question": prompt})
                    if response:
                        result = response.json()
                        ai_response = result.get("response", "Sorry, I couldn't process your question.")
                        st.markdown(ai_response)
                        st.session_state.quick_messages.append({"role": "assistant", "content": ai_response})
    
    with tab2:
        st.subheader("💡 Code Generator")
        
        col1, col2 = st.columns(2)
        with col1:
            language = st.selectbox("Language", ["Python", "JavaScript", "Java", "C++", "Go"])
        with col2:
            complexity = st.selectbox("Complexity", ["Simple", "Intermediate", "Advanced"])
        
        description = st.text_area("Describe what you want to build:", height=100)
        
        if st.button("⚡ Generate Code", type="primary"):
            if description:
                with st.spinner("🤖 Generating code..."):
                    response = make_api_request("generate", {
                        "language": language,
                        "topic": description,
                        "level": complexity
                    })
                    if response:
                        result = response.json()
                        st.code(result.get("response", "No code generated"), language=language.lower())
    
    with tab3:
        st.subheader("📖 Concept Explainer")
        
        col1, col2 = st.columns(2)
        with col1:
            language = st.selectbox("Programming Language", ["Python", "JavaScript", "Java", "C++", "Go"], key="explain_lang")
        with col2:
            level = st.selectbox("Level", ["Beginner", "Intermediate", "Advanced"], key="explain_level")
        
        topic = st.text_input("Topic to explain:", placeholder="e.g., decorators, async/await, recursion")
        
        if st.button("📖 Explain", type="primary"):
            if topic:
                with st.spinner("🤖 Explaining..."):
                    response = make_api_request("explain", {
                        "language": language,
                        "topic": topic,
                        "level": level
                    })
                    if response:
                        result = response.json()
                        st.markdown(result.get("response", "No explanation generated"))

# ---------- Footer ----------
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; padding: 20px; background-color: #262730; border-radius: 10px; margin-top: 2rem; border: 1px solid #404040;'>
        <h4 style='color: #ffffff; margin-bottom: 10px;'>🤖 Euriai AI Assistant</h4>
        <p style='color: #cccccc; margin-bottom: 15px;'>
            Professional AI-powered development assistant built with ❤️
        </p>
        <div style='display: flex; justify-content: center; gap: 20px; flex-wrap: wrap;'>
            <div style='text-align: center;'>
                <strong style='color: #ffffff;'>🔧 Developer</strong><br>
                <a href='#' style='color: #4CAF50; text-decoration: none;'>Rohit Bharti</a>
            </div>
            <div style='text-align: center;'>
                <strong style='color: #ffffff;'>⚡ Powered by</strong><br>
                <a href='https://euron.one/' target='_blank' style='color: #4CAF50; text-decoration: none;'>Euron API</a>
            </div>
            <div style='text-align: center;'>
                <strong style='color: #ffffff;'>🙏 Special Thanks</strong><br>
                <a href='https://www.linkedin.com/in/boktiarahmed73/' target='_blank' style='color: #4CAF50; text-decoration: none;'>Bappy Ahmed</a>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)