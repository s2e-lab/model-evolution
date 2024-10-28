#!/bin/bash


output_file='../data/SO_data_safetensor.json'

# Execute parse-SO.py
echo "Running parse-SO.py..."
python3 stackoverflow/parse-SO.py $output_file

# Check if parse-SO.py was successful
if [ $? -ne 0 ]; then
  echo "Error: parse-SO.py did not run successfully."
  exit 1
fi

# Execute dupcheck-json.py
echo "Running dupcheck-json.py..."
python3 stackoverflow/dupcheck-json.py $output_file

# Check if dupcheck-json.py was successful
if [ $? -ne 0 ]; then
  echo "Error: dupcheck-json.py did not run successfully."
  exit 1
fi

# Execute count-json.py
echo "Running count-json.py..."
python3 stackoverflow/count-json.py $output_file

# Check if count-json.py was successful
if [ $? -ne 0 ]; then
  echo "Error: count-json.py did not run successfully."
  exit 1
fi

# Convert JSON to CSV
echo "Converting JSON to CSV..."
python3 stackoverflow/json-to-csv.py $output_file
# Check if json-to-csv.py was successful
if [ $? -ne 0 ]; then
  echo "Error: json-to-csv.py did not run successfully."
  exit 1
fi

# Compute cosine similarity
echo "# Computing cosine similarity..."
csv_file=${output_file%.*}.csv
python3 analyze_devs_discussion.py $csv_file

# Check if analyze_devs_discussion.py was successful
if [ $? -ne 0 ]; then
  echo "Error: analyze_devs_discussion.py did not run successfully."
  exit 1
fi

# delete the CSV file
rm $csv_file


