import os

# Define project structure
project_structure = {
    "app": [
        "main.py",
        "crawl_utils.py",
        "database.py",
        "models.py",
        "schemas.py",
        {"routers": ["data.py"]},
        {"services": ["prompt_service.py"]},
        "websites.json",
    ],
    "attachments": [],
    "frontend": ["index.html", {"assets": []}],
    "requirements.txt": None,
    "README.md": None,
}

# Base directory for the project
base_dir = "project"

# Function to create the directory structure
def create_structure(base_path, structure):
    for key, value in structure.items():
        dir_path = os.path.join(base_path, key) if isinstance(value, list) else base_path
        if isinstance(value, list) or isinstance(value, dict):
            os.makedirs(dir_path, exist_ok=True)
            if isinstance(value, list):
                create_structure(dir_path, {item if isinstance(item, str) else list(item.keys())[0]: list(item.values())[0] if isinstance(item, dict) else [] for item in value})
        elif value is None:
            with open(os.path.join(base_path, key), "w") as file:
                file.write("")

# Create project structure
os.makedirs(base_dir, exist_ok=True)
create_structure(base_dir, {key: value for key, value in project_structure.items() if not isinstance(value, dict)})

print(f"Project structure created at {os.path.abspath(base_dir)}")
