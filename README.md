# 🤖 Euriai AI Coding Assistant

An AI-powered interactive coding assistant built with **Streamlit** + **FastAPI**, powered by the **Euriai API from [Euron.one](https://euron.one)**.

---

## ✨ What's New?

We've transformed this assistant into a **Production-Ready AI Companion** with the following upgrades:

### 🧠 AI Capabilities:
- 📖 **Explain Code** (by topic, level, and language)
- 🛠 **Debug Code** (spot and explain bugs)
- 💡 **Generate Code** (with proper comments and structure)
- 🧠 **Ask Anything** (AI Q&A about concepts, logic, or development)
- 📂 **Upload Python Files** for AI-powered:
  - 📘 Explanation
  - 🐞 Debugging
  - 📚 Auto-Documentation (docstrings + comments)
  - 🧱 Modularization (split into functions, config, logger, dotenv)

---

## 💸 Dynamic Model Selection + Cost Tracking

You can now:
- Select different LLM models like `gpt-3.5`, `gpt-4.1-nano`, `gpt-4`
- Each model shows:
  - Estimated tokens used
  - Cost per call (based on per-1K pricing)
- 📊 Track:
  - Total API calls
  - Total estimated cost in real-time

---

## 🖼️ Streamlit UI Improvements

- 🧭 Sidebar Navigation (feels like an app!)
- 📂 Upload + analyze Python files
- 📘 Expandable results with `st.expander`
- 🧠 Model selector + usage tracker in sidebar
- 📥 Download result `.py` files with one click
- 🎨 Clean footer with gratitude & team credits

---

## 🙏 Acknowledgements

Special thanks to:
- The amazing **[Euriai API](https://euron.one)** by [Sudhanshu Kumar](https://www.linkedin.com/in/-sudhanshu-kumar/?originalSubdomain=in) and his team at Euron.one 🌟
- One of the best courses and mentors that inspired this journey:  
  **[Bappy Ahmed](https://www.linkedin.com/in/boktiarahmed73/overlay/about-this-profile/)** — thank you for your insightful guidance and uplifting support 🙌

---

## 🚀 Run Locally

```bash
# 1. Install requirements
pip install -r requirements.txt

# 2. Start backend
uvicorn main:app --reload

# 3. Start frontend
streamlit run app.py
