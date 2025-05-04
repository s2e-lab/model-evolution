# Data Folder

- `hf_sort_by_createdAt_top996939.json.zip`: Compressed JSON file with metadata of all models from HuggingFace.
- `hf_sort_by_createdAt_topN_legacy_selected.json`: Group 1. Repositories created **before** safetensors'
  release.
- `hf_sort_by_createdAt_topN_recent_selected.json`. Group 2. Repositories created **after** safetensors'
  release. Notice that we downsample it to match the number of samples in the first group.
- `GH_data_safetensor.json`: GitHub PRs collected.
- `SO_data_safetensor.json`: StackOverflow posts collected.
- `GH_data_safetensor_sorted.csv`: GitHub PRs sorted by cosine similarity (descending).
- `SO_data_safetensor_sorted.csv`: StackOverflow posts sorted by cosine similarity (descending).
- `hf_sort_by_createdAt_top996939_commits_N_M.csv`: HuggingFace commit history for models N to M.
- `hf_sort_by_createdAt_top996939_errors_N_M.csv`: Error logs for models N to M.


  