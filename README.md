# 🤖 AgentVisa - AI Assistant for Visa Bulletin Insights

![CI](https://github.com/kenneth-fernandes/cisc691-a06/actions/workflows/ci.yml/badge.svg)
![Coverage](https://img.shields.io/badge/coverage-35%25-red)

AgentVisa is a containerized AI assistant with REST API backend that provides intelligent US visa bulletin analysis and multi-provider LLM chat capabilities.

## 📑 Table of Contents
- [✨ Features](#-features)
- [🚀 Quick Start](#-quick-start)
- [🐳 Docker Services](#-docker-services)
- [🧪 Testing](#-testing)
- [🛠️ Troubleshooting](#️-troubleshooting)
- [📊 Architecture & Documentation](#-system-architecture--documentation)
- [📝 Project Information](#-project-information)

## ✨ Features

- 🔌 **Multiple LLM Provider Support**:
  - 🌐 Google Gemini (Free tier)
  - 💻 Ollama (Local, Free)
  - 🔷 OpenAI GPT (Paid)
  - 🟣 Anthropic Claude (Paid)
  - 🤗 HuggingFace Transformers (Local, Free)

- 🎯 **Core Capabilities**:
  - 💬 Text-based chat interface with conversation memory
  - 🎯 Expert Mode Selection (General AI vs Visa Expert)
  - 📡 HTTP-based REST API communication
  - ⚙️ Configurable system prompts and response timing metrics

- 📊 **US Visa Bulletin Analytics**:
  - 📈 Complete Employment-based category support (EB-1, EB-2, EB-3, EB-4, EB-5)
  - 👨‍👩‍👧‍👦 Complete Family-based category support (F1, F2A, F2B, F3, F4)
  - 🌍 Country-specific analysis (India, China, Mexico, Philippines, Worldwide)
  - 🤖 ML-powered forecasting using Random Forest and Logistic Regression
  - 📅 Historical trend analysis and date advancement predictions
  - 📋 Interactive dashboard with charts and visualizations

- 🏗️ **Architecture**:
  - 🐳 Full Docker containerization with microservices
  - ⚡ REST API with FastAPI backend
  - 📡 HTTP-based request/response communication (Streamlit-compatible)
  - 🗄️ PostgreSQL database with Redis caching
  - 🏭 Factory pattern for agent creation
  - 📚 Layered architecture with clean separation

## 🚀 Quick Start

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) running
- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) (for GKE deployment)
- [Terraform](https://developer.hashicorp.com/terraform/downloads) (for GKE deployment)
- [kubectl](https://kubernetes.io/docs/tasks/tools/) (for Kubernetes management)
- [Minikube](https://minikube.sigs.k8s.io/docs/start/) (for local development)
- Git for cloning

### 🔒 Recommended: Secure GKE Deployment (Production)

Deploy to Google Cloud with HTTPS, autoscaling, and enterprise security:

```bash
# 1. Clone and setup
git clone https://github.com/kenneth-fernandes/cisc691-a06.git
cd cisc691-a06

# 2. Configure secrets
cp k8s/secrets/app-secrets.yaml.template k8s/secrets/app-secrets.yaml
# Edit app-secrets.yaml with your base64-encoded API keys

# 3. Configure GCP project
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# 4. Deploy to GKE (12-20 minutes)
chmod +x terraform/deploy.sh
./terraform/deploy.sh

# 5. Access your secure application
# Web: https://[STATIC-IP]/
# API: https://[STATIC-IP]/api/
```

**🔒 What You Get:**
- **HTTPS with SSL certificates** (Google-managed, free)
- **Load balancer** with health checks
- **Horizontal Pod Autoscaling** (HPA)
- **Secure Ingress** with static IP
- **Cost-optimized** (~$143/month)
- **Production-ready** infrastructure

**⏰ Setup Time: 12-20 minutes total**
- SSL certificate provisioning: +5-15 minutes additional

### 🏠 Local Development: Minikube

For local development and testing:

```bash
# 1. Clone and setup
git clone https://github.com/kenneth-fernandes/cisc691-a06.git
cd cisc691-a06

# 2. Start Minikube
minikube start --driver=docker

# 3. Deploy application
chmod +x k8s/deploy.sh
./k8s/deploy.sh

# 4. Access application
minikube service web -n visa-app
```

**🌐 Local Access Options:**
- **Tunnel URL**: `minikube service web -n visa-app` (recommended)
- **Port Forward**: `kubectl port-forward service/web 8501:8501 -n visa-app`

**📖 For complete setup instructions and troubleshooting:**
**→ See [docs/kubernetes-deployment.md](docs/kubernetes-deployment.md)**

### 🐳 Alternative: Docker Compose

```bash
# 1. Clone and setup
git clone https://github.com/kenneth-fernandes/cisc691-a06.git
cd cisc691-a06
cp .env.example .env

# 2. Add your API keys to .env file
# GOOGLE_API_KEY=your_google_api_key_here

# 3. Start application
docker-compose up --build

# 4. Access services
# Web UI: http://localhost:8501
# API: http://localhost:8000
```

### 🗂️ Complete Deployment Options

| Method | Use Case | Setup Time | Cost | Security | Documentation |
|--------|----------|------------|------|----------|---------------|
| **🔒 GKE Production** | Production deployment | 12-20 min | ~$143/month | Enterprise | [GKE Guide](terraform/README.md) |
| **🏠 Minikube Local** | Development/testing | 5-10 min | Free | Basic | [K8s Guide](docs/kubernetes-deployment.md) |
| **🐳 Docker Compose** | Quick testing | 2-5 min | Free | None | Below |

#### Quick Commands

**GKE Deployment:**
```bash
./terraform/deploy.sh    # Deploy to cloud
./terraform/cleanup.sh   # Cleanup (stops charges)
```

**Local Development:**
```bash
./k8s/deploy.sh         # Deploy to minikube
./k8s/cleanup.sh        # Cleanup local cluster
```

**Docker Compose:**
```bash
docker-compose up --build    # Start all services
docker-compose down          # Stop all services
```

## 🐳 Docker Services

The application uses **microservices architecture** with 4 containers:

- **⚡ API Service** - FastAPI backend for REST API (port 8000)
- **💻 Web Service** - Streamlit frontend for user interface (port 8501)
- **🗄️ PostgreSQL Database** - Primary data storage with JSONB support (port 5432)
- **🔄 Redis Cache** - Caching layer for API performance (port 6379)

### Configuration
All configuration is handled through environment variables in `.env`:

#### Required Environment Variables
Copy `.env.example` to `.env` and configure the following:

**LLM Provider API Keys:**
```bash
# Primary LLM (choose one or more)
GOOGLE_API_KEY=your_google_api_key_here          # Google Gemini (Free tier)
OPENAI_API_KEY=your_openai_api_key_here          # OpenAI GPT (Paid)
ANTHROPIC_API_KEY=your_anthropic_api_key_here    # Claude (Paid)
OLLAMA_BASE_URL=http://localhost:11434           # Ollama Local (Free)

# LLM Configuration
DEFAULT_LLM_PROVIDER=google                      # Default: google
LLM_MODEL_TEMPERATURE=0.7                       # Response creativity (0.0-1.0)
```

**Database Configuration:**
```bash
# PostgreSQL (Production)
DATABASE_URL=postgresql://admin:password@localhost:5432/visa_app
POSTGRES_USER=admin
POSTGRES_PASSWORD=password
POSTGRES_DB=visa_app

# Redis Cache
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=redis_password

# Application Settings
DOCKER_MODE=false                                # Set to true in containers
API_BASE_URL=http://localhost:8000              # API backend URL
PYTHONPATH=src                                   # Python module path
```

#### LLM Providers
- **Google Gemini** (default, free tier) - `gemini-1.5-flash`
- **OpenAI GPT** (paid) - `gpt-4o`, `gpt-3.5-turbo`
- **Anthropic Claude** (paid) - `claude-3-5-sonnet-20241022`
- **Ollama** (local models via Docker) - `llama-3.2`, `phi-3`
- **HuggingFace** (local models) - Transformers and community models

#### Database
- **PostgreSQL** - Primary database for all data storage
- **Redis caching** (optional, degrades gracefully to in-memory)
- Automatic schema creation and persistent volumes

## 📊 Data Collection & Processing

### Visa Bulletin Data Sources
The system automatically collects and processes visa bulletin data from:
- **US State Department** (`travel.state.gov`) - Current and historical bulletins
- **Automated Scraping** - BeautifulSoup4-based HTML parsing
- **Historical Range** - 2020-present with monthly updates
- **Data Validation** - Multi-stage validation and quality assurance

### Data Collection Methods
```bash
# Manual data collection
python scripts/visa_data_manager.py --collect-historical 2020 2025

# Monthly automated updates
python scripts/visa_data_manager.py --fetch-current

# Data validation and verification
python scripts/verify_eb_categories.py
```

### Supported Visa Categories
- **Employment-Based**: EB-1, EB-2, EB-3, EB-4, EB-5
- **Family-Based**: F1, F2A, F2B, F3, F4
- **Countries**: China, India, Mexico, Philippines, Worldwide
- **Data Types**: Final Action Dates, Filing Dates, Current/Unavailable status

## 🧪 Testing

### Run Tests
```bash
# Run all tests
pytest tests/ -v

# Run specific test categories
pytest tests/test_api_* -v        # API tests
pytest tests/test_*_caching.py -v # Caching tests
pytest tests/test_*_integration.py -v # Integration tests

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

### Test Categories
- **🔬 Unit Tests**: Individual component testing (agent core, data models, utilities)
- **🔗 Integration Tests**: End-to-end workflow testing (data collection, AI agent workflows)
- **⚡ API Tests**: REST API endpoint testing (agent chat, analytics, health checks)
- **🔄 Cache Tests**: Redis caching functionality and fallback behavior
- **🤖 Agent Tests**: LLM integration and tool calling functionality
- **📊 Analytics Tests**: ML model predictions and trend analysis

**Current Coverage: 35%** - Covers core API endpoints, agent functionality, and data processing components.

### Manual Test Scripts
```bash
python scripts/test_agent.py      # Core agent functionality
python scripts/test_visa_agent.py # Visa bulletin expertise
```

## 🛠️ Troubleshooting

### Quick Diagnostics

**Check deployment status:**
```bash
kubectl get pods -n visa-app              # Pod status
kubectl get services -n visa-app          # Service status  
kubectl get ingress -n visa-app           # Ingress status (GKE)
```

**View logs for debugging:**
```bash
kubectl logs -f deployment/api -n visa-app    # API logs
kubectl logs -f deployment/web -n visa-app    # Web logs
kubectl logs -f statefulset/postgres -n visa-app  # Database logs
```

**Common fixes:**
```bash
# Restart failed deployments
kubectl rollout restart deployment/api -n visa-app
kubectl rollout restart deployment/web -n visa-app

# Reset everything (local)
./k8s/cleanup.sh && ./k8s/deploy.sh

# Reset everything (GKE) 
./terraform/cleanup.sh && ./terraform/deploy.sh
```

### Docker Compose Issues

```bash
docker-compose ps                    # Check service status
docker-compose logs api              # View API logs  
docker-compose logs web              # View Streamlit logs
docker-compose down && docker-compose up --build  # Clean restart
```

### Common Issues & Solutions

**Environment Variables:**
```bash
# Missing API keys error
cp .env.example .env
# Edit .env with your API keys

# Database connection issues
docker-compose restart db
docker-compose logs db
```

**LLM Provider Issues:**
```bash
# Test API key validation
python scripts/test_agent.py

# Switch to fallback provider if one fails
# Edit .env: DEFAULT_LLM_PROVIDER=google
```

**Port Conflicts:**
```bash
# If ports 8000/8501 are in use
docker-compose down
sudo lsof -i :8000    # Find processes using ports
sudo lsof -i :8501
```

**Performance Issues:**
```bash
# Clear Redis cache
docker-compose exec redis redis-cli FLUSHALL

# Restart with fresh containers
docker-compose down -v
docker-compose up --build
```

**For detailed troubleshooting guides, see the infrastructure documentation above.**

## 🛠️ Advanced Configuration & Monitoring

### 🔍 Monitoring with k9s (Recommended)

Install k9s for real-time cluster monitoring:

```bash
# Install k9s
brew install k9s

# Connect to your cluster
gcloud container clusters get-credentials agentvisa-cluster --zone us-central1-a --project YOUR_PROJECT_ID

# Launch k9s
k9s
```

**Key k9s Commands:**
- `:pods` - View all pods
- `:services` - View services  
- `/visa-app` - Filter to your namespace
- `l` - View logs (select pod first)
- `?` - Help menu

### 💰 Cost Management

**Monitor costs:**
```bash
kubectl top nodes              # Node resource usage
kubectl top pods -n visa-app   # Pod resource usage
kubectl get hpa -n visa-app    # Autoscaling status
```

**Stop all charges:**
```bash
./terraform/cleanup.sh  # Destroys everything (~$143/month savings)
```

### 🔒 SSL Certificate Status

Check SSL certificate provisioning:
```bash
kubectl get managedcertificate -n visa-app
kubectl describe managedcertificate agentvisa-ssl-cert -n visa-app
```

## 📊 System Architecture & Documentation

### 🏗️ Architecture & Design
- **[🏛️ Complete System Architecture](docs/workflow-diagrams.md)** - Comprehensive system architecture, agent workflows, and component interactions
- **[🔄 Data Flow Architecture](docs/visa-bulletin-data-flow.md)** - Visa bulletin data processing pipeline and AI agent integration
- **[☁️ GKE Production Deployment](docs/gke-architecture-diagram.md)** - Google Kubernetes Engine architecture and scaling strategy
- **[✅ Architecture Verification](docs/ARCHITECTURE_VERIFICATION.md)** - Comprehensive verification report of all diagrams

### 🚀 Deployment & Infrastructure
- **[🔒 GKE Production Setup](terraform/deployment-guide.md)** - Secure cloud deployment with Terraform
- **[🏠 Local Kubernetes](docs/kubernetes-deployment.md)** - Minikube development setup and troubleshooting
- **[🐳 Docker Architecture](docs/workflow-diagrams.md#docker-architecture-overview)** - Container orchestration and service communication

### 🤖 Technical Documentation  
- **[🎯 Detailed Features](docs/detailed-features.md)** - ML models, database architecture, visa expertise system
- **[📊 Data Collection](docs/data-collection.md)** - Historical data collection, validation, and setup guides
- **[📡 Communication Analysis](docs/websocket-analysis.md)** - HTTP/WebSocket communication patterns

### Complete System Architecture

```mermaid
graph TB
    subgraph "User Interface Layer"
        UI[Streamlit Main App<br/>src/main.py]
        CHAT[Chat Interface<br/>ui/pages/chat.py]
        ANALYTICS[Analytics Dashboard<br/>ui/pages/analytics.py]
        PRED[Visa Predictions<br/>ui/pages/visa_prediction.py]
        SIDEBAR[Navigation Sidebar<br/>ui/components/sidebar.py]
    end
    
    subgraph "API Gateway Layer"
        API[FastAPI Backend<br/>api/main.py]
        AGENT_ROUTER[Agent Router<br/>api/routers/agent.py]
        ANALYTICS_ROUTER[Analytics Router<br/>api/routers/analytics.py]
        CACHE_MW[Cache Middleware<br/>api/middleware/cache_middleware.py]
    end
    
    subgraph "AI Agent System"
        FACTORY[Agent Factory<br/>agent/factory.py]
        CORE[Multi-LLM Agent Core<br/>agent/core.py]
        TOOLS[Visa Analytics Tools<br/>agent/visa_tools.py]
        EXPERTISE[Visa Expert System<br/>agent/visa_expertise.py]
        BRIDGE[Data Bridge<br/>agent/data_bridge.py]
    end
    
    subgraph "Data Processing Pipeline"
        PARSER[Web Scraper & Parser<br/>visa/parser.py]
        VALIDATOR[Data Validator<br/>visa/validators.py]
        ANALYTICS_ENGINE[Analytics Engine<br/>visa/analytics.py]
        ML_PREDICTOR[ML Predictor<br/>visa/predictor.py]
        REPO[Repository Layer<br/>visa/repository.py]
    end
    
    subgraph "Storage & Cache Layer"
        PG[(PostgreSQL<br/>Primary Database)]
        SQLITE[(SQLite<br/>Fallback Database)]
        REDIS[(Redis Cache<br/>Performance Layer)]
    end
    
    subgraph "External Services"
        STATE_DEPT[US State Department<br/>travel.state.gov]
        OPENAI[OpenAI GPT<br/>gpt-4, gpt-3.5-turbo]
        ANTHROPIC[Anthropic Claude<br/>claude-3.5-sonnet]
        GOOGLE[Google Gemini<br/>gemini-1.5-flash]
        OLLAMA[Ollama Local<br/>llama-3.2]
    end
    
    %% User Interface Flow
    UI --> CHAT
    UI --> ANALYTICS
    UI --> PRED
    UI --> SIDEBAR
    
    %% API Communication
    CHAT --> API
    ANALYTICS --> API
    PRED --> API
    
    %% API Routing
    API --> AGENT_ROUTER
    API --> ANALYTICS_ROUTER
    API --> CACHE_MW
    
    %% Agent System Flow
    AGENT_ROUTER --> FACTORY
    FACTORY --> CORE
    CORE --> TOOLS
    CORE --> EXPERTISE
    TOOLS --> BRIDGE
    
    %% Data Processing Flow
    PARSER --> STATE_DEPT
    PARSER --> VALIDATOR
    VALIDATOR --> REPO
    BRIDGE --> ANALYTICS_ENGINE
    ANALYTICS_ENGINE --> ML_PREDICTOR
    ANALYTICS_ENGINE --> REPO
    ML_PREDICTOR --> REPO
    
    %% Storage Connections
    REPO --> PG
    REPO --> SQLITE
    CACHE_MW --> REDIS
    
    %% External AI Services
    CORE --> OPENAI
    CORE --> ANTHROPIC
    CORE --> GOOGLE
    CORE --> OLLAMA
    
    %% Styling with distinct, professional colors
    classDef ui fill:#1976d2,stroke:#0d47a1,stroke-width:3px,color:#ffffff
    classDef api fill:#388e3c,stroke:#1b5e20,stroke-width:3px,color:#ffffff
    classDef agent fill:#f57c00,stroke:#e65100,stroke-width:3px,color:#ffffff
    classDef data fill:#7b1fa2,stroke:#4a148c,stroke-width:3px,color:#ffffff
    classDef storage fill:#607d8b,stroke:#455a64,stroke-width:3px,color:#ffffff
    classDef external fill:#d32f2f,stroke:#b71c1c,stroke-width:3px,color:#ffffff
    
    class UI,CHAT,ANALYTICS,PRED,SIDEBAR ui
    class API,AGENT_ROUTER,ANALYTICS_ROUTER,CACHE_MW api
    class FACTORY,CORE,TOOLS,EXPERTISE,BRIDGE agent
    class PARSER,VALIDATOR,ANALYTICS_ENGINE,ML_PREDICTOR,REPO data
    class PG,SQLITE,REDIS storage
    class STATE_DEPT,OPENAI,ANTHROPIC,GOOGLE,OLLAMA external
```

## 📝 Project Information

This project was developed as part of the **CISC 691 - Foundations of Next-Gen AI** course assignment (A06: Building the AI Agent of Your Choice).

### Course Details
- **Institution**: Harrisburg University
- **Term**: Summer 2025
- **Professor**: Donald O'Hara

### Contributors
- Tien Dinh
- Kenneth Peter Fernandes

### Assignment Objectives
- Develop a functional AI agent using modern frameworks
- Implement multiple provider support for flexibility
- Create a modular and extensible architecture
- Demonstrate practical AI integration skills

---
*This project demonstrates the practical application of AI agent development concepts learned throughout the course.*