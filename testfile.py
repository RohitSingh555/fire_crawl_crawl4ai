import json

def remove_duplicates_from_file(input_file, output_file, unique_field):
    """
    Reads a JSON file, removes duplicate entries based on a specific field, and saves the result to a new file.
    
    :param input_file: Path to the input JSON file
    :param output_file: Path to save the output JSON file
    :param unique_field: The field to use for identifying duplicates
    """
    try:
        # Load the JSON data from the input file with UTF-8 encoding
        with open(input_file, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        # Ensure the data is a list
        if not isinstance(data, list):
            print("Error: JSON data must be a list of dictionaries.")
            return
        
        # Remove duplicates
        seen = set()
        unique_data = []
        for entry in data:
            if entry[unique_field] not in seen:
                seen.add(entry[unique_field])
                unique_data.append(entry)
        
        # Save the unique data to the output file with UTF-8 encoding
        with open(output_file, 'w', encoding='utf-8') as file:
            json.dump(unique_data, file, indent=4, ensure_ascii=False)
        
        print(f"Duplicate removal complete. Cleaned data saved to {output_file}")
    except Exception as e:
        print(f"An error occurred: {e}")

# Example usage
input_file = "results_of_fire_incidents_28th_nov.json"  # Path to your input JSON file
output_file = "output.json"  # Path to save the output JSON file
unique_field = "title"  # Field to identify duplicates

remove_duplicates_from_file(input_file, output_file, unique_field)
