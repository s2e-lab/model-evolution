import json
import csv

json_input_file = '../data/GH_data_safetensor.json'
csv_output_file = '../data/GH_data_safetensor.csv'

with open (json_input_file) as f:
    data = json.load(f)

with open (csv_output_file, "w") as f:
    csv_writer = csv.writer(f)
    csv_writer.writerow(["source", "title", "url", "json content"])

    for entry in data:
        csv_writer.writerow(["GitHub", entry["title"], entry["url"], json.dumps(entry)])

print(f"{json_input_file} converted ti .csv and written to {csv_output_file}")