import ast
import subprocess
import pkg_resources
import os
import tkinter as tk
from tkinter import filedialog, messagebox

def get_imports_from_file(filepath):
    with open(filepath, "r") as file:
        tree = ast.parse(file.read(), filename=filepath)

    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            imports.add(node.module.split('.')[0])
    return imports

def get_package_version(package_name):
    try:
        return pkg_resources.get_distribution(package_name).version
    except pkg_resources.DistributionNotFound:
        return None

def generate_requirements_file(script_file, output_file="requirements.txt"):
    imports = get_imports_from_file(script_file)
    requirements = []
    
    for package in imports:
        version = get_package_version(package)
        if version:
            requirements.append(f"{package}=={version}")
        else:
            requirements.append(package)
    
    script_dir = os.path.dirname(script_file)
    output_path = os.path.join(script_dir, output_file)

    with open(output_path, "w") as file:
        file.write("\n".join(requirements))
    
    print(f"Requirements written to {output_path}")

def main():
    root = tk.Tk()
    root.withdraw()  # Hide the main window

    script_file = filedialog.askopenfilename(
        title="Select Python Script",
        filetypes=[("Python files", "*.py"), ("All files", "*.*")]
    )

    if not script_file:
        messagebox.showerror("Error", "No file selected. Exiting.")
        return

    generate_requirements_file(script_file)

if __name__ == "__main__":
    main()
