import os
import sys
from dotenv import load_dotenv

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

def test_real_balances():
    from portfolio import PortfolioManager
    
    print("Testing real balance fetching with updated PortfolioManager...")
    
    try:
        # Initialize the portfolio manager
        portfolio_manager = PortfolioManager()
        
        # Get real balances
        print("\nFetching real balances...")
        real_balances = portfolio_manager.get_real_balances()
        
        if not real_balances:
            print("❌ No balances found or error occurred")
            return False
            
        print("✅ Successfully retrieved real balances")
        print("\nAccount Balances:")
        print("-" * 50)
        
        # Print formatted balances
        total_value = 0
        for asset, data in real_balances.items():
            print(f"{asset}:")
            print(f"  Available: {data['available']}")
            print(f"  Total: {data['total']}")
            print(f"  In Orders: {data['in_orders']}")
            print(f"  USD Value: ${data['usd_value']:.2f}")
            print("-" * 30)
            total_value += data['usd_value']
        
        print(f"\nTotal Portfolio Value: ${total_value:.2f}")
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("\nTroubleshooting steps:")
        print("1. Make sure your .env file contains valid NEXO_PUBLIC_KEY and NEXO_SECRET_KEY")
        print("2. Check your internet connection")
        print("3. Verify that the Nexo API is operational")
        return False

if __name__ == "__main__":
    test_real_balances()
