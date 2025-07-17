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


class VisaDatabase:
    """SQLite database manager for visa bulletin data"""
    
    def __init__(self, db_path: str = None):
        """Initialize database connection"""
        self.db_path = db_path or VisaConfig.DATABASE_PATH
        self._ensure_directory_exists()
        self._create_tables()
    
    def _ensure_directory_exists(self):
        """Ensure the database directory exists"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
        finally:
            conn.close()
    
    def _create_tables(self):
        """Create database tables if they don't exist"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Visa bulletins table
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
            
            # Category data table
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
            
            # Predictions table
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
            
            # Trend analysis table
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
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_bulletins_date ON visa_bulletins(fiscal_year, month, year)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_category_data_lookup ON category_data(category, country)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_predictions_lookup ON predictions(category, country, target_year, target_month)")
            
            conn.commit()
    
    def save_bulletin(self, bulletin: VisaBulletin) -> int:
        """Save a visa bulletin and return its ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Insert bulletin
            cursor.execute("""
                INSERT OR REPLACE INTO visa_bulletins 
                (bulletin_date, fiscal_year, month, year, source_url, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
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
            
            # Delete existing category data for this bulletin
            cursor.execute("DELETE FROM category_data WHERE bulletin_id = ?", (bulletin_id,))
            
            # Insert category data
            for cat_data in bulletin.categories:
                cursor.execute("""
                    INSERT INTO category_data 
                    (bulletin_id, category, country, final_action_date, filing_date, status, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
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
            cursor.execute("""
                SELECT * FROM visa_bulletins 
                WHERE fiscal_year = ? AND month = ? AND year = ?
            """, (fiscal_year, month, year))
            
            bulletin_row = cursor.fetchone()
            if not bulletin_row:
                return None
            
            # Get category data
            cursor.execute("""
                SELECT * FROM category_data WHERE bulletin_id = ?
            """, (bulletin_row['id'],))
            
            category_rows = cursor.fetchall()
            
            # Build bulletin object
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
            
            cursor.execute("""
                SELECT * FROM visa_bulletins 
                WHERE year >= ? AND year <= ?
                ORDER BY year, month
            """, (start_year, end_year))
            
            for bulletin_row in cursor.fetchall():
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
            
            query = """
                SELECT cd.*, vb.year, vb.month, vb.fiscal_year
                FROM category_data cd
                JOIN visa_bulletins vb ON cd.bulletin_id = vb.id
                WHERE cd.category = ? AND cd.country = ?
            """
            params = [category.value, country.value]
            
            if start_year:
                query += " AND vb.year >= ?"
                params.append(start_year)
            
            if end_year:
                query += " AND vb.year <= ?"
                params.append(end_year)
            
            query += " ORDER BY vb.year, vb.month"
            
            cursor.execute(query, params)
            
            history = []
            for row in cursor.fetchall():
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
            
            cursor.execute("""
                INSERT INTO predictions 
                (category, country, predicted_date, confidence_score, prediction_type,
                 target_month, target_year, created_at, model_version)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            
            query = "SELECT * FROM predictions WHERE 1=1"
            params = []
            
            if category:
                query += " AND category = ?"
                params.append(category.value)
            
            if country:
                query += " AND country = ?"
                params.append(country.value)
            
            query += " ORDER BY created_at DESC"
            
            cursor.execute(query, params)
            
            predictions = []
            for row in cursor.fetchall():
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
            cursor.execute("""
                SELECT id FROM visa_bulletins 
                WHERE fiscal_year = ? AND month = ? AND year = ?
            """, (fiscal_year, month, year))
            
            bulletin_row = cursor.fetchone()
            if not bulletin_row:
                return False
            
            bulletin_id = bulletin_row['id']
            
            # Delete category data first (foreign key constraint)
            cursor.execute("DELETE FROM category_data WHERE bulletin_id = ?", (bulletin_id,))
            
            # Delete bulletin
            cursor.execute("DELETE FROM visa_bulletins WHERE id = ?", (bulletin_id,))
            
            conn.commit()
            return True
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # Count bulletins
            cursor.execute("SELECT COUNT(*) as count FROM visa_bulletins")
            stats['bulletin_count'] = cursor.fetchone()['count']
            
            # Count category data entries
            cursor.execute("SELECT COUNT(*) as count FROM category_data")
            stats['category_data_count'] = cursor.fetchone()['count']
            
            # Count predictions
            cursor.execute("SELECT COUNT(*) as count FROM predictions")
            stats['prediction_count'] = cursor.fetchone()['count']
            
            # Get date range
            cursor.execute("SELECT MIN(year) as min_year, MAX(year) as max_year FROM visa_bulletins")
            date_range = cursor.fetchone()
            stats['year_range'] = f"{date_range['min_year']}-{date_range['max_year']}" if date_range['min_year'] else "No data"
            
            return stats