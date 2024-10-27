import json
import csv
import sys

def convert_json_to_csv(json_input_file, csv_output_file):
    with open (json_input_file, encoding='utf-8') as f:
        data = json.load(f)

    with open (csv_output_file, "w", encoding='utf-8') as f:
        csv_writer = csv.writer(f, delimiter=",", quotechar='"',  lineterminator="\n")
        csv_writer.writerow(["source", "title", "url", "json content"])

        for entry in data:
            csv_writer.writerow(["GitHub", entry["title"], entry["url"], json.dumps(entry)])

    print(f"{json_input_file} converted to .csv and written to {csv_output_file}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python GH_json_to_csv.py <json-file>")
        sys.exit(1)

    json_file = sys.argv[1]
    output_file = json_file.replace('.json', '.csv')
    # Convert .json to .csv
    convert_json_to_csv(json_file, output_file)
