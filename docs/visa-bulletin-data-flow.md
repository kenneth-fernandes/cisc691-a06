# Data Flow Architecture

## Overview
This document provides comprehensive diagrams and documentation of how the AgentVisa AI system processes visa bulletin data, integrates with multiple LLM providers, and delivers intelligent visa analytics through a modern microservices architecture.

## Simplified Data Flow

```mermaid
flowchart LR
    A[🌐 State Dept Website] --> B[📥 Web Scraper & Parser]
    B --> C[🔍 Data Validator]
    C --> D[💾 PostgreSQL/SQLite]
    D --> E[🤖 AI Agent System]
    E --> F[📱 Streamlit UI]
    D --> G[🔌 REST API]
    D --> H[📊 Analytics Engine]
    
    classDef source fill:#e3f2fd
    classDef process fill:#f3e5f5
    classDef storage fill:#e8f5e8
    classDef ai fill:#fce4ec
    classDef app fill:#fff3e0
    
    class A source
    class B,C,H process
    class D storage
    class E ai
    class F,G app
```

## Detailed System Architecture & Data Flow

```mermaid
flowchart TD
    %% External Data Sources
    subgraph EXTERNAL["External Services"]
        STATE_DEPT[US State Department<br/>travel.state.gov<br/>Visa Bulletins]
        OPENAI[OpenAI API<br/>GPT-4/3.5-turbo]
        ANTHROPIC[Anthropic API<br/>Claude 3.5 Sonnet]
        GOOGLE[Google Gemini API<br/>gemini-1.5-flash]
        OLLAMA[Ollama Local<br/>llama-3.2]
    end
    
    %% Data Collection Layer
    subgraph COLLECTION["Data Collection Layer"]
        MONTHLY[MonthlyDataFetcher<br/>collection/monthly.py]
        HISTORICAL[HistoricalDataCollector<br/>collection/historical.py]
        SCRAPER[VisaBulletinScraper<br/>parser.py]
        PARSER[VisaBulletinParser<br/>parser.py]
    end
    
    %% Data Processing Pipeline
    subgraph PROCESSING["Data Processing Pipeline"]
        DATE_EXTRACTOR[BulletinDateExtractor<br/>Extract dates & fiscal years]
        TABLE_PARSER[BulletinTableParser<br/>Parse HTML tables]
        VALIDATOR[BulletinValidator<br/>Data validation]
        CLEANER[DataCleaner<br/>Data normalization]
    end
    
    %% Data Storage Layer
    subgraph STORAGE["Storage & Cache Layer"]
        REPO[VisaBulletinRepository<br/>repository.py]
        DATABASE[VisaDatabase<br/>database.py]
        POSTGRES[(PostgreSQL<br/>Primary Database)]
        SQLITE[(SQLite<br/>Fallback Database)]
        REDIS[(Redis Cache<br/>Performance Layer)]
    end
    
    %% Analytics & ML Layer
    subgraph ANALYTICS["Analytics & ML Layer"]
        ANALYTICS_ENGINE[TrendAnalyzer<br/>analytics.py]
        ML_PREDICTOR[ML Predictor<br/>predictor.py - Random Forest]
        MODELS[Data Models<br/>models.py]
    end
    
    %% AI Agent System
    subgraph AGENT["AI Agent System"]
        FACTORY[Agent Factory<br/>factory.py]
        CORE[Multi-LLM Agent Core<br/>core.py]
        TOOLS[Visa Analytics Tools<br/>visa_tools.py]
        EXPERTISE[Visa Expert System<br/>visa_expertise.py] 
        BRIDGE[Data Bridge<br/>data_bridge.py]
    end
    
    %% API Layer
    subgraph API["API Gateway Layer"]
        FASTAPI[FastAPI Backend<br/>api/main.py]
        AGENT_ROUTER[Agent Router<br/>routers/agent.py]
        ANALYTICS_ROUTER[Analytics Router<br/>routers/analytics.py]
        CACHE_MW[Cache Middleware<br/>middleware/cache_middleware.py]
    end
    
    %% Frontend Layer
    subgraph FRONTEND["Frontend Layer"]
        STREAMLIT[Streamlit App<br/>main.py]
        CHAT[Chat Interface<br/>pages/chat.py]
        ANALYTICS_UI[Analytics Dashboard<br/>pages/analytics.py]
        PREDICTIONS[Visa Predictions<br/>pages/visa_prediction.py]
    end
    
    %% Data Flow Connections
    STATE_DEPT --> SCRAPER
    MONTHLY --> PARSER
    HISTORICAL --> PARSER
    SCRAPER --> PARSER
    
    PARSER --> DATE_EXTRACTOR
    PARSER --> TABLE_PARSER
    DATE_EXTRACTOR --> VALIDATOR
    TABLE_PARSER --> VALIDATOR
    VALIDATOR --> CLEANER
    CLEANER --> REPO
    
    REPO --> DATABASE
    DATABASE --> POSTGRES
    DATABASE --> SQLITE
    
    REPO --> ANALYTICS_ENGINE
    ANALYTICS_ENGINE --> ML_PREDICTOR
    ML_PREDICTOR --> MODELS
    
    BRIDGE --> ANALYTICS_ENGINE
    TOOLS --> BRIDGE
    CORE --> TOOLS
    CORE --> EXPERTISE
    FACTORY --> CORE
    
    AGENT_ROUTER --> FACTORY
    ANALYTICS_ROUTER --> ANALYTICS_ENGINE
    FASTAPI --> AGENT_ROUTER
    FASTAPI --> ANALYTICS_ROUTER
    FASTAPI --> CACHE_MW
    CACHE_MW --> REDIS
    
    CHAT --> FASTAPI
    ANALYTICS_UI --> FASTAPI
    PREDICTIONS --> FASTAPI
    STREAMLIT --> CHAT
    STREAMLIT --> ANALYTICS_UI
    STREAMLIT --> PREDICTIONS
    
    %% External AI Services
    CORE --> OPENAI
    CORE --> ANTHROPIC
    CORE --> GOOGLE
    CORE --> OLLAMA
    
    %% Styling with professional colors
    classDef external fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef collection fill:#f3e5f5,stroke:#c2185b,stroke-width:2px
    classDef processing fill:#e8f5e8,stroke:#388e3c,stroke-width:2px
    classDef storage fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef analytics fill:#fce4ec,stroke:#e91e63,stroke-width:2px
    classDef agent fill:#f1f8e9,stroke:#689f38,stroke-width:2px
    classDef api fill:#e0f2f1,stroke:#00695c,stroke-width:2px
    classDef frontend fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px
    
    class STATE_DEPT,OPENAI,ANTHROPIC,GOOGLE,OLLAMA external
    class MONTHLY,HISTORICAL,SCRAPER,PARSER collection
    class DATE_EXTRACTOR,TABLE_PARSER,VALIDATOR,CLEANER processing
    class REPO,DATABASE,POSTGRES,SQLITE,REDIS storage
    class ANALYTICS_ENGINE,ML_PREDICTOR,MODELS analytics
    class FACTORY,CORE,TOOLS,EXPERTISE,BRIDGE agent
    class FASTAPI,AGENT_ROUTER,ANALYTICS_ROUTER,CACHE_MW api
    class STREAMLIT,CHAT,ANALYTICS_UI,PREDICTIONS frontend
```

## Component Details

### 1. Data Sources & Entry Points

**External Source:**
- `travel.state.gov` - US State Department visa bulletin website
- Provides both current and historical bulletin data

**Entry Points:**
- **MonthlyDataFetcher** (`src/visa/collection/monthly.py:20`): Automated monthly collection
- **HistoricalDataCollector** (`src/visa/collection/historical.py:19`): Bulk historical data collection
- **Manual Fetch**: Direct parser usage

### 2. Web Scraping Layer

**VisaBulletinScraper** (`src/visa/parser.py:36`):
- Handles HTTP requests with proper headers
- Manages URL discovery and generation
- Provides URL verification functionality

**Key Methods:**
- `get_current_bulletin_url()` (`src/visa/parser.py:50`): Discovers current bulletin URL
- `generate_historical_bulletin_url()` (`src/visa/parser.py:85`): Creates historical URLs
- `fetch_bulletin_content()` (`src/visa/parser.py:74`): Retrieves HTML content

### 3. Content Parsing Pipeline

**BulletinDateExtractor** (`src/visa/parser.py:123`):
- Extracts bulletin dates from URLs and content
- Calculates fiscal years
- Handles multiple date formats

**BulletinTableParser** (`src/visa/parser.py:203`):
- Identifies visa-related HTML tables
- Parses employment-based (EB-1 to EB-5) and family-based (F1-F4) categories
- Extracts country-specific data (China, India, Mexico, Philippines, Worldwide)
- Handles various date formats (State Dept format: 15JAN23, numeric formats)

### 4. Data Model Creation

**VisaBulletin** (`src/visa/models.py:88`): Main bulletin container
**CategoryData** (`src/visa/models.py:45`): Individual category/country data
**Enums:**
- `VisaCategory` (`src/visa/models.py:11`): EB-1 through EB-5, F1-F4
- `CountryCode` (`src/visa/models.py:28`): Supported countries
- `BulletinStatus` (`src/visa/models.py:37`): Current, Unavailable, Date Specified

### 5. Validation & Storage

**BulletinValidator** (`src/visa/validators.py`):
- Validates bulletin structure and data integrity
- Checks date consistency and category completeness

**VisaBulletinRepository** (`src/visa/repository.py:16`):
- High-level CRUD operations
- Bulk import functionality
- Data cleaning and transformation

**VisaDatabase** (`src/visa/database.py`):
- SQLite database operations
- Schema management
- Data persistence

### 6. Configuration & Status

**VisaConfig** (`src/visa/config.py:10`):
- State Department URLs
- Supported categories and countries
- Database and caching settings

**Status Tracking:**
- `monthly_fetch_status.json`: Monthly fetch statistics
- `collection.log`: Detailed operation logs
- Database statistics and health checks

## Data Flow Patterns

### Monthly Collection Flow
1. **Scheduler/Cron** triggers `MonthlyDataFetcher`
2. **URL Discovery** finds current bulletin
3. **Content Parsing** extracts data
4. **Validation** ensures data quality
5. **Storage** saves to SQLite database
6. **Status Update** logs success/failure

### Historical Collection Flow
1. **Date Range** specified (e.g., 2020-2025)
2. **URL Generation** creates historical URLs
3. **Parallel Processing** fetches multiple bulletins
4. **Bulk Import** stores all valid data
5. **Progress Tracking** logs completion status

### Error Handling
- **Network Errors**: Retry logic with exponential backoff
- **Parsing Errors**: Skip invalid entries, log warnings
- **Validation Errors**: Detailed error reporting
- **Database Errors**: Transaction rollback, data integrity

## Application Integration

The stored data is consumed by:
- **Streamlit UI** (`src/ui/`): User interface for predictions
- **FastAPI Endpoints** (`src/api/`): REST API for external access
- **Analytics Dashboard**: Historical trend analysis
- **Prediction Engine** (`src/visa/predictor.py`): ML-based forecasting

## Performance Characteristics

- **Concurrent Processing**: Up to 5 parallel workers for historical collection
- **Caching**: 24-hour cache duration for frequently accessed data
- **Database**: SQLite for simplicity, PostgreSQL support available
- **Validation**: Comprehensive data quality checks
- **Monitoring**: Detailed logging and status tracking