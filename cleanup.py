import subprocess
import sys

def clean_file(file_path):
    tools = [
        ("autoflake", ["--in-place", "--remove-unused-variables", "--remove-all-unused-imports", file_path]),
        ("isort", [file_path]),
        ("autopep8", ["--in-place", "--aggressive", file_path]),
        ("black", [file_path, "--line-length", "120"])
    ]
    
    for tool, args in tools:
        print(f"Running {tool}...")
        try:
            subprocess.run([tool] + args, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error running {tool}: {e}")
            sys.exit(1)
    
    print("Cleaning completed successfully!")

if __name__ == "__main__":
    clean_file("e_cuti/app.py")