import sqlite3
import json
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple, Union
from pathlib import Path
from cryptography.fernet import Fernet
import os

from settings import settings
from models import Portfolio, Transaction, RebalanceEvent, PortfolioSnapshot, RebalanceSettings, APIKey

class DatabaseManager:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.DATABASE_PATH
        self.init_database()
        # Initialize encryption system
        try:
            self._init_encryption()
        except Exception as e:
            print(f"Warning: Failed to initialize encryption: {e}")

    def init_database(self):
        """Initialize the database with required tables"""
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
                    paper_trading BOOLEAN DEFAULT FALSE,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (portfolio_id) REFERENCES portfolios (id)
                )
            ''')

            # API Keys table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS api_keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    exchange TEXT NOT NULL,
                    name TEXT NOT NULL,
                    api_key TEXT NOT NULL,
                    api_secret TEXT NOT NULL,
                    portfolio_id INTEGER,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (portfolio_id) REFERENCES portfolios (id)
                )
            ''')

            conn.commit()
            
    def _init_encryption(self):
        """Initialize the encryption system by ensuring we have a key."""
        with sqlite3.connect(self.db_path) as conn:
            try:
                # Check if the encryption key exists
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS app_settings (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL
                    )
                ''')
                
                # Try to get the existing key
                cursor.execute('SELECT value FROM app_settings WHERE key = ?', ('encryption_key',))
                result = cursor.fetchone()
                
                if not result:
                    # No key exists, generate a new one
                    key = Fernet.generate_key().decode()
                    cursor.execute(
                        'INSERT INTO app_settings (key, value) VALUES (?, ?)',
                        ('encryption_key', key)
                    )
                    conn.commit()
                    return key
                return result[0]
            except Exception as e:
                print(f"Error initializing encryption: {e}")
                raise
    
    def _get_encryption_key(self) -> bytes:
        """Get the encryption key from the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT value FROM app_settings WHERE key = ?', ('encryption_key',))
                result = cursor.fetchone()
                
                if not result:
                    # If no key exists, initialize one
                    return self._init_encryption().encode()
                    
                return result[0].encode()
        except Exception as e:
            print(f"Error getting encryption key: {e}")
            # Generate a temporary key as fallback
            return Fernet.generate_key()
    
    def _encrypt(self, data: str) -> str:
        """Encrypt sensitive data."""
        try:
            if not data:
                return ""
            f = Fernet(self._get_encryption_key())
            return f.encrypt(data.encode()).decode()
        except Exception as e:
            print(f"Encryption error: {e}")
            raise ValueError("Failed to encrypt data")
    
    def _decrypt(self, encrypted_data: str) -> str:
        """Decrypt sensitive data."""
        try:
            if not encrypted_data:
                return ""
            f = Fernet(self._get_encryption_key())
            return f.decrypt(encrypted_data.encode()).decode()
        except Exception as e:
            print(f"Decryption error: {e}")
            # Return empty string if decryption fails (e.g., due to key change)
            return "[ENCRYPTION ERROR]"
            
    def reencrypt_all_keys(self, old_key: str, new_key: str) -> bool:
        """Re-encrypt all API keys with a new encryption key."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get all API keys
                cursor.execute('SELECT id, api_key, api_secret FROM api_keys')
                keys = cursor.fetchall()
                
                # Create Fernet instances
                old_fernet = Fernet(old_key.encode())
                new_fernet = Fernet(new_key.encode())
                
                # Re-encrypt each key
                for key_id, api_key, api_secret in keys:
                    try:
                        # Decrypt with old key
                        decrypted_key = old_fernet.decrypt(api_key.encode()).decode()
                        decrypted_secret = old_fernet.decrypt(api_secret.encode()).decode()
                        
                        # Encrypt with new key
                        new_encrypted_key = new_fernet.encrypt(decrypted_key.encode()).decode()
                        new_encrypted_secret = new_fernet.encrypt(decrypted_secret.encode()).decode()
                        
                        # Update in database
                        cursor.execute(
                            'UPDATE api_keys SET api_key = ?, api_secret = ? WHERE id = ?',
                            (new_encrypted_key, new_encrypted_secret, key_id)
                        )
                        
                    except Exception as e:
                        print(f"Error re-encrypting key {key_id}: {e}")
                        continue
                
                # Update the stored encryption key
                cursor.execute(
                    'INSERT OR REPLACE INTO app_settings (key, value) VALUES (?, ?)',
                    ('encryption_key', new_key)
                )
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"Error in re-encryption: {e}")
            return False

    def create_portfolio(self, name: str, allocation: Dict[str, float]) -> Portfolio:
        """Create a new portfolio"""
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
            
    def delete_portfolio(self, portfolio_id: int) -> bool:
        """
        Delete a portfolio and all its related data.
        
        Args:
            portfolio_id: The ID of the portfolio to delete
            
        Returns:
            bool: True if deletion was successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Start a transaction
                cursor.execute('BEGIN TRANSACTION')
                
                try:
                    # 1. Delete related transactions
                    cursor.execute('DELETE FROM transactions WHERE portfolio_id = ?', (portfolio_id,))
                    
                    # 2. Delete related rebalance events
                    cursor.execute('DELETE FROM rebalance_events WHERE portfolio_id = ?', (portfolio_id,))
                    
                    # 3. Delete related portfolio snapshots
                    cursor.execute('DELETE FROM portfolio_snapshots WHERE portfolio_id = ?', (portfolio_id,))
                    
                    # 4. Delete related rebalance settings
                    cursor.execute('DELETE FROM rebalance_settings WHERE portfolio_id = ?', (portfolio_id,))
                    
                    # 5. Remove portfolio reference from API keys (set to NULL)
                    cursor.execute('UPDATE api_keys SET portfolio_id = NULL WHERE portfolio_id = ?', (portfolio_id,))
                    
                    # 6. Soft delete the portfolio by setting is_active to FALSE
                    cursor.execute('''
                        UPDATE portfolios 
                        SET is_active = FALSE, updated_at = ?
                        WHERE id = ?
                    ''', (datetime.now().isoformat(), portfolio_id))
                    
                    # Check if any rows were affected
                    if cursor.rowcount == 0:
                        cursor.execute('ROLLBACK')
                        return False
                    
                    conn.commit()
                    return True
                    
                except Exception as e:
                    cursor.execute('ROLLBACK')
                    print(f"Error deleting portfolio {portfolio_id}: {e}")
                    return False
                    
        except Exception as e:
            print(f"Database error when deleting portfolio {portfolio_id}: {e}")
            return False

    def get_portfolio(self, portfolio_id: int) -> Optional[Portfolio]:
        """Get portfolio by ID"""
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
            
    # API Key Management Methods
    def add_api_key(
        self,
        exchange: str,
        name: str,
        api_key: str,
        api_secret: str,
        portfolio_id: Optional[int] = None
    ) -> int:
        """Add a new API key to the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO api_keys 
                (exchange, name, api_key, api_secret, portfolio_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                exchange,
                name,
                self._encrypt(api_key),
                self._encrypt(api_secret),
                portfolio_id
            ))
            conn.commit()
            return cursor.lastrowid
    
    def update_api_key(
        self,
        key_id: int,
        name: Optional[str] = None,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        portfolio_id: Optional[int] = None,
        is_active: Optional[bool] = None
    ) -> bool:
        """Update an existing API key."""
        updates = []
        params = []
        
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if api_key is not None:
            updates.append("api_key = ?")
            params.append(self._encrypt(api_key))
        if api_secret is not None:
            updates.append("api_secret = ?")
            params.append(self._encrypt(api_secret))
        if portfolio_id is not None:
            updates.append("portfolio_id = ?")
            params.append(portfolio_id)
        if is_active is not None:
            updates.append("is_active = ?")
            params.append(1 if is_active else 0)
        
        if not updates:
            return False
            
        params.append(key_id)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                UPDATE api_keys 
                SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                params
            )
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_api_key(self, key_id: int) -> bool:
        """Delete an API key."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM api_keys WHERE id = ?', (key_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def get_api_key(self, key_id: int) -> Optional[Dict[str, Any]]:
        """Get API key details by ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM api_keys WHERE id = ?', (key_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
                
            return self._format_api_key_row(row)
    
    def get_api_keys_by_portfolio(self, portfolio_id: int) -> List[Dict[str, Any]]:
        """Get all API keys for a specific portfolio."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM api_keys WHERE portfolio_id = ?', (portfolio_id,))
            return [self._format_api_key_row(row) for row in cursor.fetchall()]
    
    def get_all_api_keys(self) -> List[Dict[str, Any]]:
        """Get all API keys."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM api_keys ORDER BY exchange, name')
            return [self._format_api_key_row(row) for row in cursor.fetchall()]
    
    def _format_api_key_row(self, row: Tuple) -> Dict[str, Any]:
        """Format a database row as an API key dictionary."""
        return {
            'id': row[0],
            'exchange': row[1],
            'name': row[2],
            'api_key': self._decrypt(row[3]),
            'api_secret': '••••••••' + self._decrypt(row[4])[-4:] if row[4] else None,
            'portfolio_id': row[5],
            'is_active': bool(row[6]),
            'created_at': row[7],
            'updated_at': row[8]
        }

    def get_all_portfolios(self, include_inactive: bool = False) -> List[Portfolio]:
        """
        Get all portfolios, optionally including inactive ones.
        
        Args:
            include_inactive: If True, include inactive portfolios in the results
            
        Returns:
            List[Portfolio]: List of portfolio objects
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if include_inactive:
                cursor.execute('SELECT * FROM portfolios')
            else:
                cursor.execute('SELECT * FROM portfolios WHERE is_active = TRUE')
                
            rows = cursor.fetchall()

            portfolios = []
            for row in rows:
                try:
                    portfolios.append(Portfolio(
                        id=row[0],
                        name=row[1],
                        allocation=json.loads(row[2]),
                        created_at=datetime.fromisoformat(row[3]) if row[3] else datetime.now(),
                        updated_at=datetime.fromisoformat(row[4]) if row[4] else datetime.now(),
                        is_active=bool(row[5]) if len(row) > 5 else True
                    ))
                except Exception as e:
                    print(f"Error parsing portfolio {row[0]}: {e}")
                    continue
                    
            return portfolios

    def update_portfolio(self, portfolio_id: int, allocation: Dict[str, float]) -> bool:
        """Update portfolio allocation"""
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
        """Add a new transaction"""
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
        """Get transactions for a portfolio"""
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
        """Save a portfolio snapshot"""
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
        """Get portfolio snapshots for the last N days"""
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
        """Save rebalance settings for a portfolio"""
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
        """Get rebalance settings for a portfolio"""
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