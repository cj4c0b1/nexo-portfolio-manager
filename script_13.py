# Create setup.py for the project
setup_content = '''from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="nexo-portfolio-manager",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A comprehensive portfolio management system for Nexo and Nexo Pro platforms",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/nexo-portfolio-manager",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Office/Business :: Financial :: Investment",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "nexo-portfolio=app.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", "*.yml", "*.yaml"],
    },
)
'''

with open("nexo_portfolio_manager/setup.py", "w") as f:
    f.write(setup_content)

# Create a quick start guide
quickstart_content = '''# Nexo Portfolio Manager - Quick Start Guide

## Prerequisites

- Python 3.8 or higher
- Nexo Pro account (optional, for live trading)
- Git (for cloning the repository)

## Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd nexo_portfolio_manager
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# On Windows:
venv\\Scripts\\activate

# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables
```bash
# Copy the example file
cp .env.example .env

# Edit .env with your API credentials (optional)
# For testing, you can leave the API keys empty to use mock data
```

### 5. Run the Application
```bash
# Option 1: Use the run script
python run.py

# Option 2: Direct Streamlit command
streamlit run app/main.py
```

## First Steps

1. **Access the Application**: Open your browser to http://localhost:8501
2. **Create a Portfolio**: Go to the "Portfolio Setup" tab
3. **Choose an Allocation**: Select a preset or create custom allocation
4. **Enable Paper Trading**: Keep this enabled for testing
5. **Explore Features**: Try rebalancing, analytics, and dashboard features

## API Setup (Optional)

For live trading with Nexo Pro:

1. Log in to your Nexo Pro account
2. Go to Settings > API Management
3. Create new API credentials with "Trading Only" permissions
4. Enable IP whitelisting for security
5. Add credentials to your `.env` file:
   ```
   NEXO_PUBLIC_KEY=your_public_key_here
   NEXO_SECRET_KEY=your_secret_key_here
   ```

## Testing

Run the test suite:
```bash
python -m pytest tests/ -v
```

## Support

- Check the Help tab in the application
- Review the README.md file
- Submit issues on GitHub

## Important Notes

⚠️ **Always start with paper trading mode**
⚠️ **Never share your API keys**
⚠️ **Use at your own risk - this is educational software**

Happy portfolio managing! 🚀
'''

with open("nexo_portfolio_manager/QUICKSTART.md", "w") as f:
    f.write(quickstart_content)

# Display final project structure
print("🎉 Project created successfully!")
print("\n📁 Complete Project Structure:")
print("=" * 60)

def display_tree(directory, prefix=""):
    """Display directory tree structure"""
    items = sorted(os.listdir(directory))
    for i, item in enumerate(items):
        if item.startswith('.') and item not in ['.env.example', '.gitignore', '.github']:
            continue
            
        path = os.path.join(directory, item)
        is_last = i == len(items) - 1
        current_prefix = "└── " if is_last else "├── "
        print(f"{prefix}{current_prefix}{item}")
        
        if os.path.isdir(path) and not item.startswith('.'):
            extension = "    " if is_last else "│   "
            display_tree(path, prefix + extension)

display_tree("nexo_portfolio_manager")

print("\n" + "=" * 60)
print("🚀 Next Steps:")
print("1. cd nexo_portfolio_manager")
print("2. python -m venv venv")
print("3. source venv/bin/activate  # On Windows: venv\\Scripts\\activate")
print("4. pip install -r requirements.txt")
print("5. cp .env.example .env")
print("6. python run.py")
print("\n📖 See QUICKSTART.md for detailed instructions!")
print("⚠️  Remember to enable paper trading mode for testing!")