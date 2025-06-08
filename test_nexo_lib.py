import os
import sys
from dotenv import load_dotenv
import nexo

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

def test_nexo_connection():
    print("Testing Nexo API connection using python-nexo library...")
    
    try:
        # Get API keys from environment variables
        key = os.getenv("NEXO_PUBLIC_KEY")
        secret = os.getenv("NEXO_SECRET_KEY")
        
        if not key or not secret:
            print("❌ Error: NEXO_PUBLIC_KEY and NEXO_SECRET_KEY must be set in .env file")
            return False
            
        print(f"Using API key: {key[:5]}...{key[-5:]}")
        
        # Initialize the Nexo client
        client = nexo.Client(key, secret)
        
        # Test connection by getting account balances
        print("\nFetching account balances...")
        balances = client.get_account_balances()
        
        if not balances:
            print("❌ Received empty balances")
            return False
            
        print("✅ Successfully retrieved account balances")
        print("\nAccount Balances:")
        print("-" * 50)
        
        # Print the raw response for debugging
        print("\nRaw API Response:")
        print("-" * 50)
        print(balances)
        print("-" * 50)
        
        # Print formatted balances
        print("\nFormatted Balances:")
        print("-" * 50)
        
        if isinstance(balances, list):
            for balance in balances:
                if isinstance(balance, dict):
                    currency = balance.get('currency', 'UNKNOWN')
                    amount = balance.get('balance', 0)
                    available = balance.get('available', 0)
                    print(f"{currency}: {amount} (Available: {available})")
        elif isinstance(balances, dict):
            for currency, balance in balances.items():
                if isinstance(balance, dict):
                    amount = balance.get('balance', 0)
                    available = balance.get('available', 0)
                    print(f"{currency}: {amount} (Available: {available})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("\nTroubleshooting steps:")
        print("1. Make sure your API credentials in .env are correct")
        print("2. Check your internet connection")
        print("3. Verify that the Nexo API is operational")
        print("4. Ensure your API key has the necessary permissions")
        return False

if __name__ == "__main__":
    test_nexo_connection()