## Usage: bash scripts/merge_commit_history.sh
## Description: Merge all the commit history files into a single file
#
#cd ../data
#
## Find the first and last index of the commit history files
#first_index=$(ls huggingface_sort_by_createdAt_top996939_commits_*.csv | head -n 1 | sed -E 's/.*_([0-9]+)_[0-9]+\.csv/\1/') &&
#last_index=$(ls huggingface_sort_by_createdAt_top996939_commits_*.csv | tail -n 1 | sed -E 's/.*_[0-9]+_([0-9]+)\.csv/\1/') &&
#output_file="huggingface_sort_by_createdAt_top996939_commits_${first_index}_${last_index}.csv" &&
#
## Check if the output file already exists
#if [ -f "$output_file" ]; then
#    echo "Output file $output_file already exists. Please remove it before running this script."
#    exit 1
#fi
#
## Start merging the commit history files
#echo "Merging commit history files into $output_file"
#head -n 1 $(ls huggingface_sort_by_createdAt_top996939_commits_*.csv | head -n 1) > "$output_file" &&
#tail -n +2 -q huggingface_sort_by_createdAt_top996939_commits_*.csv >> "$output_file"
#
#
## Check integrity by counting rows
#original_count=$(tail -n +2 -q huggingface_sort_by_createdAt_top996939_commits_*.csv | wc -l) &&
#merged_count=$(tail -n +2 "$output_file" | wc -l)
#
#if [ "$original_count" -eq "$merged_count" ]; then
#    echo "Merge successful: $original_count entries."
#else
#    echo "Merge failed: Original count is $original_count but merged count is $merged_count."
#fi
#
#cd ../scripts

cd ../data

for suffix in "commits" "errors"; do
    # Determine the file pattern based on the suffix
    file_pattern="huggingface_sort_by_createdAt_top996939_${suffix}_*.csv"
    files=($(ls $file_pattern))
    total_files=${#files[@]}
    if [ $total_files -eq 0 ]; then
        echo "No files found for suffix '${file_pattern}'."
        continue
    else
        echo "Found $total_files files for suffix '${suffix}'."
    fi


    # Extract the first and last index
    first_index=$(echo "${files[0]}" | sed -E 's/.*_([0-9]+)_[0-9]+\.csv/\1/')
    last_index=$(echo "${files[$((total_files - 1))]}" | sed -E 's/.*_[0-9]+_([0-9]+)\.csv/\1/')

    # Check if the extraction was successful
    if [ -z "$first_index" ] || [ -z "$last_index" ]; then
        echo "Failed to extract indices from file names for suffix '${suffix}'."
        exit 1
    fi

    output_file="huggingface_sort_by_createdAt_top996939_${suffix}_${first_index}_${last_index}.csv"
    if [ -f "$output_file" ]; then
        echo "Output file $output_file already exists. Please remove it before running this script."
        exit 1
    fi
    # Start merging with the header of the first file
    echo "Merging ${total_files} files for suffix '${suffix}' into $output_file"
    head -n 1 "${files[0]}" > "$output_file"

    # Process each file and track progress
    for ((i = 0; i < total_files; i++)); do
        file="${files[i]}"
        echo "Processing file $((i + 1)) of $total_files: $file\r"
        tail -n +2 "$file" >> "$output_file"
    done
    echo "\nCompleted merging for suffix '${suffix}'."

    # Check integrity by counting rows
    original_count=$(tail -n +2 -q "${files[@]}" | wc -l) &&
    merged_count=$(tail -n +2 "$output_file" | wc -l)

    # Verify the merge result
    if [ "$original_count" -eq "$merged_count" ]; then
        echo "Merge successful for suffix '${suffix}': $original_count entries."
    else
        echo "Merge failed for suffix '${suffix}': Original count is $original_count but merged count is $merged_count."
    fi
done

cd ../scripts