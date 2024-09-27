import json
import csv

def convert_json_to_csv(json_file, csv_file):
    # Open and load the JSON file
    with open(json_file, 'r') as f:
        data = json.load(f)

    # Open the CSV file for writing
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, lineterminator='\r\n\n')
        
        # Write the header row
        writer.writerow(['title', 'source', 'url', 'json_content'])

        # Iterate over items in the JSON
        for item in data.get("items", []):
            title = item.get('title', 'N/A')
            url = item.get('url', 'N/A')  # Assuming the URL of the post is stored in the 'url' field
            source = 'Stack Overflow'
            json_content = json.dumps(item, ensure_ascii=False)  # Store the whole item as JSON content

            # Write a row to the CSV file
            writer.writerow([title, source, url, json_content])

if __name__ == "__main__":
    # Convert SO.json to SO.csv
    convert_json_to_csv('SO.json', 'SO.csv')
