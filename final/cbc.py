import requests
import json

# Fire-related keywords list
fire_keywords = [
    "fire", "wildfire", "blaze", "flame", "heat", "burn", "inferno", "smoke", "firefighters", "firemen",
    "combustion", "embers", "spark", "wildfire", "brush fire", "forest fire", "structure fire", "arson", "explosion",
    "campfire", "stove", "bonfire", "incendiary", "ignition", "firestorm", "fire escape", "firetruck", "fire hose",
    "fire alarm", "fire extinguishers", "fire drill", "flamethrower", "fireplace", "flashover", "fire resistance",
    "fire retardant", "burnout", "smolder", "scorched", "pyro", "ash", "fire break", "firefighting", "controlled burn",
    "flame resistant", "fire safety", "fireproof", "fire hazard", "fire safety plan", "fire zone", "fire department",
    "rescue", "burning building", "fire department response", "fire risk", "fire control", "ignition point",
    "fire line", "emergency response", "fire damage", "fire services", "fire watch", "fire protection", "fire coverage",
    "fire escape plan", "fire prevention", "fire safety equipment", "combustible", "hotspot", "arsonist",
    "blaze containment", "fire warning", "fire signal", "fire reports", "fire alert", "cinder", "fire retardant material",
    "wildfire containment", "flash fire", "backfire", "high flames", "wildland fire", "firebreak", "fireline",
    "safety evacuation", "wildfire season", "fire-fighting equipment", "forest blaze", "fire outbreak", "fire jump",
    "hot embers", "fire flare", "overheated", "fire risk management", "fire safety regulations", "fire ecology",
    "fire damage report", "fireproofing", "overcooked", "smoke detector", "fuel load", "fire safety system",
    "flame spread", "fire spread", "extinguishing fire", "house fire", "urban fire", "firing pin", "fire control line",
    "burnt debris", "sparking", "fire drill practice", "burning structure", "fire department unit", "fire rescue teams",
    "fire source", "burning materials", "fire traces", "firewatch", "fire escape ladder", "urban wildfire", "extinguisher",
    "combustible material"
]

# API URL
url = "https://api.queryly.com/json.aspx?queryly_key=4690eece66c6499f&batchsize=120&query=fire&groups=live:0_4_2&showfaceted=true&facetedkey=pubDate&facetedvalue=24"

# Make the request
response = requests.get(url)

if response.status_code == 200:
    data = response.json()

    publisher_urls = {}

    # Loop through the 'items' in the JSON response
    links = [item['link'] for item in data.get('items', [])]

    # Filter URLs that contain any of the fire-related keywords
    filtered_links = [
        link for link in links if any(keyword in link.lower() for keyword in fire_keywords)
    ]

    publisher_name = "https://www.cbsnews.com"  # You can adjust this based on the 'feedname' or another field.

    publisher_urls[publisher_name] = filtered_links

    # Convert the filtered data to a JSON format
    output_data = json.dumps(publisher_urls, indent=4)

    # Print the output
    print(output_data)

    # Save the output to a file
    with open('output2.json', 'w') as f:
        f.write(output_data)

else:
    print("Failed to retrieve data. Status code:", response.status_code)
