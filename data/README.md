# Data Folder

- `hf_sort_by_createdAt_top996939.json.zip`: Compressed JSON file with metadata of all models from HuggingFace.
- `selected_legacy_repos.json`: Group 1. Repositories created **before** safetensors' release.
- `selected_recent_repos.json`: Group 2. Repositories created **after** safetensors' release. Notice that we downsample
  it to match the number of samples in the first group.
- `GH_data_safetensor.json`: GitHub PRs collected.
- `SO_data_safetensor.json`: StackOverflow posts collected.
- `GH_data_safetensor_sorted.csv`: GitHub PRs sorted by cosine similarity (descending).
- `SO_data_safetensor_sorted.csv`: StackOverflow posts sorted by cosine similarity (descending).
- `selected_legacy_commits.csv` and `selected_recent_commits.csv`: HuggingFace commit history for models in both groups.
- `selected_legacy_errors.csv` and `selected_recent_errors.csv`: HuggingFace commit history errors for models in both
  groups.


  