# 🤖 AI Agent Project

A flexible AI agent implementation using LangChain framework that supports multiple LLM providers and can run with both cloud and local models.

## ✨ Features

- 🔌 Multiple LLM Provider Support:
  - 🌐 Google Gemini (Free tier)
  - 💻 Ollama (Local, Free)
  - 🔷 OpenAI GPT (Paid)
  - 🟣 Anthropic Claude (Paid)

- 🎯 Core Capabilities:
  - 💬 Text-based chat interface
  - 🧠 Conversation memory
  - ⚙️ Configurable system prompts
  - ⏱️ Response timing metrics

- 🏗️ Architecture:
  - 🏭 Factory pattern for agent creation
  - 📚 Layered architecture
  - 🔄 Provider-agnostic design
  - 🛠️ Configuration management

## 🚀 Setup

1. 📥 Clone the repository:
```bash
git clone [repository-url]
cd cisc691-a06
```

2. 🌍 Create and activate virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. 📦 Install dependencies:
```bash
pip install -r requirements.txt
```

4. ⚙️ Configure environment:
- Copy `.env.example` to `.env`
- Add your API keys (if using cloud providers)
- For local setup, install Ollama:
  ```bash
  # Install Ollama
  curl -fsSL https://ollama.com/install.sh | sh
  
  # Pull Llama model
  ollama pull llama3.2
  ```

## 🧪 Testing

Run the test script to verify the setup:
```bash
python test_agent.py
```

The test will:
- 🚀 Initialize the AI agent
- 💬 Run test conversations
- ⏱️ Show response timing
- 📜 Display conversation history

## ⚙️ Configuration

Set your preferred provider in `.env`:
```
# Use Google's free tier
LLM_PROVIDER=google
GOOGLE_MODEL=gemini-1.5-flash

# Or use local Ollama
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.2
```

## 📊 Current Status

- ✅ Core agent implementation
- ✅ Multi-provider support
- ✅ Basic conversation functionality
- ✅ Test script with timing
- 🚧 Streamlit UI (Coming soon)
- 🚧 Advanced features (Coming soon)

## 📝 Assignment Information

This project was developed as part of the CISC 691 - Foundations of Next-Gen AI course assignment (A06: Building the AI Agent of Your Choice).

### 🎯 Assignment Objectives
- Develop a functional AI agent using modern frameworks
- Implement multiple provider support for flexibility
- Create a modular and extensible architecture
- Demonstrate practical AI integration skills

### 📚 Course Details
- **Course**: CISC 691 - Foundations of Next-Gen AI
- **Institution**: Harrisburg University
- **Term**: Summer 2025
- **Professor**: Donald O'Hara

### 👥 Contributors
- Tien Dinh
- Kenneth Peter Fernandes

### 📋 Future Enhancements
- Streamlit-based user interface
- Advanced reasoning capabilities
- Enhanced memory management
- Additional provider integrations

---
*This project demonstrates the practical application of AI agent development concepts learned throughout the course.*