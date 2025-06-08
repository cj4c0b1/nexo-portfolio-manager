# Create run.py - Easy script to run the application
run_script_content = '''#!/usr/bin/env python3
"""
Nexo Portfolio Manager - Run Script

Simple script to start the Streamlit application.
"""

import subprocess
import sys
import os
from pathlib import Path

def check_requirements():
    """Check if required packages are installed"""
    try:
        import streamlit
        import pandas
        import plotly
        import requests
        print("✅ All required packages are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def check_env_file():
    """Check if .env file exists"""
    env_file = Path(".env")
    if env_file.exists():
        print("✅ .env file found")
        return True
    else:
        print("⚠️  .env file not found")
        print("Copy .env.example to .env and add your API credentials")
        print("The app will run in mock mode without API credentials")
        return False

def main():
    """Run the Streamlit application"""
    
    print("🚀 Starting Nexo Portfolio Manager...")
    print("=" * 50)
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Check environment file
    check_env_file()
    
    # Change to the project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    # Run Streamlit
    try:
        print("\\n🌐 Starting Streamlit server...")
        print("📱 The application will open in your default browser")
        print("🛑 Press Ctrl+C to stop the server")
        print("=" * 50)
        
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "app/main.py",
            "--server.port=8501",
            "--server.address=localhost"
        ])
        
    except KeyboardInterrupt:
        print("\\n🛑 Application stopped by user")
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''

with open("nexo_portfolio_manager/run.py", "w") as f:
    f.write(run_script_content)

print("Created run.py script successfully!")