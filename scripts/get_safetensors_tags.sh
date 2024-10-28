git clone https://github.com/huggingface/safetensors.git
cd safetensors
#git tag --sort=-creatordate --format="%(tag) %(creatordate)"
git for-each-ref --sort=-creatordate --format '%(refname:short),%(creatordate:short)' refs/tags > ../data/safetensors_tags.csv
# add header tag,date
sed -i '1s/^/tag,date\n/' ../data/safetensors_tags.csv
cd ..
rm -rf safetensors