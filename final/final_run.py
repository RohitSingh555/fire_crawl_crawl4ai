import subprocess
import json
import os

# Function to run a script and check for success
def run_script(script_name):
    try:
        print(f"Running {script_name}...")
        subprocess.run(['python', script_name], check=True)  # Run the script
        print(f"{script_name} executed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error running {script_name}: {e}")

# Function to load JSON data from a file
def load_json(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return json.load(file)
    else:
        print(f"Warning: {file_path} does not exist.")
        return {}

# Function to save merged JSON data to a file
def save_json(data, output_file):
    with open(output_file, 'w') as file:
        json.dump(data, file, indent=4)
    print(f"Merged URLs saved to {output_file}")

# Master function to run all scripts and merge URLs
def run_all_scripts_and_merge_urls():
    # List of individual scripts
    scripts = [
        "news3.py",  
        "abcnews.py",     
        "scrapping_urls.py",     
    ]
    
    for script in scripts:
        run_script(script)

    urls_from_scripts = [
        "combined_fire_urls.json",  
        "news_urls.json",    
        "fire_urls.json",    
    ]
    
    merged_urls = {}

    for url_file in urls_from_scripts:
        urls = load_json(url_file)
        for domain, url_list in urls.items():
            if domain not in merged_urls:
                merged_urls[domain] = []
            merged_urls[domain].extend(url_list)

    for domain, url_list in merged_urls.items():
        merged_urls[domain] = list(set(url_list))  # Remove duplicates

    save_json(merged_urls, 'fire_scraped_urls.json')

    # Run verification.py after merging
    run_script("verification.py")

    # Run excel.py after verification
    run_script("excel.py")

# Call the function to run all scripts and merge URLs
run_all_scripts_and_merge_urls()
