import csv
import json
import sys


def convert_json_to_csv(json_file, csv_file):
    # Open and load the JSON file
    with open(json_file, 'r') as f:
        data = json.load(f)

    # Open the CSV file for writing
    with open(csv_file, 'w', encoding='utf-8') as f:
        writer = csv.writer(f)

        # Write the header row
        writer.writerow(['title', 'source', 'url', 'json_content'])

        # Iterate over items in the JSON
        for item in data.get("items", []):
            title = item.get('title', 'N/A')
            url = f"https://stackoverflow.com/questions/{item.get('question_id')}"
            source = 'Stack Overflow'
            json_content = json.dumps(item, ensure_ascii=False)  # Store the whole item as JSON content

            # Write a row to the CSV file
            writer.writerow([title, source, url, json_content])


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python json-to-csv.py <json-file> <csv-file>")
        sys.exit(1)

    json_file = sys.argv[1]
    output_file = json_file.replace('.json', '.csv')
    # Convert .json to .csv
    convert_json_to_csv(json_file, output_file)
