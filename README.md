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

- 📊 **US Visa Bulletin Predictions** (NEW):
  - 📈 Employment-based category forecasting (EB-1, EB-2, EB-3)
  - 👨‍👩‍👧‍👦 Family-based category predictions (F1, F2A, F2B, F3, F4)
  - 🌍 Country-specific analysis (India, China, Mexico, Philippines)
  - 📅 Historical trend analysis and date advancement predictions
  - 🤖 ML-powered forecasting using Random Forest and Logistic Regression
  - 📋 Interactive dashboard with charts and visualizations

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

## 🚀 Running the Application

1. Start the Streamlit application:
```bash
streamlit run src/main.py
```

2. Access the UI:
- Open your browser to `http://localhost:8501`
- Use the sidebar to select your preferred AI provider
- Start chatting with the AI agent

Features available:
- 🎨 Dark theme interface
- 🔄 Real-time provider switching
- ⏱️ Response timing display
- 💬 Persistent chat history
- 🔌 Multiple provider support

## 🧪 Testing

Run the test script to verify the core functionality:
```bash
# Test core agent functionality
python test_agent.py

# Test visa bulletin expertise
python test_visa_agent.py
```

Core Agent Test will:
- 🚀 Initialize the AI agent
- 💬 Run test conversations
- ⏱️ Show response timing
- 📜 Display conversation history

Visa Bulletin Test will:
- 🔄 Test movement analysis for visa categories
- 🔮 Generate predictions for future movements
- 📱 Explain current visa bulletin status
- 🌍 Provide country-specific insights

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
- ✅ Streamlit UI with dark theme
- ✅ Dynamic provider switching
- ✅ Real-time chat interface
- ✅ **Visa bulletin expertise and analysis** (NEW)
  - ✅ Category and country-specific insights
  - ✅ Movement analysis and predictions
  - ✅ Historical trend analysis
  - ✅ Expert system prompts and templates
- 🚧 Visa data collection and parsing (In progress)
- 🚧 ML prediction models (Coming soon)
- 🚧 Interactive visa dashboard (Coming soon)
- 🚧 Memory persistence (Coming soon)
- 🚧 Enhanced error handling (Coming soon)

## 🏛️ Visa Bulletin Expertise

The AI agent now includes specialized expertise and analytical capabilities for US visa bulletin analysis:

### 📈 Supported Categories
- **Employment-Based**: EB-1, EB-2, EB-3, EB-4, EB-5
- **Family-Based**: F1, F2A, F2B, F3, F4

### 🌍 Country Analysis
- India, China, Mexico, Philippines (special processing)
- Worldwide category tracking

### 🔮 Analysis Features
- Historical trend analysis and pattern recognition
- Category movement analysis with context
- Country-specific expertise and insights
- Data-driven movement predictions
- Expert-level explanations and analysis

### 🛠️ Technical Implementation
- Machine learning models (Random Forest, Logistic Regression)
- Official State Department data parsing
- Real-time bulletin updates
- Interactive visualizations with Plotly

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
- Advanced reasoning capabilities
- Enhanced memory management with persistence
- Error handling and fallback mechanisms
- Performance optimizations
- Additional provider integrations

---
*This project demonstrates the practical application of AI agent development concepts learned throughout the course.*