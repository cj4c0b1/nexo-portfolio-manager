import os
import sys
from dotenv import load_dotenv

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

def test_nexo_connection():
    from nexo_client import get_nexo_client
    
    print("Testing Nexo API connection...")
    
    try:
        # Try to get a client (will use real credentials from .env)
        client = get_nexo_client(use_mock=False)
        print("✅ Successfully created Nexo client")
        
        # Test the connection by getting account summary
        print("\nFetching account summary...")
        account_summary = client.get_account_summary()
        
        if not account_summary:
            print("❌ Received empty account summary")
            return False
            
        print(f"✅ Successfully retrieved account summary")
        print("\nAccount Summary:")
        print("-" * 50)
        
        # Print the raw response for debugging
        print("\nRaw API Response:")
        print("-" * 50)
        print(account_summary)
        print("-" * 50)
        
        # Print basic account info
        if isinstance(account_summary, list):
            print(f"\nFound {len(account_summary)} assets in your account")
            print("\nBalances:")
            for asset in account_summary:
                if isinstance(asset, dict):
                    asset_name = asset.get('currency', 'UNKNOWN')
                    total = asset.get('balance', 0)
                    available = asset.get('available', 0)
                    print(f"- {asset_name}: {total} (Available: {available})")
        elif isinstance(account_summary, dict):
            if 'balances' in account_summary:
                print(f"\nFound {len(account_summary['balances'])} assets in your account")
                print("\nBalances:")
                for asset in account_summary['balances']:
                    if isinstance(asset, dict):
                        asset_name = asset.get('asset', asset.get('currency', 'UNKNOWN'))
                        total = asset.get('total', asset.get('balance', 0))
                        available = asset.get('available', 0)
                        print(f"- {asset_name}: {total} (Available: {available})")
        
        # Try to calculate total balance
        total_balance = 0
        if isinstance(account_summary, list):
            for asset in account_summary:
                if isinstance(asset, dict) and 'balance' in asset and 'usd_value' in asset:
                    total_balance += float(asset['usd_value'])
        elif isinstance(account_summary, dict) and 'total_balance_usd' in account_summary:
            total_balance = float(account_summary['total_balance_usd'])
            
        if total_balance > 0:
            print(f"\nTotal Balance: ${total_balance:,.2f} USD")
            
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
