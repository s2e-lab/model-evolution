#!/bin/bash

# Execute parse-SO.py
echo "Running parse-SO.py..."
python3 parse-SO.py

# Check if parse-SO.py was successful
if [ $? -ne 0 ]; then
  echo "Error: parse-SO.py did not run successfully."
  exit 1
fi

# Execute dupcheck-json.py
echo "Running dupcheck-json.py..."
python3 dupcheck-json.py

# Check if dupcheck-json.py was successful
if [ $? -ne 0 ]; then
  echo "Error: dupcheck-json.py did not run successfully."
  exit 1
fi

# Execute count-json.py
echo "Running count-json.py..."
python3 count-json.py

# Check if count-json.py was successful
if [ $? -ne 0 ]; then
  echo "Error: count-json.py did not run successfully."
  exit 1
fi

echo "All scripts executed successfully."
