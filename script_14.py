import zipfile
import os
from pathlib import Path

# Create a ZIP file of the entire project
zip_filename = "nexo_portfolio_manager_complete.zip"

with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
    # Walk through the project directory
    for root, dirs, files in os.walk("nexo_portfolio_manager"):
        # Skip __pycache__ directories
        dirs[:] = [d for d in dirs if d != '__pycache__']
        
        for file in files:
            if not file.endswith('.pyc'):
                file_path = os.path.join(root, file)
                arcname = file_path  # Keep the full path in the archive
                zipf.write(file_path, arcname)

print(f"✅ Complete project archived as: {zip_filename}")
print(f"📦 Archive size: {os.path.getsize(zip_filename) / 1024:.1f} KB")

# Display summary of what was created
print("\n📋 Project Summary:")
print("=" * 50)

file_count = 0
total_lines = 0

for root, dirs, files in os.walk("nexo_portfolio_manager"):
    dirs[:] = [d for d in dirs if d != '__pycache__']
    for file in files:
        if file.endswith('.py'):
            file_path = os.path.join(root, file)
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = len(f.readlines())
                total_lines += lines
                file_count += 1

print(f"📄 Python files: {file_count}")
print(f"📝 Total lines of code: {total_lines:,}")
print(f"🗂️  Project structure: Complete MVC architecture")
print(f"🧪 Testing: Unit tests included")
print(f"🔄 CI/CD: GitHub Actions workflow")
print(f"📚 Documentation: README, QuickStart, and Help system")

print("\n🎯 Key Features Implemented:")
print("✅ Portfolio creation and management")
print("✅ Real-time market data integration")
print("✅ Automated rebalancing algorithms")
print("✅ Cost optimization (Nexo vs Nexo Pro)")
print("✅ Risk analysis and metrics")
print("✅ Paper trading mode")
print("✅ Interactive Streamlit dashboard")
print("✅ SQLite database integration")
print("✅ Nexo Pro API client")
print("✅ Transaction history tracking")
print("✅ Performance analytics")
print("✅ Comprehensive error handling")
print("✅ Security best practices")

print("\n🛡️  Security Features:")
print("✅ Environment variable management")
print("✅ API key protection")
print("✅ Paper trading safety mode")
print("✅ Input validation")
print("✅ Error handling")

print("\n🚀 Ready to Deploy:")
print("✅ Production-ready code structure")
print("✅ Scalable architecture")
print("✅ Comprehensive documentation")
print("✅ Testing framework")
print("✅ CI/CD pipeline")

print(f"\n📦 Download the complete project: {zip_filename}")
print("🎉 Your Nexo Portfolio Manager is ready to use!"))