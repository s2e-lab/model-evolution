import huggingface_hub

repo_names = ['safetensors/convert', 'safetensors/convert2', 'safetensors/convert_large']
# get the space info for each repo
for repo in repo_names:
    info = huggingface_hub.space_info(repo)
    print(repo, "created_at", info.created_at, "duplicated from", info.cardData.duplicated_from, sep='\t')



# This is when the dataset creation was disabled for the space safetensors/convert
# https://huggingface.co/spaces/safetensors/convert/commit/0b0a7a0e4fe0dc5a68dd847d9ca6c024fb134df4
# It seems that in prior versions the script used the user's token to create the PR
# https://huggingface.co/spaces/safetensors/convert/blob/9c99c64d6853249eaa9412ae378352a2f5f90d0a/convert.py
# This explains why I see commits not by the bot!