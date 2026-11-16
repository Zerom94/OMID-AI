# 🚀 OMID AI - Autonomous Multi-Agent System

**OMID AI** is a fully autonomous, multi-agent AI system built with Python and FastAPI. It operates in a secure, sandboxed environment, allowing you to interact with specialized agents for coding, security auditing, content creation, and research.

## 🌟 Key Features
- 🧠 **Smart LLM Routing:** Dispatches tasks to specialist agents.
- 💾 **Persistent Memory (RAG):** SQLite-backed memory for user preferences and chat history.
- 💻 **Standalone Code Generation:** Production-ready Python scripts.
- 🛡️ **Real Ethical Hacking:** Executes real Nmap, Ping, and Whois scans.
- 🎨 **Cyberpunk UI:** Fully RTL, Glassmorphism dashboard with live SSE logs.

## 💻 Tech Stack
- **Backend:** Python, FastAPI, SQLite
- **AI Engine:** Groq API (openai/gpt-oss-120b)
- **Frontend:** HTML, CSS, JavaScript

---
*Developed by [Zerom94](https://github.com/Zerom94)*

## 🚀 Quick Start

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Zerom94/OMID-AI.git
   cd OMID-AI
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   Create a `.env` file and add your Groq API key:
   ```env
   GROQ_API_KEY="gsk_your_api_key_here"
   ```

4. **Start the LLM Router (Terminal 1):**
   ```bash
   python smart_router.py
   ```

5. **Start the Web Dashboard (Terminal 2):**
   ```bash
   python web_ui.py
   ```
   Access the dashboard at `http://localhost:8000`.
