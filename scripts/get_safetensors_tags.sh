git clone https://github.com/huggingface/safetensors.git
cd safetensors

# create a CSV file with tags and dates
csv_file='../../data/safetensors_tags.csv'
rm -f $csv_file
echo "tag,date" > $csv_file
git for-each-ref --sort=-creatordate --format '%(refname:short),%(creatordate:short)' refs/tags >> $csv_file

cd ..
rm -rf safetensors