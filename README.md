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
  - 📈 **Complete Employment-based category support** (EB-1, EB-2, EB-3, EB-4, EB-5)
  - 👨‍👩‍👧‍👦 **Complete Family-based category support** (F1, F2A, F2B, F3, F4)
  - 🌍 Country-specific analysis (India, China, Mexico, Philippines, Worldwide)
  - 📅 Historical trend analysis and date advancement predictions
  - 🔍 **Advanced date parsing** with 67%+ success rate for State Department formats
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

### 🐳 Docker Mode (Recommended)
**Automatic startup with all services:**
```bash
# Option 1: Use helper script
python scripts/start_docker.py

# Option 2: Manual Docker compose
cd docker
docker-compose up --build
```

**Services available:**
- 🌐 **Frontend**: http://localhost:8501
- 🔌 **API**: http://localhost:8000
- 📖 **API Docs**: http://localhost:8000/docs
- 🗄️ **Database**: PostgreSQL (auto-configured)

### 🔧 Local Mode
**For development with SQLite:**
```bash
# Option 1: Use helper script (starts both API and frontend)
python scripts/start_local.py

# Option 2: Manual startup
# Terminal 1: Start API
python scripts/start_api.py

# Terminal 2: Start Frontend  
streamlit run src/main.py
```

**Services available:**
- 🌐 **Frontend**: http://localhost:8501
- 🔌 **API**: http://localhost:8000
- 📖 **API Docs**: http://localhost:8000/docs
- 🗄️ **Database**: SQLite (auto-configured)

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
- ✅ **Machine Learning Prediction Models** (NEW)
  - ✅ Random Forest regression for date advancement predictions
  - ✅ Logistic Regression for trend classification
  - ✅ Trend analysis with seasonal factors and volatility scoring
  - ✅ Country-specific prediction logic (India, China, etc.)
  - ✅ Model training, evaluation, and persistence utilities
  - ✅ Comprehensive test suite (23 tests) with 100% pass rate
- 🚧 Visa data collection and parsing (In progress)
- ✅ **Historical visa data collection system** (NEW)
  - ✅ **Complete visa category parsing** (all 10 categories: 5 EB + 5 FB)
  - ✅ **Advanced date parsing** with State Department format support ("15JAN23", "22APR24")
  - ✅ Automated collection of bulletins from 2020-2025 (25 bulletins collected)
  - ✅ **Dual-database architecture** (SQLite for local, PostgreSQL for Docker)
  - ✅ Monthly data fetching with CLI management tools
  - ✅ Data cleaning, validation, and quality reporting (100% success rate)
  - ✅ Advanced trend analysis and predictions
- 🚧 ML prediction models (In progress)
- 🚧 Interactive visa dashboard (Coming soon)
- 🚧 Memory persistence (Coming soon)

## 🏛️ Visa Bulletin Expertise

The AI agent now includes specialized expertise and analytical capabilities for US visa bulletin analysis:

### 📈 Supported Categories
- **Employment-Based**: EB-1, EB-2, EB-3, EB-4, EB-5 ✅ **FULLY SUPPORTED**
- **Family-Based**: F1, F2A, F2B, F3, F4 ✅ **FULLY SUPPORTED**

**Recent Enhancement**: Fixed Employment-Based category parsing to recognize State Department's ordinal format ("1st", "2nd", "3rd", etc.) and subcategory names ("Other Workers", "Certain Religious Workers", etc.)

### 🌍 Country Analysis
- India, China, Mexico, Philippines (special processing)
- Worldwide category tracking

### 🔮 Analysis Features
- **Complete historical data**: 25 bulletins with 850+ data entries
- **Advanced date extraction**: 67%+ success rate with State Department formats
- Historical trend analysis and pattern recognition
- Category movement analysis with context
- Country-specific expertise and insights
- Data-driven movement predictions with confidence scoring
- Expert-level explanations and analysis
- **Data quality management**: Automated validation and error detection

### 🛠️ Technical Implementation
- **Database Layer**: Abstract interface supporting SQLite and PostgreSQL
- **Repository Pattern**: Clean data access layer with validation
- **Factory Pattern**: Automatic database selection based on environment
- Machine learning models (Random Forest, Logistic Regression)
- Official State Department data parsing
- Real-time bulletin updates
- Interactive visualizations with Plotly
- Docker containerization with service orchestration

## 🤖 Machine Learning Prediction System

The application now includes advanced machine learning capabilities for visa bulletin forecasting, implemented in `src/visa/predictor.py`:

### 🎯 ML Models

**Random Forest Predictor** (`RandomForestPredictor`):
- **Purpose**: Regression-based date advancement predictions
- **Features**: Feature importance analysis, confidence scoring
- **Best for**: Precise date forecasting with uncertainty quantification

**Logistic Regression Predictor** (`LogisticRegressionPredictor`):
- **Purpose**: Hybrid classification + regression approach
- **Features**: Trend classification (advancing/stable/retrogressing) + magnitude prediction
- **Best for**: Trend analysis and interpretable predictions

### 📊 Feature Engineering

The system automatically extracts rich features from historical visa data:

- **Temporal Features**: Fiscal year, month, days since epoch
- **Trend Features**: Date advancement patterns, volatility scores, trend slopes
- **Seasonal Features**: Month-specific advancement factors
- **Country Features**: Country-specific processing factors (India: 0.3, China: 0.5, etc.)
- **Category Features**: Employment vs family-based encoding

### 🔬 Trend Analysis

**TrendAnalyzer Class**:
- Historical pattern recognition and seasonal factor calculation
- Volatility scoring for prediction uncertainty
- Trend direction classification (advancing/retrogressing/stable)
- Monthly advancement statistics

### 💻 Usage Examples

```python
from visa.predictor import create_predictor, TrendAnalyzer
from visa.database import VisaDatabase
from visa.models import VisaCategory, CountryCode

# Initialize system
db = VisaDatabase()
predictor = create_predictor('randomforest', db)

# Train model with historical data
metrics = predictor.train()
print(f"Model accuracy - MAE: {metrics['test_mae']:.2f} days")

# Make predictions
prediction = predictor.predict(
    category=VisaCategory.EB2,
    country=CountryCode.INDIA,
    target_month=8,
    target_year=2024
)

print(f"Predicted date: {prediction.predicted_date}")
print(f"Confidence: {prediction.confidence_score:.1%}")
print(f"Trend: {prediction.prediction_type}")

# Analyze historical trends
analyzer = TrendAnalyzer(db)
trend = analyzer.analyze_category_trend(VisaCategory.EB2, CountryCode.INDIA)
print(f"Average monthly advancement: {trend.average_monthly_advancement:.1f} days")
print(f"Trend direction: {trend.trend_direction}")
```

### 🛠️ Model Management

**Model Persistence**:
```python
# Save trained model
predictor.save_model('models/eb2_india_rf.pkl')

# Load pre-trained model
new_predictor = RandomForestPredictor(db)
new_predictor.load_model('models/eb2_india_rf.pkl')
```

**Model Evaluation**:
```python
from visa.predictor import ModelEvaluator

evaluator = ModelEvaluator(db)
models = [
    create_predictor('randomforest', db),
    create_predictor('logisticregression', db)
]

# Compare model performance
comparison = evaluator.compare_models(models)
recommendations = evaluator.get_model_recommendations()
```

### 🧪 Testing Infrastructure

**Comprehensive Test Suite** (`tests/test_visa_predictor.py`):
- ✅ **23 tests** covering all ML components
- ✅ **100% pass rate** with proper mocking
- ✅ **Feature extraction** testing with various data scenarios
- ✅ **Model training** validation with synthetic data
- ✅ **Prediction logic** testing including edge cases
- ✅ **Model persistence** save/load functionality
- ✅ **Integration tests** for end-to-end workflows

**Test Categories**:
- `TrendAnalyzer` tests: Historical analysis and seasonal factors
- `RandomForestPredictor` tests: Training, prediction, persistence
- `LogisticRegressionPredictor` tests: Classification + regression hybrid
- `ModelEvaluator` tests: Performance comparison utilities
- Factory function tests: Model creation and validation

### 🎨 Architecture Design

**Modular Design Principles**:
- **Pluggable Models**: Easy addition of new ML algorithms
- **Feature Engineering**: Automated extraction from historical data
- **Country-Specific Logic**: Tailored predictions per country/category
- **Confidence Scoring**: Reliability metrics for all predictions
- **Model Versioning**: Track model evolution and performance

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

## 📊 Historical Visa Bulletin Data Collection

The system includes a comprehensive historical data collection module for US visa bulletins with advanced analytics capabilities.

### 🎯 **Key Features**

#### ✅ **1. Historical Data Collection (2020-2025)**
- Multi-threaded collection with configurable workers
- URL verification and error handling
- Progress tracking and resumable collection
- Comprehensive logging and reporting

#### ✅ **2. Automated Monthly Data Fetching**
- Automated current bulletin fetching
- Cron job scheduling support  
- Status tracking and duplicate prevention
- Error handling and retry logic

#### ✅ **3. Data Cleaning and Normalization**
- **Complete category parsing**: All 10 visa categories (EB-1 through EB-5, F1 through F4)
- **Advanced date parsing**: State Department formats ("15JAN23", "22APR24") + standard formats
- **Employment-Based category recognition**: Ordinal formats ("1st", "2nd") and subcategories
- Category name standardization (EB1 → EB-1, etc.)
- Country name normalization
- Date format standardization to ISO format
- Status code normalization (C, U, DATE)
- **PostgreSQL compatibility**: Native date/datetime type handling

#### ✅ **4. Advanced Trend Analysis**
- Statistical trend analysis with momentum calculation
- Seasonal pattern detection
- Volatility and consistency scoring
- Category comparison across countries
- Prediction algorithms with confidence scoring

### 🚀 **Implementation Guide**

The visa data collection system supports both local development and Docker containerized environments with automatic mode detection.

#### 🖥️ **Local Mode Implementation**

**Setup:**
```bash
# 1. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure for local mode
cp .env.example .env
# Edit .env: set DOCKER_MODE=false
```

**Execute commands:**
```bash
# Collect historical data (uses SQLite)
python scripts/visa_data_manager.py collect --start-year 2020 --end-year 2025

# Fetch current bulletin
python scripts/visa_data_manager.py fetch

# Validate and clean data
python scripts/visa_data_manager.py validate --fix-errors

# Analyze trends
python scripts/visa_data_manager.py analyze --category EB-2 --country India

# Start web interface
streamlit run src/main.py
```

#### 🐳 **Docker Mode Implementation**

**Setup:**
```bash
# 1. Start all services (PostgreSQL, Redis, MongoDB, Streamlit)
cd docker
docker-compose up -d

# 2. Verify services are running
docker-compose ps
```

**Execute commands:**
```bash
# Collect historical data (uses PostgreSQL)
docker-compose exec web python scripts/visa_data_manager.py collect --start-year 2020 --end-year 2025

# Fetch current bulletin
docker-compose exec web python scripts/visa_data_manager.py fetch

# Validate and clean data
docker-compose exec web python scripts/visa_data_manager.py validate --fix-errors

# Analyze trends
docker-compose exec web python scripts/visa_data_manager.py analyze --category EB-2 --country India

# Web interface automatically available at http://localhost:8501
```

#### 🎯 **Quick Start Commands**

**Local Mode:**
```bash
# Complete setup and execution
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python scripts/visa_data_manager.py collect --start-year 2020 --end-year 2025
streamlit run src/main.py
```

**Docker Mode:**
```bash
# Complete setup and execution
cd docker && docker-compose up -d
docker-compose exec web python scripts/visa_data_manager.py collect --start-year 2020 --end-year 2025
# Access web UI at http://localhost:8501
```

#### 🔧 **Dual-Mode Architecture**

The system automatically detects the environment and configures itself:

**Environment Detection:**
- **Local Mode**: `DOCKER_MODE=false` → Uses SQLite database
- **Docker Mode**: `DOCKER_MODE=true` → Uses PostgreSQL database

**Database Selection:**
```python
# Automatic database selection via factory pattern
def get_database():
    if os.getenv('DOCKER_MODE', 'false').lower() == 'true':
        return PostgreSQLDatabase()  # Production ready
    else:
        return SQLiteDatabase()      # Local development
```

**Key Benefits:**
- ✅ **Seamless switching** between development and production environments
- ✅ **Same codebase** works in both modes without modification
- ✅ **Automatic configuration** based on environment variables
- ✅ **Database abstraction** ensures consistent behavior

### 🔄 **Automated Monthly Updates**

Set up cron job for automatic monthly updates:

**Local Mode:**
```bash
# Add to crontab (crontab -e)
0 6 * * * cd /path/to/project && /path/to/.venv/bin/python scripts/visa_data_manager.py fetch >> /var/log/visa_bulletin.log 2>&1
```

**Docker Mode:**
```bash
# Add to crontab (crontab -e)
0 6 * * * cd /path/to/project/docker && docker-compose exec -T web python scripts/visa_data_manager.py fetch >> /var/log/visa_bulletin.log 2>&1
```

### 📈 **Programmatic Usage**

```python
# Use the collection modules directly
from visa.collection import HistoricalDataCollector, MonthlyDataFetcher, DataValidator
from visa.analytics import TrendAnalyzer

# Historical collection
collector = HistoricalDataCollector()
results = collector.collect_historical_data(2020, 2025)

# Monthly fetching
fetcher = MonthlyDataFetcher()
bulletin = fetcher.fetch_current_bulletin()

# Data validation
validator = DataValidator()
validation_results = validator.validate_all_data()

# Trend analysis
analyzer = TrendAnalyzer()
trends = analyzer.calculate_advancement_trends(VisaCategory.EB2, CountryCode.INDIA)
```

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