#!/bin/bash

output_file='../data/GH_data_safetensor.json'

# Execute GH_collect_safetensor.py
echo "Running GH_collect_safetensor.py..."
python3 github/GH_collect_safetensor.py $output_file

# Check if script was successful
if [ $? -ne 0 ]; then
  echo "Error: GH_collect_safetensor.py did not run successfully."
  exit 1
fi
#
## Execute dupcheck-json.py
#echo "Running dupcheck-json.py..."
#python3 stackoverflow/dupcheck-json.py $output_file
#
## Check if dupcheck-json.py was successful
#if [ $? -ne 0 ]; then
#  echo "Error: dupcheck-json.py did not run successfully."
#  exit 1
#fi
#
## Execute count-json.py
#echo "Running count-json.py..."
#python3 stackoverflow/count-json.py $output_file
#
## Check if count-json.py was successful
#if [ $? -ne 0 ]; then
#  echo "Error: count-json.py did not run successfully."
#  exit 1
#fi
#
## Convert JSON to CSV
#echo "Converting JSON to CSV..."
#python3 stackoverflow/json-to-csv.py $output_file
## Check if json-to-csv.py was successful
#if [ $? -ne 0 ]; then
#  echo "Error: json-to-csv.py did not run successfully."
#  exit 1
#fi

echo "All scripts executed successfully."
