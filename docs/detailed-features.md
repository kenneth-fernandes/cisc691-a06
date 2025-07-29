# Detailed Features Documentation

## 🤖 Machine Learning Prediction System

The application includes advanced machine learning capabilities for visa bulletin forecasting, implemented in `src/visa/predictor.py`:

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

## 🏛️ Visa Bulletin Expertise

The AI agent includes specialized expertise and analytical capabilities for US visa bulletin analysis:

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