"""
Database layer for visa bulletin data storage and retrieval
"""
import sqlite3
import os
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from contextlib import contextmanager

from .models import VisaBulletin, CategoryData, PredictionResult, TrendAnalysis, VisaCategory, CountryCode
from .config import VisaConfig

try:
    import psycopg2
    import psycopg2.extras
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False


class VisaDatabase:
    """Multi-database manager for visa bulletin data (SQLite/PostgreSQL)"""
    
    def __init__(self, db_path: str = None):
        """Initialize database connection"""
        # Check if PostgreSQL should be used via DATABASE_URL
        self.database_url = os.getenv('DATABASE_URL')
        self.use_postgres = bool(self.database_url and POSTGRES_AVAILABLE and 'postgresql://' in self.database_url)
        
        if self.use_postgres:
            self.db_path = None
            print(f"VisaDatabase: Using PostgreSQL - {self.database_url}")
        else:
            self.db_path = db_path or VisaConfig.DATABASE_PATH
            self._ensure_directory_exists()
            print(f"VisaDatabase: Using SQLite - {self.db_path}")
        
        print("VisaDatabase: About to create tables...")
        try:
            self._create_tables()
            print("VisaDatabase: Tables created successfully")
        except Exception as e:
            if self.use_postgres:
                print(f"VisaDatabase: PostgreSQL connection failed, falling back to SQLite: {e}")
                # Fall back to SQLite
                self.use_postgres = False
                self.database_url = None
                self.db_path = db_path or VisaConfig.DATABASE_PATH
                self._ensure_directory_exists()
                self._create_tables()
                print("VisaDatabase: Fallback to SQLite successful")
            else:
                raise
    
    def _ensure_directory_exists(self):
        """Ensure the database directory exists"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    def _get_param_placeholder(self):
        """Get the correct parameter placeholder for the database type"""
        return "%s" if self.use_postgres else "?"
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        if self.use_postgres:
            conn = psycopg2.connect(self.database_url)
            conn.autocommit = False
            try:
                yield conn
            finally:
                conn.close()
        else:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            try:
                yield conn
            finally:
                conn.close()
    
    def _create_tables(self):
        """Create database tables if they don't exist"""
        print(f"_create_tables: Starting table creation, use_postgres={self.use_postgres}")
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                print("_create_tables: Got database connection and cursor")
                
                if self.use_postgres:
                    # PostgreSQL table creation
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS visa_bulletins (
                            id SERIAL PRIMARY KEY,
                            bulletin_date DATE NOT NULL,
                            fiscal_year INTEGER NOT NULL,
                            month INTEGER NOT NULL,
                            year INTEGER NOT NULL,
                            source_url TEXT,
                            created_at TIMESTAMP NOT NULL,
                            updated_at TIMESTAMP NOT NULL,
                            UNIQUE(fiscal_year, month, year)
                        )
                    """)
                else:
                    # SQLite table creation
                    print("_create_tables: Creating SQLite visa_bulletins table")
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS visa_bulletins (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            bulletin_date TEXT NOT NULL,
                            fiscal_year INTEGER NOT NULL,
                            month INTEGER NOT NULL,
                            year INTEGER NOT NULL,
                            source_url TEXT,
                            created_at TEXT NOT NULL,
                            updated_at TEXT NOT NULL,
                            UNIQUE(fiscal_year, month, year)
                        )
                    """)
                    print("_create_tables: SQLite visa_bulletins table created")
                
                if self.use_postgres:
                    # PostgreSQL category data table
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS category_data (
                            id SERIAL PRIMARY KEY,
                            bulletin_id INTEGER NOT NULL,
                            category TEXT NOT NULL,
                            country TEXT NOT NULL,
                            final_action_date DATE,
                            filing_date DATE,
                            status TEXT NOT NULL,
                            notes TEXT,
                            FOREIGN KEY (bulletin_id) REFERENCES visa_bulletins (id) ON DELETE CASCADE,
                            UNIQUE(bulletin_id, category, country)
                        )
                    """)
                else:
                    # SQLite category data table
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS category_data (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            bulletin_id INTEGER NOT NULL,
                            category TEXT NOT NULL,
                            country TEXT NOT NULL,
                            final_action_date TEXT,
                            filing_date TEXT,
                            status TEXT NOT NULL,
                            notes TEXT,
                            FOREIGN KEY (bulletin_id) REFERENCES visa_bulletins (id),
                            UNIQUE(bulletin_id, category, country)
                        )
                    """)
                
                if self.use_postgres:
                    # PostgreSQL predictions table
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS predictions (
                            id SERIAL PRIMARY KEY,
                            category TEXT NOT NULL,
                            country TEXT NOT NULL,
                            predicted_date DATE,
                            confidence_score REAL NOT NULL,
                            prediction_type TEXT NOT NULL,
                            target_month INTEGER NOT NULL,
                            target_year INTEGER NOT NULL,
                            created_at TIMESTAMP NOT NULL,
                            model_version TEXT NOT NULL
                        )
                    """)
                    
                    # PostgreSQL trend analysis table
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS trend_analysis (
                            id SERIAL PRIMARY KEY,
                            category TEXT NOT NULL,
                            country TEXT NOT NULL,
                            start_date DATE NOT NULL,
                            end_date DATE NOT NULL,
                            total_advancement_days INTEGER NOT NULL,
                            average_monthly_advancement REAL NOT NULL,
                            volatility_score REAL NOT NULL,
                            trend_direction TEXT NOT NULL,
                            analysis_date TIMESTAMP NOT NULL
                        )
                    """)
                else:
                    # SQLite predictions table
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS predictions (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            category TEXT NOT NULL,
                            country TEXT NOT NULL,
                            predicted_date TEXT,
                            confidence_score REAL NOT NULL,
                            prediction_type TEXT NOT NULL,
                            target_month INTEGER NOT NULL,
                            target_year INTEGER NOT NULL,
                            created_at TEXT NOT NULL,
                            model_version TEXT NOT NULL
                        )
                    """)
                    
                    # SQLite trend analysis table
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS trend_analysis (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            category TEXT NOT NULL,
                            country TEXT NOT NULL,
                            start_date TEXT NOT NULL,
                            end_date TEXT NOT NULL,
                            total_advancement_days INTEGER NOT NULL,
                            average_monthly_advancement REAL NOT NULL,
                            volatility_score REAL NOT NULL,
                            trend_direction TEXT NOT NULL,
                            analysis_date TEXT NOT NULL
                        )
                    """)
                
                # Create indexes for better query performance
                if self.use_postgres:
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bulletins_date ON visa_bulletins(fiscal_year, month, year)")
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_category_data_lookup ON category_data(category, country)")
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_predictions_lookup ON predictions(category, country, target_year, target_month)")
                else:
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_bulletins_date ON visa_bulletins(fiscal_year, month, year)")
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_category_data_lookup ON category_data(category, country)")
                    cursor.execute("CREATE INDEX IF NOT EXISTS idx_predictions_lookup ON predictions(category, country, target_year, target_month)")
                    
                conn.commit()
        except Exception as e:
            print(f"Error creating tables: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def save_bulletin(self, bulletin: VisaBulletin) -> int:
        """Save a visa bulletin and return its ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # First, check if bulletin already exists
            placeholder = self._get_param_placeholder()
            cursor.execute(f"""
                SELECT id FROM visa_bulletins 
                WHERE fiscal_year = {placeholder} AND month = {placeholder} AND year = {placeholder}
            """, (bulletin.fiscal_year, bulletin.month, bulletin.year))
            
            existing = cursor.fetchone()
            
            if existing:
                # Update existing bulletin
                bulletin_id = existing[0]
                placeholder = self._get_param_placeholder()
                cursor.execute(f"""
                    UPDATE visa_bulletins 
                    SET bulletin_date = {placeholder}, source_url = {placeholder}, updated_at = {placeholder}
                    WHERE id = {placeholder}
                """, (
                    bulletin.bulletin_date.isoformat(),
                    bulletin.source_url,
                    bulletin.updated_at.isoformat(),
                    bulletin_id
                ))
                
                # Delete existing category data for this bulletin
                placeholder = self._get_param_placeholder()
                cursor.execute(f"DELETE FROM category_data WHERE bulletin_id = {placeholder}", (bulletin_id,))
            else:
                # Insert new bulletin
                placeholder = self._get_param_placeholder()
                if self.use_postgres:
                    cursor.execute(f"""
                        INSERT INTO visa_bulletins 
                        (bulletin_date, fiscal_year, month, year, source_url, created_at, updated_at)
                        VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
                        RETURNING id
                    """, (
                        bulletin.bulletin_date.isoformat(),
                        bulletin.fiscal_year,
                        bulletin.month,
                        bulletin.year,
                        bulletin.source_url,
                        bulletin.created_at.isoformat(),
                        bulletin.updated_at.isoformat()
                    ))
                    bulletin_id = cursor.fetchone()[0]
                else:
                    cursor.execute(f"""
                        INSERT INTO visa_bulletins 
                        (bulletin_date, fiscal_year, month, year, source_url, created_at, updated_at)
                        VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
                    """, (
                        bulletin.bulletin_date.isoformat(),
                        bulletin.fiscal_year,
                        bulletin.month,
                        bulletin.year,
                        bulletin.source_url,
                        bulletin.created_at.isoformat(),
                        bulletin.updated_at.isoformat()
                    ))
                    bulletin_id = cursor.lastrowid
            
            # Insert category data
            for cat_data in bulletin.categories:
                placeholder = self._get_param_placeholder()
                if self.use_postgres:
                    # Use ON CONFLICT for PostgreSQL to handle duplicates
                    cursor.execute(f"""
                        INSERT INTO category_data 
                        (bulletin_id, category, country, final_action_date, filing_date, status, notes)
                        VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
                        ON CONFLICT (bulletin_id, category, country) 
                        DO UPDATE SET 
                            final_action_date = EXCLUDED.final_action_date,
                            filing_date = EXCLUDED.filing_date,
                            status = EXCLUDED.status,
                            notes = EXCLUDED.notes
                    """, (
                        bulletin_id,
                        cat_data.category.value,
                        cat_data.country.value,
                        cat_data.final_action_date.isoformat() if cat_data.final_action_date else None,
                        cat_data.filing_date.isoformat() if cat_data.filing_date else None,
                        cat_data.status.value,
                        cat_data.notes
                    ))
                else:
                    # SQLite INSERT OR REPLACE
                    cursor.execute(f"""
                        INSERT OR REPLACE INTO category_data 
                        (bulletin_id, category, country, final_action_date, filing_date, status, notes)
                        VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
                    """, (
                        bulletin_id,
                        cat_data.category.value,
                        cat_data.country.value,
                        cat_data.final_action_date.isoformat() if cat_data.final_action_date else None,
                        cat_data.filing_date.isoformat() if cat_data.filing_date else None,
                        cat_data.status.value,
                        cat_data.notes
                    ))
            
            conn.commit()
            return bulletin_id
    
    def get_bulletin(self, fiscal_year: int, month: int, year: int) -> Optional[VisaBulletin]:
        """Get a specific bulletin by date"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get bulletin
            placeholder = self._get_param_placeholder()
            cursor.execute(f"""
                SELECT * FROM visa_bulletins 
                WHERE fiscal_year = {placeholder} AND month = {placeholder} AND year = {placeholder}
            """, (fiscal_year, month, year))
            
            bulletin_row = cursor.fetchone()
            if not bulletin_row:
                return None
            
            # Get category data
            placeholder = self._get_param_placeholder()
            bulletin_id = bulletin_row[0] if self.use_postgres else bulletin_row['id']
            cursor.execute(f"""
                SELECT * FROM category_data WHERE bulletin_id = {placeholder}
            """, (bulletin_id,))
            
            category_rows = cursor.fetchall()
            
            # Build bulletin object
            if self.use_postgres:
                # PostgreSQL: access by index, handle native types vs strings
                def safe_parse_date(value):
                    if isinstance(value, date):
                        return value
                    elif isinstance(value, str):
                        return datetime.fromisoformat(value).date()
                    else:
                        return datetime.fromisoformat(str(value)).date()
                
                def safe_parse_datetime(value):
                    if isinstance(value, datetime):
                        return value
                    elif isinstance(value, str):
                        return datetime.fromisoformat(value)
                    else:
                        return datetime.fromisoformat(str(value))
                
                bulletin = VisaBulletin(
                    bulletin_date=safe_parse_date(bulletin_row[1]),
                    fiscal_year=bulletin_row[2],
                    month=bulletin_row[3],
                    year=bulletin_row[4],
                    source_url=bulletin_row[5],
                    created_at=safe_parse_datetime(bulletin_row[6]),
                    updated_at=safe_parse_datetime(bulletin_row[7])
                )
            else:
                # SQLite: access by name, dates are strings
                bulletin = VisaBulletin(
                    bulletin_date=datetime.fromisoformat(bulletin_row['bulletin_date']).date(),
                    fiscal_year=bulletin_row['fiscal_year'],
                    month=bulletin_row['month'],
                    year=bulletin_row['year'],
                    source_url=bulletin_row['source_url'],
                    created_at=datetime.fromisoformat(bulletin_row['created_at']),
                    updated_at=datetime.fromisoformat(bulletin_row['updated_at'])
                )
            
            for cat_row in category_rows:
                if self.use_postgres:
                    # PostgreSQL: access by index, handle native types vs strings
                    def safe_parse_date(value):
                        if not value:
                            return None
                        if isinstance(value, date):
                            return value
                        elif isinstance(value, str):
                            return datetime.fromisoformat(value).date()
                        else:
                            return datetime.fromisoformat(str(value)).date()
                    
                    cat_data = CategoryData(
                        category=VisaCategory(cat_row[2]),
                        country=CountryCode(cat_row[3]),
                        final_action_date=safe_parse_date(cat_row[4]),
                        filing_date=safe_parse_date(cat_row[5]),
                        status=cat_row[6],
                        notes=cat_row[7]
                    )
                else:
                    # SQLite: access by name
                    cat_data = CategoryData(
                        category=VisaCategory(cat_row['category']),
                        country=CountryCode(cat_row['country']),
                        final_action_date=datetime.fromisoformat(cat_row['final_action_date']).date() if cat_row['final_action_date'] else None,
                        filing_date=datetime.fromisoformat(cat_row['filing_date']).date() if cat_row['filing_date'] else None,
                        status=cat_row['status'],
                        notes=cat_row['notes']
                    )
                bulletin.add_category_data(cat_data)
            
            return bulletin
    
    def get_bulletins_range(self, start_year: int, end_year: int) -> List[VisaBulletin]:
        """Get all bulletins within a year range"""
        bulletins = []
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            placeholder = self._get_param_placeholder()
            cursor.execute(f"""
                SELECT * FROM visa_bulletins 
                WHERE year >= {placeholder} AND year <= {placeholder}
                ORDER BY year, month
            """, (start_year, end_year))
            
            for bulletin_row in cursor.fetchall():
                if self.use_postgres:
                    # PostgreSQL: access by index
                    bulletin = self.get_bulletin(
                        bulletin_row[2],  # fiscal_year
                        bulletin_row[3],  # month
                        bulletin_row[4]   # year
                    )
                else:
                    # SQLite: access by name
                    bulletin = self.get_bulletin(
                        bulletin_row['fiscal_year'],
                        bulletin_row['month'],
                        bulletin_row['year']
                    )
                if bulletin:
                    bulletins.append(bulletin)
        
        return bulletins
    
    def get_category_history(self, category: VisaCategory, country: CountryCode, 
                           start_year: int = None, end_year: int = None) -> List[CategoryData]:
        """Get historical data for a specific category and country"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            placeholder = self._get_param_placeholder()
            query = f"""
                SELECT cd.*, vb.year, vb.month, vb.fiscal_year
                FROM category_data cd
                JOIN visa_bulletins vb ON cd.bulletin_id = vb.id
                WHERE cd.category = {placeholder} AND cd.country = {placeholder}
            """
            params = [category.value, country.value]
            
            if start_year:
                query += f" AND vb.year >= {placeholder}"
                params.append(start_year)
            
            if end_year:
                query += f" AND vb.year <= {placeholder}"
                params.append(end_year)
            
            query += " ORDER BY vb.year, vb.month"
            
            cursor.execute(query, params)
            
            history = []
            for row in cursor.fetchall():
                if self.use_postgres:
                    # PostgreSQL: access by index, handle native types vs strings
                    def safe_parse_date(value):
                        if not value:
                            return None
                        if isinstance(value, date):
                            return value
                        elif isinstance(value, str):
                            return datetime.fromisoformat(value).date()
                        else:
                            return datetime.fromisoformat(str(value)).date()
                    
                    cat_data = CategoryData(
                        category=VisaCategory(row[2]),  # category
                        country=CountryCode(row[3]),   # country
                        final_action_date=safe_parse_date(row[4]),  # final_action_date
                        filing_date=safe_parse_date(row[5]),  # filing_date
                        status=row[6],  # status
                        notes=row[7]   # notes
                    )
                else:
                    # SQLite: access by name
                    cat_data = CategoryData(
                        category=VisaCategory(row['category']),
                        country=CountryCode(row['country']),
                        final_action_date=datetime.fromisoformat(row['final_action_date']).date() if row['final_action_date'] else None,
                        filing_date=datetime.fromisoformat(row['filing_date']).date() if row['filing_date'] else None,
                        status=row['status'],
                        notes=row['notes']
                    )
                history.append(cat_data)
            
            return history
    
    def save_prediction(self, prediction: PredictionResult) -> int:
        """Save a prediction result"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            placeholder = self._get_param_placeholder()
            cursor.execute(f"""
                INSERT INTO predictions 
                (category, country, predicted_date, confidence_score, prediction_type,
                 target_month, target_year, created_at, model_version)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            """, (
                prediction.category.value,
                prediction.country.value,
                prediction.predicted_date.isoformat() if prediction.predicted_date else None,
                prediction.confidence_score,
                prediction.prediction_type,
                prediction.target_month,
                prediction.target_year,
                prediction.created_at.isoformat(),
                prediction.model_version
            ))
            
            conn.commit()
            return cursor.lastrowid
    
    def get_latest_predictions(self, category: VisaCategory = None, 
                             country: CountryCode = None) -> List[PredictionResult]:
        """Get the latest predictions, optionally filtered by category and country"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            placeholder = self._get_param_placeholder()
            query = "SELECT * FROM predictions WHERE 1=1"
            params = []
            
            if category:
                query += f" AND category = {placeholder}"
                params.append(category.value)
            
            if country:
                query += f" AND country = {placeholder}"
                params.append(country.value)
            
            query += " ORDER BY created_at DESC"
            
            cursor.execute(query, params)
            
            predictions = []
            for row in cursor.fetchall():
                if self.use_postgres:
                    # PostgreSQL: access by index, handle native types vs strings
                    def safe_parse_date(value):
                        if not value:
                            return None
                        if isinstance(value, date):
                            return value
                        elif isinstance(value, str):
                            return datetime.fromisoformat(value).date()
                        else:
                            return datetime.fromisoformat(str(value)).date()
                    
                    def safe_parse_datetime(value):
                        if isinstance(value, datetime):
                            return value
                        elif isinstance(value, str):
                            return datetime.fromisoformat(value)
                        else:
                            return datetime.fromisoformat(str(value))
                    
                    prediction = PredictionResult(
                        category=VisaCategory(row[1]),  # category
                        country=CountryCode(row[2]),   # country
                        predicted_date=safe_parse_date(row[3]),  # predicted_date
                        confidence_score=row[4],  # confidence_score
                        prediction_type=row[5],   # prediction_type
                        target_month=row[6],      # target_month
                        target_year=row[7],       # target_year
                        created_at=safe_parse_datetime(row[8]),  # created_at
                        model_version=row[9]      # model_version
                    )
                else:
                    # SQLite: access by name
                    prediction = PredictionResult(
                        category=VisaCategory(row['category']),
                        country=CountryCode(row['country']),
                        predicted_date=datetime.fromisoformat(row['predicted_date']).date() if row['predicted_date'] else None,
                        confidence_score=row['confidence_score'],
                        prediction_type=row['prediction_type'],
                        target_month=row['target_month'],
                        target_year=row['target_year'],
                        created_at=datetime.fromisoformat(row['created_at']),
                        model_version=row['model_version']
                    )
                predictions.append(prediction)
            
            return predictions
    
    def delete_bulletin(self, fiscal_year: int, month: int, year: int) -> bool:
        """Delete a bulletin and its associated data"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get bulletin ID
            placeholder = self._get_param_placeholder()
            cursor.execute(f"""
                SELECT id FROM visa_bulletins 
                WHERE fiscal_year = {placeholder} AND month = {placeholder} AND year = {placeholder}
            """, (fiscal_year, month, year))
            
            bulletin_row = cursor.fetchone()
            if not bulletin_row:
                return False
            
            bulletin_id = bulletin_row[0] if self.use_postgres else bulletin_row['id']
            
            # Delete category data first (foreign key constraint)
            placeholder = self._get_param_placeholder()
            cursor.execute(f"DELETE FROM category_data WHERE bulletin_id = {placeholder}", (bulletin_id,))
            
            # Delete bulletin
            cursor.execute(f"DELETE FROM visa_bulletins WHERE id = {placeholder}", (bulletin_id,))
            
            conn.commit()
            return True
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # Count bulletins
            cursor.execute("SELECT COUNT(*) FROM visa_bulletins")
            stats['bulletin_count'] = cursor.fetchone()[0]
            
            # Count category data entries
            cursor.execute("SELECT COUNT(*) FROM category_data")
            stats['category_data_count'] = cursor.fetchone()[0]
            
            # Count predictions
            cursor.execute("SELECT COUNT(*) FROM predictions")
            stats['prediction_count'] = cursor.fetchone()[0]
            
            # Get date range
            cursor.execute("SELECT MIN(year), MAX(year) FROM visa_bulletins")
            date_range = cursor.fetchone()
            if self.use_postgres:
                min_year, max_year = date_range
                stats['year_range'] = f"{min_year}-{max_year}" if min_year else "No data"
            else:
                # SQLite also returns a tuple, not named columns
                min_year, max_year = date_range
                stats['year_range'] = f"{min_year}-{max_year}" if min_year else "No data"
            
            return stats