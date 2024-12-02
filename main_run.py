import subprocess
import sys

files_to_run = [
    "create_sitemap_step_one.py",
    "get_last_modified_date.py",
    "clean_json.py",
    # "crawler_by_umang.py",  
    # "crawler_by_rohit.py", 
    # "final_crawler.py", 
    "final_crawler_2.py", 
]

def run_script(script_name):
    try:
        print(f"Running: {script_name}")
        subprocess.run([sys.executable, script_name], check=True)
        print(f"Successfully executed: {script_name}")
    except subprocess.CalledProcessError as e:
        print(f"Error while running {script_name}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    for file in files_to_run:
        run_script(file)
    print("All scripts executed successfully.")
