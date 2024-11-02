## Usage: bash scripts/merge_csv.sh
## Description: Merge all the CSV files into a single file.
## Input: several files named with the same prefix. For example:
##    data/huggingface_sort_by_createdAt_top996939_commits_[0-9]+_[0-9]+.csv
##    data/huggingface_sort_by_createdAt_top996939_errors_[0-9]+_[0-9]+.csv
## Output: a merged file with the same prefix. For example:
##    data/huggingface_sort_by_createdAt_top996939_commits_<first_index>_<last_index>.csv
##    data/huggingface_sort_by_createdAt_top996939_errors_<first_index>_<last_index>.csv

# read first parameter which is the folder
folder=$1
if [ -z "$folder" ]; then
    echo "Please provide the folder name as the first parameter."
    exit 1
fi
# read second parameter which is the prefix
prefix=$2
if [ -z "$prefix" ]; then
    echo "Please provide the prefix as the second parameter."
    echo "Example: bash ./merge_csv.sh data huggingface_sort_by_createdAt_top996939_"
    echho "Example: bash ./merge_csv.sh data fixed_repository_evolution_"
    echho "Example: bash ./merge_csv.sh data repository_evolution_"
    exit 1
fi


# cd to the folder
cd $folder


for suffix in "commits" "errors"; do
    # Determine the file pattern based on the suffix
    file_pattern="huggingface_sort_by_createdAt_top996939_${suffix}_*.csv"
    file_pattern="${prefix}${suffix}_*.csv"
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
    output_file="${prefix}${suffix}_${first_index}_${last_index}.csv"
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