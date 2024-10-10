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

# Execute GH_dupcheck.py
echo "Running GH_dupcheck.py..."
python3 github/GH_dupcheck.py $output_file

# Check if GH_dupcheck.py was successful
if [ $? -ne 0 ]; then
  echo "Error: GH_dupcheck.py did not run successfully."
  exit 1
fi

# Convert JSON to CSV
echo "Converting JSON to CSV..."
python3 github/GH_json_to_csv.py $output_file
# Check if GH_json_to_csv.py was successful
if [ $? -ne 0 ]; then
  echo "Error: GH_json_to_csv.py did not run successfully."
  exit 1
fi

echo "All scripts executed successfully."
