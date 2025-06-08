"""
API Key Management Module

This module provides functionality to securely store, retrieve, and manage
API keys for multiple exchanges and accounts.
"""
import os
import json
from typing import Dict, List, Optional
from datetime import datetime
import streamlit as st
from cryptography.fernet import Fernet
from database import DatabaseManager
from models import Portfolio

class APIKeyManager:
    """Manages API keys for different exchanges and accounts."""
    
    def __init__(self, db: DatabaseManager):
        """Initialize the API key manager with a database connection."""
        self.db = db
        self._init_database()
        self.encryption_key = self._get_encryption_key()
    
    def _init_database(self):
        """Initialize the API keys table in the database."""
        with self.db.conn:
            self.db.conn.execute('''
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
    
    def _get_encryption_key(self) -> bytes:
        """Get or generate the encryption key for API keys."""
        key = os.getenv('ENCRYPTION_KEY')
        if not key:
            # In production, you should set ENCRYPTION_KEY in your environment
            key = Fernet.generate_key().decode()
            st.warning(
                "No ENCRYPTION_KEY found in environment. Using a temporary key. "
                "For production, set ENCRYPTION_KEY in your environment variables."
            )
        return key.encode()
    
    def _encrypt(self, data: str) -> str:
        """Encrypt sensitive data."""
        f = Fernet(self.encryption_key)
        return f.encrypt(data.encode()).decode()
    
    def _decrypt(self, encrypted_data: str) -> str:
        """Decrypt sensitive data."""
        f = Fernet(self.encryption_key)
        return f.decrypt(encrypted_data.encode()).decode()
    
    def add_api_key(
        self,
        exchange: str,
        name: str,
        api_key: str,
        api_secret: str,
        portfolio_id: Optional[int] = None
    ) -> int:
        """Add a new API key to the database."""
        with self.db.conn:
            cursor = self.db.conn.cursor()
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
        
        with self.db.conn:
            cursor = self.db.conn.cursor()
            cursor.execute(
                f"""
                UPDATE api_keys 
                SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                params
            )
            return cursor.rowcount > 0
    
    def delete_api_key(self, key_id: int) -> bool:
        """Delete an API key."""
        with self.db.conn:
            cursor = self.db.conn.cursor()
            cursor.execute('DELETE FROM api_keys WHERE id = ?', (key_id,))
            return cursor.rowcount > 0
    
    def get_api_key(self, key_id: int) -> Optional[Dict]:
        """Get API key details by ID."""
        cursor = self.db.conn.cursor()
        cursor.execute('SELECT * FROM api_keys WHERE id = ?', (key_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
            
        return self._format_api_key_row(row)
    
    def get_api_keys_by_portfolio(self, portfolio_id: int) -> List[Dict]:
        """Get all API keys for a specific portfolio."""
        cursor = self.db.conn.cursor()
        cursor.execute('SELECT * FROM api_keys WHERE portfolio_id = ?', (portfolio_id,))
        return [self._format_api_key_row(row) for row in cursor.fetchall()]
    
    def get_all_api_keys(self) -> List[Dict]:
        """Get all API keys."""
        cursor = self.db.conn.cursor()
        cursor.execute('SELECT * FROM api_keys ORDER BY exchange, name')
        return [self._format_api_key_row(row) for row in cursor.fetchall()]
    
    def _format_api_key_row(self, row) -> Dict:
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


def render_api_key_management_ui(api_key_manager: APIKeyManager, portfolio_manager):
    """Render the API key management UI."""
    st.subheader("🔑 API Key Management")
    
    # Get all portfolios for the dropdown
    portfolios = portfolio_manager.db.get_all_portfolios()
    portfolio_options = {p.name: p.id for p in portfolios}
    
    # Add new API key
    with st.expander("➕ Add New API Key"):
        with st.form("add_api_key_form"):
            col1, col2 = st.columns(2)
            with col1:
                exchange = st.selectbox(
                    "Exchange",
                    ["Nexo", "Nexo Pro", "Binance", "Kraken", "Coinbase"],
                    key="api_key_exchange"
                )
                name = st.text_input("Name/Description", help="A friendly name to identify this API key")
            
            with col2:
                portfolio_id = st.selectbox(
                    "Link to Portfolio (Optional)",
                    options=[""] + list(portfolio_options.keys()),
                    format_func=lambda x: "Select a portfolio..." if x == "" else x,
                    key="api_key_portfolio"
                )
                
                # Only show API key/secret if not in production or in debug mode
                api_key = st.text_input("API Key", type="password")
                api_secret = st.text_input("API Secret", type="password")
            
            if st.form_submit_button("Save API Key"):
                if not all([exchange, name, api_key, api_secret]):
                    st.error("Please fill in all required fields.")
                else:
                    try:
                        portfolio_id_value = portfolio_options.get(portfolio_id) if portfolio_id else None
                        api_key_manager.add_api_key(
                            exchange=exchange,
                            name=name,
                            api_key=api_key,
                            api_secret=api_secret,
                            portfolio_id=portfolio_id_value
                        )
                        st.success(f"API key for {exchange} added successfully!")
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Error adding API key: {str(e)}")
    
    # List existing API keys
    st.subheader("🔐 Your API Keys")
    
    api_keys = api_key_manager.get_all_api_keys()
    
    if not api_keys:
        st.info("No API keys found. Add your first API key above.")
        return
    
    for key in api_keys:
        with st.expander(f"{key['exchange']} - {key['name']}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**ID:** {key['id']}")
                st.markdown(f"**Exchange:** {key['exchange']}")
                st.markdown(f"**Name:** {key['name']}")
                st.markdown(f"**Status:** {'🟢 Active' if key['is_active'] else '🔴 Inactive'}")
                
                # Show portfolio link if exists
                if key['portfolio_id']:
                    portfolio = next((p for p in portfolios if p.id == key['portfolio_id']), None)
                    if portfolio:
                        st.markdown(f"**Linked to:** {portfolio.name}")
            
            with col2:
                st.markdown(f"**API Key:** `{key['api_key']}`")
                st.markdown(f"**API Secret:** `{key['api_secret']}`")
                st.markdown(f"**Created:** {key['created_at']}")
                st.markdown(f"**Last Updated:** {key['updated_at']}")
            
            # Edit/Delete buttons
            col1, col2, _ = st.columns([1, 1, 3])
            
            with col1:
                if st.button("Edit", key=f"edit_{key['id']}"):
                    st.session_state[f"editing_key_{key['id']}"] = True
                
                if st.session_state.get(f"editing_key_{key['id']}", False):
                    with st.form(key=f"edit_form_{key['id']}"):
                        new_name = st.text_input("Name", value=key['name'])
                        new_portfolio = st.selectbox(
                            "Link to Portfolio",
                            [""] + list(portfolio_options.keys()),
                            index=0 if not key['portfolio_id'] else 
                                list(portfolio_options.values()).index(key['portfolio_id']) + 1,
                            format_func=lambda x: "Select a portfolio..." if x == "" else x,
                            key=f"edit_portfolio_{key['id']}"
                        )
                        new_status = st.checkbox("Active", value=key['is_active'])
                        
                        if st.form_submit_button("Save Changes"):
                            try:
                                portfolio_id_value = portfolio_options.get(new_portfolio) if new_portfolio else None
                                api_key_manager.update_api_key(
                                    key_id=key['id'],
                                    name=new_name,
                                    portfolio_id=portfolio_id_value,
                                    is_active=new_status
                                )
                                st.success("API key updated successfully!")
                                st.session_state[f"editing_key_{key['id']}"] = False
                                st.experimental_rerun()
                            except Exception as e:
                                st.error(f"Error updating API key: {str(e)}")
            
            with col2:
                if st.button("Delete", key=f"delete_{key['id']}"):
                    if api_key_manager.delete_api_key(key['id']):
                        st.success("API key deleted successfully!")
                        st.experimental_rerun()
                    else:
                        st.error("Failed to delete API key.")
            
            st.markdown("---")
