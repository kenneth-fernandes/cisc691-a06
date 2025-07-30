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
    
    %% Styling with high contrast colors
    classDef frontend fill:#1976d2,stroke:#0d47a1,stroke-width:2px,color:#ffffff
    classDef api fill:#388e3c,stroke:#1b5e20,stroke-width:2px,color:#ffffff
    classDef agent fill:#f57c00,stroke:#e65100,stroke-width:2px,color:#ffffff
    classDef data fill:#7b1fa2,stroke:#4a148c,stroke-width:2px,color:#ffffff
    classDef external fill:#d32f2f,stroke:#b71c1c,stroke-width:2px,color:#ffffff
    
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
    
    %% Styling with vibrant contrasting colors
    classDef frontend fill:#2e7d32,stroke:#1b5e20,stroke-width:3px,color:#ffffff
    classDef backend fill:#c62828,stroke:#b71c1c,stroke-width:3px,color:#ffffff
    classDef aiml fill:#1565c0,stroke:#0d47a1,stroke-width:3px,color:#ffffff
    classDef database fill:#6a1b9a,stroke:#4a148c,stroke-width:3px,color:#ffffff
    classDef infrastructure fill:#ef6c00,stroke:#e65100,stroke-width:3px,color:#ffffff
    
    class ST,HTML frontend
    class FA,UV backend
    class LC,OPENAI,ANTHROPIC,GOOGLE,OLLAMA aiml
    class PG,SL,CACHE database
    class DOCKER,NGINX infrastructure
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

## Docker Architecture Overview

```mermaid
graph TB
    subgraph "Host Machine"
        subgraph "Docker Compose Environment"
            subgraph "Web Service Container"
                WEB[Streamlit Frontend<br/>Port: 8501<br/>Dockerfile.web]
                WEB_HEALTH[Health Check<br/>/_stcore/health]
            end
            
            subgraph "API Service Container"
                API[FastAPI Backend<br/>Port: 8000<br/>Dockerfile.api]
                API_HEALTH[Health Check<br/>/health]
                UVICORN[Uvicorn ASGI Server]
            end
            
            subgraph "Database Container"
                POSTGRES[PostgreSQL 15 Alpine<br/>Port: 5432<br/>Database: visa_app]
                PG_HEALTH[Health Check<br/>pg_isready]
                PG_DATA[(Persistent Volume<br/>postgres_data)]
            end
            
            subgraph "Cache Container"
                REDIS[Redis 7.0 Alpine<br/>Port: 6379<br/>Password Protected]
                REDIS_HEALTH[Health Check<br/>redis-cli ping]
                REDIS_DATA[(Persistent Volume<br/>redis_data)]
            end
        end
        
        subgraph "External Access"
            USER[Users]
            API_CLIENT[API Clients]
        end
        
        subgraph "Host Volumes"
            CODE_MOUNT[Code Mount<br/>.:/app]
            INIT_SQL[Init Script<br/>./init/init.sql]
        end
    end
    
    %% External connections
    USER -->|HTTP:8501| WEB
    API_CLIENT -->|HTTP:8000| API
    
    %% Internal service dependencies
    WEB -->|API Calls| API
    API -->|Database Queries| POSTGRES
    API -->|Cache Operations| REDIS
    
    %% Health checks
    WEB -.->|Monitor| WEB_HEALTH
    API -.->|Monitor| API_HEALTH
    POSTGRES -.->|Monitor| PG_HEALTH
    REDIS -.->|Monitor| REDIS_HEALTH
    
    %% Volume mounts
    CODE_MOUNT -.->|Mount| WEB
    CODE_MOUNT -.->|Mount| API
    INIT_SQL -.->|Initialize| POSTGRES
    PG_DATA -.->|Persist| POSTGRES
    REDIS_DATA -.->|Persist| REDIS
    
    %% Startup dependencies
    API -.->|depends_on| POSTGRES
    API -.->|depends_on| REDIS
    WEB -.->|depends_on| API
    
    %% Styling with distinct colors
    classDef web fill:#1976d2,stroke:#0d47a1,stroke-width:3px,color:#ffffff
    classDef api fill:#388e3c,stroke:#1b5e20,stroke-width:3px,color:#ffffff
    classDef database fill:#7b1fa2,stroke:#4a148c,stroke-width:3px,color:#ffffff  
    classDef cache fill:#d32f2f,stroke:#b71c1c,stroke-width:3px,color:#ffffff
    classDef external fill:#f57c00,stroke:#e65100,stroke-width:3px,color:#ffffff
    classDef volume fill:#607d8b,stroke:#455a64,stroke-width:2px,color:#ffffff
    classDef health fill:#4caf50,stroke:#2e7d32,stroke-width:1px,color:#ffffff
    
    class WEB web
    class API,UVICORN api
    class POSTGRES database
    class REDIS cache
    class USER,API_CLIENT external
    class CODE_MOUNT,INIT_SQL,PG_DATA,REDIS_DATA volume
    class WEB_HEALTH,API_HEALTH,PG_HEALTH,REDIS_HEALTH health
```

## Container Communication Flow

```mermaid
sequenceDiagram
    participant User
    participant Web as Streamlit Web (8501)
    participant API as FastAPI API (8000)
    participant Redis as Redis Cache (6379)
    participant DB as PostgreSQL (5432)
    
    Note over User,DB: Docker Compose Container Network
    
    User->>Web: HTTP Request (localhost:8501)
    Web->>API: Internal API Call (api:8000)
    
    alt Cache Hit
        API->>Redis: Check cache
        Redis-->>API: Return cached data
    else Cache Miss
        API->>DB: Query database
        DB-->>API: Return data
        API->>Redis: Store in cache
    end
    
    API-->>Web: JSON response
    Web-->>User: Rendered page
    
    Note over Web,DB: Health checks run every 30s
    Web->>Web: /_stcore/health
    API->>API: /health
    Redis->>Redis: redis-cli ping
    DB->>DB: pg_isready
```

## Docker Service Configuration

| Service | Image | Port | Dependencies | Health Check | Volumes |
|---------|-------|------|--------------|--------------|---------|
| **web** | Custom (Dockerfile.web) | 8501 | api | /_stcore/health | Code mount |
| **api** | Custom (Dockerfile.api) | 8000 | db, redis | /health | Code mount |
| **db** | postgres:15-alpine | 5432 | - | pg_isready | postgres_data, init.sql |
| **redis** | redis:7.0-alpine | 6379 | - | redis-cli ping | redis_data |

## Environment Variables

```bash
# Database Configuration
DATABASE_URL=postgresql://admin:password@db:5432/visa_app
POSTGRES_USER=admin
POSTGRES_PASSWORD=password
POSTGRES_DB=visa_app

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=redis_password

# Application Configuration
DOCKER_MODE=true
PYTHONPATH=/app/src
API_BASE_URL=http://api:8000
```

## Kubernetes Architecture Overview

```mermaid
graph TB
    subgraph "Kubernetes Cluster (visa-app namespace)"
        subgraph "Frontend Tier"
            WEB_POD[Web Pod<br/>Streamlit UI<br/>visa-app-web:latest]
            WEB_SVC[Web Service<br/>NodePort: 30080<br/>ClusterIP: 8501]
        end
        
        subgraph "API Tier"
            API_POD[API Pod<br/>FastAPI Backend<br/>visa-app-api:latest]
            API_SVC[API Service<br/>NodePort: 30081<br/>ClusterIP: 8000]
        end
        
        subgraph "Database Tier"
            PG_STATEFUL[PostgreSQL StatefulSet<br/>postgres:15-alpine<br/>Persistent Storage]
            PG_SVC[PostgreSQL Service<br/>ClusterIP: 5432<br/>Internal Only]
            PG_PVC[PostgreSQL PVC<br/>1Gi Storage<br/>ReadWriteOnce]
        end
        
        subgraph "Cache Tier"
            REDIS_POD[Redis Pod<br/>redis:7.0-alpine<br/>Persistent Storage]
            REDIS_SVC[Redis Service<br/>ClusterIP: 6379<br/>Internal Only]
            REDIS_PVC[Redis PVC<br/>512Mi Storage<br/>ReadWriteOnce]
        end
        
        subgraph "Configuration"
            CONFIGMAP[ConfigMap<br/>app-config<br/>Environment Variables]
            SECRETS[Secret<br/>app-secrets<br/>API Keys & Passwords]
        end
    end
    
    subgraph "External Access"
        USERS[Users]
        MINIKUBE[Minikube Service<br/>Tunnel/Port Forward]
    end
    
    %% External connections
    USERS -->|HTTP| MINIKUBE
    MINIKUBE -->|Tunnel| WEB_SVC
    MINIKUBE -->|Tunnel| API_SVC
    
    %% Internal service connections
    WEB_POD -->|API Calls| API_SVC
    API_POD -->|Database Queries| PG_SVC
    API_POD -->|Cache Operations| REDIS_SVC
    
    %% Service to pod connections
    WEB_SVC --> WEB_POD
    API_SVC --> API_POD
    PG_SVC --> PG_STATEFUL
    REDIS_SVC --> REDIS_POD
    
    %% Storage connections
    PG_STATEFUL -.->|Mount| PG_PVC
    REDIS_POD -.->|Mount| REDIS_PVC
    
    %% Configuration connections
    WEB_POD -.->|Config| CONFIGMAP
    API_POD -.->|Config| CONFIGMAP
    PG_STATEFUL -.->|Config| CONFIGMAP
    REDIS_POD -.->|Config| CONFIGMAP
    
    WEB_POD -.->|Secrets| SECRETS
    API_POD -.->|Secrets| SECRETS
    PG_STATEFUL -.->|Secrets| SECRETS
    REDIS_POD -.->|Secrets| SECRETS
    
    %% Styling with distinct colors
    classDef frontend fill:#1976d2,stroke:#0d47a1,stroke-width:3px,color:#ffffff
    classDef api fill:#388e3c,stroke:#1b5e20,stroke-width:3px,color:#ffffff
    classDef database fill:#7b1fa2,stroke:#4a148c,stroke-width:3px,color:#ffffff
    classDef cache fill:#d32f2f,stroke:#b71c1c,stroke-width:3px,color:#ffffff
    classDef config fill:#f57c00,stroke:#e65100,stroke-width:3px,color:#ffffff
    classDef storage fill:#607d8b,stroke:#455a64,stroke-width:2px,color:#ffffff
    classDef external fill:#795548,stroke:#5d4037,stroke-width:2px,color:#ffffff
    
    class WEB_POD,WEB_SVC frontend
    class API_POD,API_SVC api
    class PG_STATEFUL,PG_SVC database
    class REDIS_POD,REDIS_SVC cache
    class CONFIGMAP,SECRETS config
    class PG_PVC,REDIS_PVC storage
    class USERS,MINIKUBE external
```

## Kubernetes Deployment Flow

```mermaid
flowchart TD
    START([Start Deployment]) --> MINIKUBE_CHECK{Minikube Running?}
    MINIKUBE_CHECK -->|No| START_MINIKUBE[minikube start]
    MINIKUBE_CHECK -->|Yes| DOCKER_ENV[eval $(minikube docker-env)]
    START_MINIKUBE --> DOCKER_ENV
    
    DOCKER_ENV --> BUILD_IMAGES[Build Docker Images]
    BUILD_IMAGES --> BUILD_API[docker build -f Dockerfile.api -t visa-app-api:latest .]
    BUILD_IMAGES --> BUILD_WEB[docker build -f Dockerfile.web -t visa-app-web:latest .]
    
    BUILD_API --> DEPLOY_INFRA[Deploy Infrastructure]
    BUILD_WEB --> DEPLOY_INFRA
    
    DEPLOY_INFRA --> CREATE_NS[kubectl apply -f k8s/namespace.yaml]
    CREATE_NS --> DEPLOY_SECRETS[kubectl apply -f k8s/secrets/]
    DEPLOY_SECRETS --> DEPLOY_CONFIG[kubectl apply -f k8s/configmaps/]
    DEPLOY_CONFIG --> DEPLOY_STORAGE[kubectl apply -f k8s/volumes/]
    
    DEPLOY_STORAGE --> DEPLOY_DB[Deploy Database Layer]
    DEPLOY_DB --> PG_DEPLOY[kubectl apply -f k8s/deployments/postgres.yaml]
    PG_DEPLOY --> PG_SERVICE[kubectl apply -f k8s/services/postgres-service.yaml]
    PG_SERVICE --> PG_WAIT[kubectl wait --for=condition=ready pod -l app=postgres]
    
    PG_WAIT --> DEPLOY_CACHE[Deploy Cache Layer]
    DEPLOY_CACHE --> REDIS_DEPLOY[kubectl apply -f k8s/deployments/redis.yaml]
    REDIS_DEPLOY --> REDIS_SERVICE[kubectl apply -f k8s/services/redis-service.yaml]
    REDIS_SERVICE --> REDIS_WAIT[kubectl wait --for=condition=ready pod -l app=redis]
    
    REDIS_WAIT --> DEPLOY_APP[Deploy Application Layer]
    DEPLOY_APP --> API_DEPLOY[kubectl apply -f k8s/deployments/api.yaml]
    API_DEPLOY --> API_SERVICE[kubectl apply -f k8s/services/api-service.yaml]
    API_SERVICE --> API_WAIT[kubectl wait --for=condition=ready pod -l app=api]
    
    API_WAIT --> WEB_DEPLOY[kubectl apply -f k8s/deployments/web.yaml]
    WEB_DEPLOY --> WEB_SERVICE[kubectl apply -f k8s/services/web-service.yaml]
    WEB_SERVICE --> WEB_WAIT[kubectl wait --for=condition=ready pod -l app=web]
    
    WEB_WAIT --> VERIFY[Verify Deployment]
    VERIFY --> CHECK_PODS[kubectl get pods -n visa-app]
    CHECK_PODS --> CHECK_SERVICES[kubectl get services -n visa-app]
    CHECK_SERVICES --> ACCESS_APP[minikube service web -n visa-app]
    ACCESS_APP --> END([Deployment Complete])
    
    %% Error handling
    PG_WAIT -->|Timeout| PG_DEBUG[Check PostgreSQL logs]
    REDIS_WAIT -->|Timeout| REDIS_DEBUG[Check Redis logs]
    API_WAIT -->|Timeout| API_DEBUG[Check API logs]
    WEB_WAIT -->|Timeout| WEB_DEBUG[Check Web logs]
    
    PG_DEBUG --> END
    REDIS_DEBUG --> END
    API_DEBUG --> END
    WEB_DEBUG --> END
    
    %% Styling
    classDef startEnd fill:#4caf50,color:white
    classDef process fill:#2196f3,color:white
    classDef decision fill:#ff9800,color:white
    classDef deploy fill:#9c27b0,color:white
    classDef error fill:#f44336,color:white
    
    class START,END startEnd
    class MINIKUBE_CHECK decision
    class START_MINIKUBE,DOCKER_ENV,BUILD_IMAGES,BUILD_API,BUILD_WEB,VERIFY,CHECK_PODS,CHECK_SERVICES,ACCESS_APP process
    class DEPLOY_INFRA,CREATE_NS,DEPLOY_SECRETS,DEPLOY_CONFIG,DEPLOY_STORAGE,DEPLOY_DB,PG_DEPLOY,PG_SERVICE,DEPLOY_CACHE,REDIS_DEPLOY,REDIS_SERVICE,DEPLOY_APP,API_DEPLOY,API_SERVICE,WEB_DEPLOY,WEB_SERVICE deploy
    class PG_WAIT,REDIS_WAIT,API_WAIT,WEB_WAIT,PG_DEBUG,REDIS_DEBUG,API_DEBUG,WEB_DEBUG error
```

## Kubernetes Resource Hierarchy

```mermaid
graph TD
    subgraph "Namespace: visa-app"
        subgraph "ConfigMaps & Secrets"
            CM[app-config<br/>ConfigMap]
            SEC[app-secrets<br/>Secret]
        end
        
        subgraph "Storage"
            PG_PVC[postgres-pvc<br/>PersistentVolumeClaim<br/>1Gi]
            REDIS_PVC[redis-pvc<br/>PersistentVolumeClaim<br/>512Mi]
        end
        
        subgraph "Database Services"
            PG_SS[postgres<br/>StatefulSet<br/>1 replica]
            PG_SVC[postgres-service<br/>ClusterIP:5432]
        end
        
        subgraph "Cache Services"
            REDIS_DEP[redis<br/>Deployment<br/>1 replica]
            REDIS_SVC[redis-service<br/>ClusterIP:6379]
        end
        
        subgraph "Application Services"
            API_DEP[api<br/>Deployment<br/>1+ replicas]
            API_SVC[api-service<br/>NodePort:30081]
            
            WEB_DEP[web<br/>Deployment<br/>1+ replicas]
            WEB_SVC[web-service<br/>NodePort:30080]
        end
    end
    
    %% Resource relationships
    PG_SS -.->|mounts| PG_PVC
    REDIS_DEP -.->|mounts| REDIS_PVC
    
    PG_SVC -.->|targets| PG_SS
    REDIS_SVC -.->|targets| REDIS_DEP
    API_SVC -.->|targets| API_DEP
    WEB_SVC -.->|targets| WEB_DEP
    
    PG_SS -.->|uses| CM
    PG_SS -.->|uses| SEC
    REDIS_DEP -.->|uses| CM
    REDIS_DEP -.->|uses| SEC
    API_DEP -.->|uses| CM
    API_DEP -.->|uses| SEC
    WEB_DEP -.->|uses| CM
    WEB_DEP -.->|uses| SEC
    
    %% Dependencies
    API_DEP -.->|depends on| PG_SVC
    API_DEP -.->|depends on| REDIS_SVC
    WEB_DEP -.->|depends on| API_SVC
    
    %% Styling with distinct colors
    classDef config fill:#f57c00,stroke:#e65100,stroke-width:2px,color:#ffffff
    classDef storage fill:#607d8b,stroke:#455a64,stroke-width:2px,color:#ffffff
    classDef database fill:#7b1fa2,stroke:#4a148c,stroke-width:2px,color:#ffffff
    classDef cache fill:#d32f2f,stroke:#b71c1c,stroke-width:2px,color:#ffffff
    classDef application fill:#2196f3,stroke:#1565c0,stroke-width:2px,color:#ffffff
    
    class CM,SEC config
    class PG_PVC,REDIS_PVC storage
    class PG_SS,PG_SVC database
    class REDIS_DEP,REDIS_SVC cache
    class API_DEP,API_SVC,WEB_DEP,WEB_SVC application
```

## Kubernetes Access Patterns

```mermaid
sequenceDiagram
    participant User
    participant Minikube as Minikube Service
    participant WebSvc as Web Service (NodePort)
    participant WebPod as Web Pod
    participant APISvc as API Service (ClusterIP)
    participant APIPod as API Pod
    participant DBSvc as DB Service (ClusterIP)
    participant DBPod as PostgreSQL Pod
    
    Note over User,DBPod: Kubernetes Service Discovery & Load Balancing
    
    User->>Minikube: Access via tunnel URL
    Minikube->>WebSvc: Forward to NodePort 30080
    WebSvc->>WebPod: Load balance to healthy pod
    
    WebPod->>APISvc: Internal API call (api:8000)
    APISvc->>APIPod: Route to available pod
    
    APIPod->>DBSvc: Database query (postgres:5432)
    DBSvc->>DBPod: Connect to StatefulSet pod
    DBPod-->>APIPod: Return data
    
    APIPod-->>WebPod: JSON response
    WebPod-->>User: Rendered HTML
    
    Note over User,DBPod: All internal communication uses service discovery
```

## Kubernetes Resource Configuration

| Resource Type | Name | Replicas | Storage | Ports | Access |
|---------------|------|----------|---------|-------|---------|
| **StatefulSet** | postgres | 1 | 1Gi PVC | 5432 | ClusterIP |
| **Deployment** | redis | 1 | 512Mi PVC | 6379 | ClusterIP |
| **Deployment** | api | 1+ | - | 8000 | NodePort:30081 |
| **Deployment** | web | 1+ | - | 8501 | NodePort:30080 |
| **Service** | postgres-service | - | - | 5432 | ClusterIP |
| **Service** | redis-service | - | - | 6379 | ClusterIP |
| **Service** | api-service | - | - | 8000→30081 | NodePort |
| **Service** | web-service | - | - | 8501→30080 | NodePort |

---

*Generated with Claude Code - Professional Technical Documentation for Academic Submission*