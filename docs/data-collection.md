# Historical Visa Bulletin Data Collection

The system includes a comprehensive historical data collection module for US visa bulletins with advanced analytics capabilities.

## 🎯 Key Features

### ✅ 1. Historical Data Collection (2020-2025)
- Multi-threaded collection with configurable workers
- URL verification and error handling
- Progress tracking and resumable collection
- Comprehensive logging and reporting

### ✅ 2. Automated Monthly Data Fetching
- Automated current bulletin fetching
- Cron job scheduling support  
- Status tracking and duplicate prevention
- Error handling and retry logic

### ✅ 3. Data Cleaning and Normalization
- **Complete category parsing**: All 10 visa categories (EB-1 through EB-5, F1 through F4)
- **Advanced date parsing**: State Department formats ("15JAN23", "22APR24") + standard formats
- **Employment-Based category recognition**: Ordinal formats ("1st", "2nd") and subcategories
- Category name standardization (EB1 → EB-1, etc.)
- Country name normalization
- Date format standardization to ISO format
- Status code normalization (C, U, DATE)
- **PostgreSQL compatibility**: Native date/datetime type handling

### ✅ 4. Advanced Trend Analysis
- Statistical trend analysis with momentum calculation
- Seasonal pattern detection
- Volatility and consistency scoring
- Category comparison across countries
- Prediction algorithms with confidence scoring

## 🚀 Implementation Guide

The visa data collection system supports both local development and Docker containerized environments with automatic mode detection.

### 🖥️ Local Mode Implementation

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

### 🐳 Docker Mode Implementation

**Setup:**
```bash
# 1. Start all services (PostgreSQL, Redis, Application)
docker-compose up -d

# 2. Verify services are running
docker-compose ps
```

**Execute commands:**
```bash
# Collect historical data (uses PostgreSQL)
docker-compose exec api python scripts/visa_data_manager.py collect --start-year 2020 --end-year 2025

# Fetch current bulletin
docker-compose exec api python scripts/visa_data_manager.py fetch

# Validate and clean data
docker-compose exec api python scripts/visa_data_manager.py validate --fix-errors

# Analyze trends
docker-compose exec api python scripts/visa_data_manager.py analyze --category EB-2 --country India

# Web interface automatically available at http://localhost:8501
```

### 🎯 Quick Start Commands

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
docker-compose up -d
docker-compose exec api python scripts/visa_data_manager.py collect --start-year 2020 --end-year 2025
# Access web UI at http://localhost:8501
```

### 🔧 Dual-Mode Architecture

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

## 🔄 Automated Monthly Updates

Set up cron job for automatic monthly updates:

**Local Mode:**
```bash
# Add to crontab (crontab -e)
0 6 * * * cd /path/to/project && /path/to/.venv/bin/python scripts/visa_data_manager.py fetch >> /var/log/visa_bulletin.log 2>&1
```

**Docker Mode:**
```bash
# Add to crontab (crontab -e)
0 6 * * * cd /path/to/project && docker-compose exec -T app python scripts/visa_data_manager.py fetch >> /var/log/visa_bulletin.log 2>&1
```

## 📈 Programmatic Usage

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