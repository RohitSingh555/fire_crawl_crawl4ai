import pandas as pd
import json

def json_to_excel(json_file, excel_file):
    try:
        # Load the JSON data
        with open(json_file, "r", encoding="utf-8") as file:
            data = json.load(file)

        # Convert JSON to DataFrame
        df = pd.DataFrame(data)

        # Save DataFrame to Excel
        df.to_excel(excel_file, index=False, engine="openpyxl")
        print(f"Excel file created: {excel_file}")
    except Exception as e:
        print(f"Error converting JSON to Excel: {e}")

# Replace these with your file paths
json_file = "final_result/confirmed_fire_articles_2024-11-27.json"  # Input JSON file path
excel_file = "output.xlsx"  # Output Excel file path

# Convert JSON to Excel
json_to_excel(json_file, excel_file)
