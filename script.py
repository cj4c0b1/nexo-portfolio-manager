import os
import textwrap

# Create project directory structure
project_structure = {
    "nexo_portfolio_manager": {
        "app": {
            "api": {},
            "db": {},
            "components": {},
            "utils": {}
        },
        "config": {},
        "tests": {},
        "data": {}
    }
}

def create_directory_structure(structure, base_path=""):
    for name, content in structure.items():
        current_path = os.path.join(base_path, name)
        if isinstance(content, dict):
            os.makedirs(current_path, exist_ok=True)
            create_directory_structure(content, current_path)
        else:
            # This would be a file
            with open(current_path, 'w') as f:
                f.write(content)

# Create the structure
create_directory_structure(project_structure)
print("Project directory structure created successfully!")
print("\nProject Structure:")
for root, dirs, files in os.walk("nexo_portfolio_manager"):
    level = root.replace("nexo_portfolio_manager", '').count(os.sep)
    indent = ' ' * 2 * level
    print(f"{indent}{os.path.basename(root)}/")
    subindent = ' ' * 2 * (level + 1)
    for file in files:
        print(f"{subindent}{file}")