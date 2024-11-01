# Scripts Folder

## Requirements
- [Python 3.10+](https://www.python.org/downloads/)
- [Pip](https://pip.pypa.io/en/stable/installation/)
- [Git](https://git-scm.com/downloads)
- [HuggingFace](https://huggingface.co/) account
- [SSH](https://huggingface.co/docs/hub/en/security-git-ssh) keys for HuggingFace.

## Setup
- Install the required packages using `pip install -r requirements.txt`
- Install our local dependency 
```bash
git clone https://github.com/s2e-lab/AnalyticaML.git
cd AnalyticaML
pip install .
```
- Set up your [SSH](https://huggingface.co/docs/hub/en/security-git-ssh) keys locally to access the HuggingFace API.

## Data Collection

### Scraping StackOverflow posts and GitHub PRs

1) Create a `.env` file in the root directory with the following content:
```bash
GITHUB_TOKEN=<your_github_token>

```
2) Now, you can run the following shell scripts to collect data from GitHub and StackOverflow.

- **Collecting PRs from GitHub:** Run the shell script below to trigger the data collection process.
    ```bash
    GH-collection.sh
    ```
- **Collecting StackOverflow posts:** Run the shell script below to trigger the data collection process.
    ```bash
    SO-collection.sh
    ```
The data will be saved in the `data` folder.

### Getting Models Metadata & Commits from HuggingFace
***(Make sure that you've set up your [HF SSH keys](https://huggingface.co/docs/hub/en/security-git-ssh))***

#### Step 1: Getting the metadata of the models
- `get_models.py`: Script to get metadata of all models from HuggingFace. 
  ```bash
  python get_models.py
  ```
  It will save the metadata of all models in the `../data/` folder.
  File name will be `huggingface_sort_by_createdAt_topN.json`, where `N` is the number of model repositories.

#### Step 2: Filtering the models using the criteria described in our methodology
- `./notebooks/select_models.ipynb`: Script to filter the repositories from HuggingFace using our filtering criteria based on creation / last update dates. 
  ```bash
  cd notebooks
  jupyter notebook select_models.ipynb
  ```
  It will select model repositories and save the filtered list at `../data/huggingface_sort_by_createdAt_topN_selected.json`.   
  
#### Step 3: Getting the commit history of the models
- `get_models_history.py`: Script to get metadata of all models from HuggingFace. 
It will produce commit history for each model repository and save it on the data folder. 
It requires the start and end index of the models to be processed.
```bash
python get_commit_logs.py <start_index> <end_index>
```
Example: below it will process the first 517 models and then the next 517 models.
```bash
python get_commit_logs.py 0 517
python get_commit_logs.py 517 1035 
```
    
#### Step 4: Merging the commit history into a single CSV file
- `./merge_commit_history.sh`: Merge the CSV files for the commit history into a single file.
  ```bash
  ./merge_commit_history.sh
  ```
  The script will merge all the CSV files in the `../data/` folder into a single file `../data/huggingface_sort_by_createdAt_top996939_commits_<first_index>_<last_index>.csv`.
    
#### Step 5: Analyzing the commit history to identify the serialization format
- `analyze_commit_history.py`: Script to analyze the commit history of the models to identify the serialization format using at a given time.
  ```bash
  python analyze_commit_history.py <start_index> <end_index>
  ```
  It requires the start and end index of the commits to be processed.
  The script will generate a CSV file with the commit history analysis on the `../results/` folder. 

### Getting SFConvertBot Data

#### Step 1: Extract Safetensors' versions 
- `get_sfconvertbot_tags.sh`: Script to get all the safetensors versions.
  ```bash
  ./get_sfconvertbot_tags.sh
  ```
  It will save the list of versions in `../data/safetensors_tags.csv`.
  Notice that safetensors has versions released on the same date (one named `v0.N.M` and the other `python-v0.N.M`). 
  We manually removed the `python-` suffixes and removed duplicates prior to generating our charts. 

#### Step 2: Extract SFConvertBot PRs 
- `get_sfconvert_prs.py`: Script to get the data from the SFConvertBot.
  ```bash
  python get_sfconvert_prs.py
  ```
  It will save the data in `../data/sfconvertbot_pr_metadata.csv`.


## Data Analysis

All of the analysis and charts shown in the paper are generated using the Jupyter notebooks in the `notebooks` folder.
Each RQ has a separate notebook for analysis.

