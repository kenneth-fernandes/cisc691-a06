# Workflow Diagram Documentation

## System Architecture Overview

```mermaid
graph TB
    subgraph "Frontend Layer"
        UI[Streamlit UI<br/>src/main.py]
        CHAT[Chat Interface<br/>ui/pages/chat.py]
        ANALYTICS[Analytics Dashboard<br/>ui/pages/analytics.py]
        SIDEBAR[Navigation Sidebar<br/>ui/components/sidebar.py]
    end
    
    subgraph "API Layer"
        API[FastAPI Backend<br/>api/main.py]
        AGENT_ROUTER[Agent Router<br/>api/routers/agent.py]
        ANALYTICS_ROUTER[Analytics Router<br/>api/routers/analytics.py]
        AUTH_ROUTER[Auth Router<br/>api/routers/auth.py]
        CACHE[Cache Middleware<br/>api/middleware/cache_middleware.py]
    end
    
    subgraph "Agent System"
        FACTORY[Agent Factory<br/>agent/factory.py]
        CORE[AI Agent Core<br/>agent/core.py]
        VISA_EXPERT[Visa Expertise<br/>agent/visa_expertise.py]
        VISA_TOOLS[Visa Analytics Tools<br/>agent/visa_tools.py]
        DATA_BRIDGE[Data Bridge<br/>agent/data_bridge.py]
    end
    
    subgraph "Data Layer"
        MODELS[Data Models<br/>visa/models.py]
        DATABASE[Database Access<br/>visa/database.py]
        REPOSITORY[Data Repository<br/>visa/repository.py]
        PARSER[Bulletin Parser<br/>visa/parser.py]
        VALIDATOR[Data Validator<br/>visa/validators.py]
    end
    
    subgraph "External Systems"
        LLM_PROVIDERS[LLM Providers<br/>OpenAI, Anthropic, Google, Ollama]
        VISA_DB[(PostgreSQL/SQLite<br/>Visa Bulletins Database)]
    end
    
    %% Connections
    UI --> CHAT
    UI --> ANALYTICS
    UI --> SIDEBAR
    
    CHAT --> API
    ANALYTICS --> API
    
    API --> AGENT_ROUTER
    API --> ANALYTICS_ROUTER
    API --> AUTH_ROUTER
    API --> CACHE
    
    AGENT_ROUTER --> FACTORY
    FACTORY --> CORE
    CORE --> VISA_EXPERT
    CORE --> VISA_TOOLS
    CORE --> DATA_BRIDGE
    
    VISA_TOOLS --> MODELS
    DATA_BRIDGE --> DATABASE
    DATABASE --> REPOSITORY
    REPOSITORY --> VISA_DB
    
    CORE --> LLM_PROVIDERS
    PARSER --> MODELS
    VALIDATOR --> MODELS
    
    %% Styling
    classDef frontend fill:#e1f5fe
    classDef api fill:#f3e5f5
    classDef agent fill:#e8f5e8
    classDef data fill:#fff3e0
    classDef external fill:#ffebee
    
    class UI,CHAT,ANALYTICS,SIDEBAR frontend
    class API,AGENT_ROUTER,ANALYTICS_ROUTER,AUTH_ROUTER,CACHE api
    class FACTORY,CORE,VISA_EXPERT,VISA_TOOLS,DATA_BRIDGE agent
    class MODELS,DATABASE,REPOSITORY,PARSER,VALIDATOR data
    class LLM_PROVIDERS,VISA_DB external
```

## Agent Decision-Making Process

```mermaid
flowchart TD
    START([User Input Received]) --> MODE_CHECK{Agent Mode?}
    
    MODE_CHECK -->|General| GENERAL_FLOW[Process with Standard LLM]
    MODE_CHECK -->|Visa Expert| VISA_FLOW[Visa Expert Processing]
    
    VISA_FLOW --> DATA_CHECK{Data Available?}
    DATA_CHECK -->|No| FALLBACK_MSG[Return Data Unavailable Message]
    DATA_CHECK -->|Yes| CONTEXT_EXTRACT[Extract Visa Context<br/>Categories, Countries, Query Type]
    
    CONTEXT_EXTRACT --> TOOL_SELECT{Select Tool}
    
    TOOL_SELECT -->|Trend Analysis| TREND_TOOL[VisaTrendAnalysisTool]
    TOOL_SELECT -->|Category Comparison| COMP_TOOL[VisaCategoryComparisonTool]
    TOOL_SELECT -->|Movement Prediction| PRED_TOOL[VisaMovementPredictionTool]
    TOOL_SELECT -->|Summary Report| SUMMARY_TOOL[VisaSummaryReportTool]
    
    TREND_TOOL --> TOOL_EXEC[Execute Tool with Database Query]
    COMP_TOOL --> TOOL_EXEC
    PRED_TOOL --> TOOL_EXEC
    SUMMARY_TOOL --> TOOL_EXEC
    
    TOOL_EXEC --> TOOL_SUCCESS{Tool Success?}
    TOOL_SUCCESS -->|Yes| PROCESS_DATA[Process Tool Data with LLM]
    TOOL_SUCCESS -->|No| AGENT_EXECUTOR{Agent Executor Available?}
    
    AGENT_EXECUTOR -->|Yes| LANGCHAIN_AGENT[Use LangChain Agent Executor]
    AGENT_EXECUTOR -->|No| CONTEXT_INJECT[Inject Data Context into Prompt]
    
    LANGCHAIN_AGENT --> LLM_INVOKE[Invoke LLM with Tools]
    CONTEXT_INJECT --> LLM_INVOKE
    PROCESS_DATA --> FORMAT_RESPONSE[Format Intelligent Response]
    
    GENERAL_FLOW --> LLM_INVOKE
    LLM_INVOKE --> MEMORY_SAVE[Save to Conversation Memory]
    FORMAT_RESPONSE --> MEMORY_SAVE
    MEMORY_SAVE --> RESPONSE([Return Response to User])
    FALLBACK_MSG --> RESPONSE
    
    %% Error Handling
    TOOL_EXEC -->|Error| ERROR_LOG[Log Error]
    ERROR_LOG --> FALLBACK_PROCESSING[Fallback to Standard Processing]
    FALLBACK_PROCESSING --> LLM_INVOKE
    
    %% Styling
    classDef startEnd fill:#4caf50,color:white
    classDef decision fill:#ff9800,color:white
    classDef process fill:#2196f3,color:white
    classDef tool fill:#9c27b0,color:white
    classDef error fill:#f44336,color:white
    
    class START,RESPONSE startEnd
    class MODE_CHECK,DATA_CHECK,TOOL_SELECT,TOOL_SUCCESS,AGENT_EXECUTOR decision
    class GENERAL_FLOW,VISA_FLOW,CONTEXT_EXTRACT,TOOL_EXEC,PROCESS_DATA,LLM_INVOKE,FORMAT_RESPONSE,MEMORY_SAVE,CONTEXT_INJECT,LANGCHAIN_AGENT process
    class TREND_TOOL,COMP_TOOL,PRED_TOOL,SUMMARY_TOOL tool
    class FALLBACK_MSG,ERROR_LOG,FALLBACK_PROCESSING error
```

## Data Flow Sequence Diagram

```mermaid
sequenceDiagram
    participant User
    participant UI as Streamlit UI
    participant API as FastAPI
    participant Agent as AI Agent
    participant Tools as Visa Tools
    participant DB as Database
    participant LLM as LLM Provider
    
    User->>UI: Enter visa query
    UI->>API: POST /api/agent/chat
    API->>Agent: chat(user_input)
    
    alt Visa Expert Mode
        Agent->>Agent: Extract visa context
        Agent->>Tools: Select appropriate tool
        Tools->>DB: Query visa bulletin data
        DB-->>Tools: Return historical data
        Tools-->>Agent: Return formatted data
        Agent->>LLM: Process data with context
        LLM-->>Agent: Generate intelligent response
    else General Mode
        Agent->>LLM: Direct query processing
        LLM-->>Agent: Generate response
    end
    
    Agent->>Agent: Save to conversation memory
    Agent-->>API: Return response
    API-->>UI: JSON response with content
    UI-->>User: Display formatted response
    
    Note over User,LLM: Response includes data-driven insights,<br/>trends, and predictions when available
```

## User Interaction Flow

```mermaid
journey
    title User Journey - Visa Analytics System
    section Initial Access
      Launch Application: 5: User
      Select Page (Chat/Analytics): 4: User
      Configure Agent Settings: 3: User
    section Chat Interaction
      Enter Visa Query: 5: User
      Processing Indicator: 3: System
      Receive AI Response: 5: User, System
      Review Data Insights: 4: User
    section Analytics Dashboard
      View Trend Charts: 4: User
      Filter by Categories: 4: User
      Export Reports: 3: User
    section Advanced Features
      Compare Categories: 4: User
      Predict Movements: 5: User
      Historical Analysis: 4: User
```

## Component Interaction Matrix

| Component | Streamlit UI | FastAPI | Agent Core | Visa Tools | Database |
|-----------|--------------|---------|------------|------------|----------|
| **Streamlit UI** | ✓ | HTTP REST | - | - | - |
| **FastAPI** | CORS/JSON | ✓ | Direct Call | - | - |
| **Agent Core** | - | Response | ✓ | Tool Integration | Via Tools |
| **Visa Tools** | - | - | Data Provider | ✓ | SQL Queries |
| **Database** | - | - | - | Data Storage | ✓ |

## Technology Stack Overview

```mermaid
graph LR
    subgraph "Frontend"
        ST[Streamlit 1.28+]
        HTML[HTML/CSS/JS]
    end
    
    subgraph "Backend"
        FA[FastAPI 0.104+]
        UV[Uvicorn ASGI]
    end
    
    subgraph "AI/ML"
        LC[LangChain 0.1+]
        OPENAI[OpenAI GPT]
        ANTHROPIC[Claude]
        GOOGLE[Gemini]
        OLLAMA[Ollama Local]
    end
    
    subgraph "Database"
        PG[PostgreSQL]
        SL[SQLite]
        CACHE[Redis Cache]
    end
    
    subgraph "Infrastructure"
        DOCKER[Docker Compose]
        NGINX[Nginx Proxy]
    end
    
    ST --> FA
    FA --> LC
    LC --> OPENAI
    LC --> ANTHROPIC
    LC --> GOOGLE
    LC --> OLLAMA
    FA --> PG
    FA --> SL
    FA --> CACHE
    DOCKER --> ST
    DOCKER --> FA
    DOCKER --> PG
    NGINX --> DOCKER
```

## Database Schema Visualization

```mermaid
erDiagram
    VISA_BULLETINS ||--o{ CATEGORY_DATA : contains
    VISA_BULLETINS {
        int id PK
        date bulletin_date
        int fiscal_year
        int month
        int year
        string source_url
        datetime created_at
        datetime updated_at
    }
    
    CATEGORY_DATA {
        int id PK
        int bulletin_id FK
        string category
        string country
        date final_action_date
        date filing_date
        string status
        string notes
        datetime created_at
    }
    
    PREDICTIONS ||--o{ CATEGORY_DATA : references
    PREDICTIONS {
        int id PK
        string category
        string country
        date predicted_date
        float confidence_score
        string prediction_type
        int target_month
        int target_year
        datetime created_at
        string model_version
    }
    
    TREND_ANALYSIS ||--o{ CATEGORY_DATA : analyzes
    TREND_ANALYSIS {
        int id PK
        string category
        string country
        date start_date
        date end_date
        int total_advancement_days
        float average_monthly_advancement
        float volatility_score
        string trend_direction
        datetime analysis_date
    }
    
    USERS ||--o{ CHAT_SESSIONS : has
    USERS {
        int id PK
        string username
        string email
        datetime created_at
        datetime last_login
    }
    
    CHAT_SESSIONS ||--o{ MESSAGES : contains
    CHAT_SESSIONS {
        int id PK
        int user_id FK
        string session_id
        string agent_mode
        datetime created_at
        datetime updated_at
    }
    
    MESSAGES {
        int id PK
        int session_id FK
        string role
        text content
        datetime timestamp
        json metadata
    }
```

## File Structure Overview

```
cisc691-a06/
├── src/
│   ├── main.py                 # Streamlit entry point
│   ├── agent/                  # AI Agent system
│   │   ├── core.py            # Main agent logic
│   │   ├── factory.py         # Agent creation
│   │   ├── visa_expertise.py  # Domain knowledge
│   │   ├── visa_tools.py      # Analytics tools
│   │   └── data_bridge.py     # Data integration
│   ├── api/                   # FastAPI backend
│   │   ├── main.py           # API entry point
│   │   ├── routers/          # HTTP endpoints
│   │   ├── models/           # API data models
│   │   ├── middleware/       # Request processing
│   │   └── utils/            # API utilities
│   ├── ui/                   # Streamlit frontend
│   │   ├── pages/            # UI pages
│   │   ├── components/       # Reusable components
│   │   └── utils/            # Frontend utilities
│   ├── visa/                 # Domain logic
│   │   ├── models.py         # Core data models
│   │   ├── database.py       # Database access
│   │   ├── repository.py     # Data operations
│   │   ├── parser.py         # Bulletin parsing
│   │   ├── validators.py     # Data validation
│   │   ├── analytics.py      # Analysis engine
│   │   └── collection/       # Data collection
│   └── utils/                # Shared utilities
├── tests/                    # Test suite
├── docs/                     # Documentation
├── data/                     # Application data
├── docker/                   # Docker configuration
└── scripts/                  # Utility scripts
```

---

*Generated with Claude Code - Professional Technical Documentation for Academic Submission*