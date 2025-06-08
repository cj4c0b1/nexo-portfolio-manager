# Create app/db/database.py
database_content = """import sqlite3
import json
from datetime import datetime
from typing import List, Optional, Dict
from pathlib import Path

from config.settings import settings
from app.db.models import Portfolio, Transaction, RebalanceEvent, PortfolioSnapshot, RebalanceSettings

class DatabaseManager:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.DATABASE_PATH
        self.init_database()
    
    def init_database(self):
        \"\"\"Initialize the database with required tables\"\"\"
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Portfolios table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS portfolios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    allocation TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE
                )
            ''')
            
            # Transactions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    portfolio_id INTEGER NOT NULL,
                    token TEXT NOT NULL,
                    transaction_type TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    price REAL NOT NULL,
                    fee REAL DEFAULT 0.0,
                    platform TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (portfolio_id) REFERENCES portfolios (id)
                )
            ''')
            
            # Rebalance events table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS rebalance_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    portfolio_id INTEGER NOT NULL,
                    trigger_type TEXT NOT NULL,
                    old_allocation TEXT NOT NULL,
                    new_allocation TEXT NOT NULL,
                    executed_trades TEXT NOT NULL,
                    total_cost REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (portfolio_id) REFERENCES portfolios (id)
                )
            ''')
            
            # Portfolio snapshots table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS portfolio_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    portfolio_id INTEGER NOT NULL,
                    balances TEXT NOT NULL,
                    prices TEXT NOT NULL,
                    total_value REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (portfolio_id) REFERENCES portfolios (id)
                )
            ''')
            
            # Rebalance settings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS rebalance_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    portfolio_id INTEGER NOT NULL UNIQUE,
                    frequency TEXT NOT NULL DEFAULT 'weekly',
                    threshold REAL NOT NULL DEFAULT 5.0,
                    min_trade_value REAL NOT NULL DEFAULT 10.0,
                    auto_rebalance BOOLEAN DEFAULT FALSE,
                    paper_trading BOOLEAN DEFAULT TRUE,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (portfolio_id) REFERENCES portfolios (id)
                )
            ''')
            
            conn.commit()
    
    def create_portfolio(self, name: str, allocation: Dict[str, float]) -> Portfolio:
        \"\"\"Create a new portfolio\"\"\"
        now = datetime.now()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO portfolios (name, allocation, created_at, updated_at)
                VALUES (?, ?, ?, ?)
            ''', (name, json.dumps(allocation), now.isoformat(), now.isoformat()))
            
            portfolio_id = cursor.lastrowid
            conn.commit()
            
            return Portfolio(
                id=portfolio_id,
                name=name,
                allocation=allocation,
                created_at=now,
                updated_at=now,
                is_active=True
            )
    
    def get_portfolio(self, portfolio_id: int) -> Optional[Portfolio]:
        \"\"\"Get portfolio by ID\"\"\"
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM portfolios WHERE id = ?', (portfolio_id,))
            row = cursor.fetchone()
            
            if row:
                return Portfolio(
                    id=row[0],
                    name=row[1],
                    allocation=json.loads(row[2]),
                    created_at=datetime.fromisoformat(row[3]),
                    updated_at=datetime.fromisoformat(row[4]),
                    is_active=bool(row[5])
                )
            return None
    
    def get_all_portfolios(self) -> List[Portfolio]:
        \"\"\"Get all active portfolios\"\"\"
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM portfolios WHERE is_active = TRUE')
            rows = cursor.fetchall()
            
            portfolios = []
            for row in rows:
                portfolios.append(Portfolio(
                    id=row[0],
                    name=row[1],
                    allocation=json.loads(row[2]),
                    created_at=datetime.fromisoformat(row[3]),
                    updated_at=datetime.fromisoformat(row[4]),
                    is_active=bool(row[5])
                ))
            return portfolios
    
    def update_portfolio(self, portfolio_id: int, allocation: Dict[str, float]) -> bool:
        \"\"\"Update portfolio allocation\"\"\"
        now = datetime.now()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE portfolios 
                SET allocation = ?, updated_at = ?
                WHERE id = ?
            ''', (json.dumps(allocation), now.isoformat(), portfolio_id))
            
            conn.commit()
            return cursor.rowcount > 0
    
    def add_transaction(self, transaction: Transaction) -> int:
        \"\"\"Add a new transaction\"\"\"
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO transactions 
                (portfolio_id, token, transaction_type, quantity, price, fee, platform, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                transaction.portfolio_id,
                transaction.token,
                transaction.transaction_type,
                transaction.quantity,
                transaction.price,
                transaction.fee,
                transaction.platform,
                transaction.timestamp.isoformat()
            ))
            
            transaction_id = cursor.lastrowid
            conn.commit()
            return transaction_id
    
    def get_portfolio_transactions(self, portfolio_id: int, limit: int = 100) -> List[Transaction]:
        \"\"\"Get transactions for a portfolio\"\"\"
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM transactions 
                WHERE portfolio_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (portfolio_id, limit))
            
            rows = cursor.fetchall()
            transactions = []
            for row in rows:
                transactions.append(Transaction(
                    id=row[0],
                    portfolio_id=row[1],
                    token=row[2],
                    transaction_type=row[3],
                    quantity=row[4],
                    price=row[5],
                    fee=row[6],
                    platform=row[7],
                    timestamp=datetime.fromisoformat(row[8])
                ))
            return transactions
    
    def save_portfolio_snapshot(self, snapshot: PortfolioSnapshot) -> int:
        \"\"\"Save a portfolio snapshot\"\"\"
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO portfolio_snapshots 
                (portfolio_id, balances, prices, total_value, timestamp)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                snapshot.portfolio_id,
                json.dumps(snapshot.balances),
                json.dumps(snapshot.prices),
                snapshot.total_value,
                snapshot.timestamp.isoformat()
            ))
            
            snapshot_id = cursor.lastrowid
            conn.commit()
            return snapshot_id
    
    def get_portfolio_snapshots(self, portfolio_id: int, days: int = 30) -> List[PortfolioSnapshot]:
        \"\"\"Get portfolio snapshots for the last N days\"\"\"
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM portfolio_snapshots 
                WHERE portfolio_id = ? 
                AND timestamp >= datetime('now', '-{} days')
                ORDER BY timestamp ASC
            '''.format(days), (portfolio_id,))
            
            rows = cursor.fetchall()
            snapshots = []
            for row in rows:
                snapshots.append(PortfolioSnapshot(
                    id=row[0],
                    portfolio_id=row[1],
                    balances=json.loads(row[2]),
                    prices=json.loads(row[3]),
                    total_value=row[4],
                    timestamp=datetime.fromisoformat(row[5])
                ))
            return snapshots
    
    def save_rebalance_settings(self, settings: RebalanceSettings) -> int:
        \"\"\"Save rebalance settings for a portfolio\"\"\"
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO rebalance_settings 
                (portfolio_id, frequency, threshold, min_trade_value, auto_rebalance, paper_trading, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                settings.portfolio_id,
                settings.frequency,
                settings.threshold,
                settings.min_trade_value,
                settings.auto_rebalance,
                settings.paper_trading,
                settings.created_at.isoformat(),
                settings.updated_at.isoformat()
            ))
            
            conn.commit()
            return cursor.lastrowid
    
    def get_rebalance_settings(self, portfolio_id: int) -> Optional[RebalanceSettings]:
        \"\"\"Get rebalance settings for a portfolio\"\"\"
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM rebalance_settings WHERE portfolio_id = ?', (portfolio_id,))
            row = cursor.fetchone()
            
            if row:
                return RebalanceSettings(
                    id=row[0],
                    portfolio_id=row[1],
                    frequency=row[2],
                    threshold=row[3],
                    min_trade_value=row[4],
                    auto_rebalance=bool(row[5]),
                    paper_trading=bool(row[6]),
                    created_at=datetime.fromisoformat(row[7]),
                    updated_at=datetime.fromisoformat(row[8])
                )
            return None
"""

with open("nexo_portfolio_manager/app/db/database.py", "w") as f:
    f.write(database_content.strip())

print("Created database operations file!")