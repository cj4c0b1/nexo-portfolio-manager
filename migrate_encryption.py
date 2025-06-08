"""
Migration script for updating the encryption system.

This script helps migrate existing API keys to the new encryption system.
It should be run once after updating the database.py file.
"""
import os
import sys
from cryptography.fernet import Fernet, InvalidToken
from database import DatabaseManager

def main():
    print("🔑 Nexo Portfolio Manager - Encryption Migration Tool")
    print("=" * 50)
    
    # Initialize the database
    db = DatabaseManager()
    
    # Check if we have any API keys to migrate
    with sqlite3.connect(db.db_path) as conn:
        cursor = conn.cursor()
        
        # Check if we have any API keys
        cursor.execute('SELECT COUNT(*) FROM api_keys')
        key_count = cursor.fetchone()[0]
        
        if key_count == 0:
            print("✅ No API keys found in the database. No migration needed.")
            return
            
        print(f"Found {key_count} API keys in the database.")
        
        # Get the current encryption key
        cursor.execute('SELECT value FROM app_settings WHERE key = ?', ('encryption_key',))
        result = cursor.fetchone()
        
        if not result:
            print("❌ No encryption key found in the database. This shouldn't happen!")
            return
            
        current_key = result[0]
        
        # Try to decrypt a key to check if the current key works
        cursor.execute('SELECT api_key FROM api_keys LIMIT 1')
        test_key = cursor.fetchone()
        
        if test_key:
            try:
                f = Fernet(current_key.encode())
                f.decrypt(test_key[0].encode()).decode()
                print("✅ Current encryption key is valid.")
                print("\nNo migration needed. Your API keys are already using the new encryption system.")
                return
            except (InvalidToken, Exception) as e:
                print(f"⚠️  Current encryption key is invalid: {e}")
        
        # Ask for the old encryption key
        print("\n🔐 Please enter your old encryption key (or leave empty to skip migration):")
        old_key = input("Old encryption key: ").strip()
        
        if not old_key:
            print("\n⚠️  Migration skipped. Your API keys will be inaccessible until you provide the correct key.")
            return
            
        # Verify the old key
        try:
            f = Fernet(old_key.encode())
            test_decrypted = f.decrypt(test_key[0].encode()).decode()
            print("✅ Old encryption key is valid.")
            
            # Generate a new key
            new_key = Fernet.generate_key().decode()
            print(f"\n🔒 Generated new encryption key: {new_key[:10]}...")
            
            # Ask for confirmation
            print("\n⚠️  WARNING: This will re-encrypt all API keys with the new key.")
            confirm = input("Are you sure you want to continue? (yes/no): ").strip().lower()
            
            if confirm != 'yes':
                print("\n❌ Migration cancelled by user.")
                return
                
            # Re-encrypt all keys
            print("\n🔄 Re-encrypting API keys...")
            success = db.reencrypt_all_keys(old_key, new_key)
            
            if success:
                print("\n✅ Migration completed successfully!")
                print("\nIMPORTANT: Please make a note of your new encryption key:")
                print(f"ENCRYPTION_KEY={new_key}")
                print("\nAdd this to your .env file to ensure future access to your API keys.")
            else:
                print("\n❌ Migration failed. Please check the error messages above.")
                
        except InvalidToken:
            print("\n❌ Invalid encryption key. Please try again with the correct key.")
        except Exception as e:
            print(f"\n❌ An error occurred: {e}")

if __name__ == "__main__":
    import sqlite3
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")
        sys.exit(1)