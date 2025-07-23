# 🤖 AI Agent Project

![CI](https://github.com/kenneth-fernandes/cisc691-a06/actions/workflows/ci.yml/badge.svg)

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
  - 📚 Layered architecture with clean separation
  - 🔄 Provider-agnostic design
  - 🛠️ Configuration management
  - 🗄️ Multi-database support (SQLite, PostgreSQL)
  - 🐳 Docker containerization with health checks

## 🚀 Setup

### 🐳 Docker Setup (Recommended)

For a complete environment with PostgreSQL, Redis, and MongoDB:

1. 📥 Clone the repository:
```bash
git clone [repository-url]
cd cisc691-a06
```

2. 🐳 Start Docker services:
```bash
cd docker
docker-compose up -d
```

This will start:
- 🗄️ PostgreSQL database (port 5432)
- 🔄 Redis cache (port 6379) 
- 📊 MongoDB (port 27017)
- 🌐 Streamlit web interface (port 8501)

3. ⚙️ Configure environment:
- The application will automatically use PostgreSQL in Docker mode
- Environment variables are configured in docker-compose.yml

### 🔧 Local Development Setup

For local development with SQLite:

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

### 🐳 Docker Mode
If using Docker, the application starts automatically:
- Access the UI at `http://localhost:8501`
- The application uses PostgreSQL database automatically

### 🔧 Local Mode
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

### Comprehensive Test Suite
Run the full test suite to verify functionality:
```bash
# Run all fast tests (recommended)
python run_tests.py --fast --coverage

# Run specific test categories
python run_tests.py --unit        # Unit tests only
python run_tests.py --integration # Integration tests only
python run_tests.py --mock        # Mock tests only

# Direct pytest usage
pytest tests/ -v                  # All tests
pytest tests/ -m "unit" -v        # Unit tests only
```

### Test Categories
- **🔬 Unit Tests**: Individual component testing (models, validators, parsers)
- **🔗 Integration Tests**: End-to-end workflow testing
- **🎭 Mock Tests**: Tests with mocked dependencies (no network calls)
- **🌐 Network Tests**: Real external API testing (optional)

### Coverage
Current test coverage: **90%+** for visa parsing system components
- `visa/models.py`: 90%
- `visa/config.py`: 96%
- `visa/parser.py`: 67%
- `visa/validators.py`: 53%

### Manual Test Scripts
```bash
# Manual agent tests (in scripts/ folder)
python scripts/test_agent.py      # Core agent functionality
python scripts/test_visa_agent.py # Visa bulletin expertise
```

## ⚙️ Configuration

### 🗄️ Database Configuration

The application supports multiple database backends:

**Docker Mode (PostgreSQL)**:
```env
DOCKER_MODE=true
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=app_db
POSTGRES_USER=admin
POSTGRES_PASSWORD=password
```

**Local Mode (SQLite)**:
```env
DOCKER_MODE=false
DATABASE_PATH=data/visa_bulletins.db
```

### 🤖 LLM Provider Configuration

Set your preferred provider in `.env`:
```env
# Use Google's free tier
LLM_PROVIDER=google
GOOGLE_MODEL=gemini-1.5-flash

# Or use local Ollama
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.2

# Or use OpenAI (requires API key)
LLM_PROVIDER=openai
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4o

# Or use Anthropic (requires API key)
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_api_key_here
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
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
- ✅ **Multi-database architecture** (NEW)
  - ✅ Abstract database interface
  - ✅ SQLite implementation for local development
  - ✅ PostgreSQL implementation for production
  - ✅ Factory pattern for automatic database selection
  - ✅ Docker containerization with health checks
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
- **Database Layer**: Abstract interface supporting SQLite and PostgreSQL
- **Repository Pattern**: Clean data access layer with validation
- **Factory Pattern**: Automatic database selection based on environment
- Machine learning models (Random Forest, Logistic Regression)
- Official State Department data parsing
- Real-time bulletin updates
- Interactive visualizations with Plotly
- Docker containerization with service orchestration

## 🗄️ Database Architecture

The application features a flexible, multi-database architecture designed for both development and production environments:

### 🏗️ Architecture Components

- **Abstract Interface**: `DatabaseInterface` defines standard CRUD operations
- **SQLite Implementation**: Lightweight database for local development and testing
- **PostgreSQL Implementation**: Production-ready database with advanced features
- **Factory Pattern**: Automatic database selection based on `DOCKER_MODE` configuration
- **Repository Layer**: Clean separation between business logic and data access

### 🔧 Database Implementations

**SQLite Database** (`src/database/sqlite.py`):
- File-based storage with automatic directory creation
- In-memory database support for testing
- Persistent connection handling for memory databases
- Full-text search capabilities

**PostgreSQL Database** (`src/database/postgresql.py`):
- Production-ready with connection pooling
- ACID compliance and advanced query optimization
- Docker integration with health checks
- Scalable for high-volume data processing

### 🧪 Testing Infrastructure

- **Comprehensive Test Suite**: Unit tests for both database implementations
- **In-Memory Testing**: Fast SQLite in-memory tests for CI/CD
- **Integration Tests**: End-to-end testing with real database operations
- **Mock Testing**: Isolated testing with dependency injection

### 📊 Supported Operations

All database implementations support:
- Visa bulletin storage and retrieval
- Category-specific historical data queries
- Prediction result storage and analysis
- Database statistics and health monitoring
- Atomic transactions and data integrity

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