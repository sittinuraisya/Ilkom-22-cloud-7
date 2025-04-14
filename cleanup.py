import os
import subprocess

def clean_code():
    """Run all code cleaning tools in sequence"""
    file_path = "e_cuti/app.py"
    
    print("Running autoflake...")
    subprocess.run(["autoflake", "--in-place", "--remove-unused-variables", 
                   "--remove-all-unused-imports", file_path])
    
    print("Running isort...")
    subprocess.run(["isort", file_path])
    
    print("Running autopep8...")
    subprocess.run(["autopep8", "--in-place", "--aggressive", file_path])
    
    print("Running black...")
    subprocess.run(["black", file_path, "--line-length", "79"])
    
    print("Cleaning completed!")

if __name__ == "__main__":
    clean_code()