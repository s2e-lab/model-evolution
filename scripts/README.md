# Scripts Folder

## Requirements
- [Python 3.10+](https://www.python.org/downloads/)
- [Pip](https://pip.pypa.io/en/stable/installation/)
- [Git](https://git-scm.com/downloads)
- [HuggingFace](https://huggingface.co/) account
- [SSH](https://huggingface.co/docs/hub/en/security-git-ssh) keys for HuggingFace.
- [GeckoDriver](https://github.com/mozilla/geckodriver/releases) for Selenium (for SFConvertBot data collection)
- [Firefox](https://www.mozilla.org/en-US/firefox/new/) browser (for SFConvertBot data collection)

**All scripts were tested on Windows 10 and macOS. The scripts should work on Linux as well, but we did not test them on this platform.**

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



### RQ1/RQ2: Getting Models Metadata & Commits from HuggingFace
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
It requires the start and end index of the models to be processed. This script will take a long time to run (~1 day).
```bash
python get_commit_logs.py <start_index> <end_index>
```
Example: below it will process the first 517 models and then the next 517 models.
```bash
python get_commit_logs.py 0 517
python get_commit_logs.py 517 1035 
```
    
#### Step 4: Merging the commit history into a single CSV file
- `./merge_csvs.sh`: Merge the CSV files for the commit history into a single file.
  ```bash
  ./merge_csvs.sh ../data huggingface_sort_by_createdAt_top996939_
  ```
  The script will merge all the CSV files in the `../data/` folder into tw single files:
`../data/huggingface_sort_by_createdAt_top996939_commits_<first_index>_<last_index>.csv`
and `../data/huggingface_sort_by_createdAt_top996939_errors_<first_index>_<last_index>.csv`.
    
#### Step 5: Analyzing the commit history to identify the serialization format
- `analyze_commit_history.py`: Script to analyze the commit history of the models to identify the serialization format using at a given time.
  ```bash
  python analyze_commit_history.py <start_index> <end_index>
  ```
  It requires the start and end index of the commits to be processed.
  The script will generate a CSV file with the commit history analysis on the `../results/` folder. 

### RQ3: Scraping StackOverflow posts and GitHub PRs

#### Step 1: Create a `.env` file
Create a `.env` file in the root directory with the following content:
```bash
GITHUB_TOKEN=<your_github_token>
```
Replace `<your_github_token>` with your GitHub token. 
You can create a token by following the instructions [here](https://docs.github.com/en/github/authenticating-to-github/keeping-your-account-and-data-secure/creating-a-personal-access-token).

#### Step 2: Run our crawlers

Now, you can run the following shell scripts to collect data from GitHub and StackOverflow.

- **Collecting PRs from GitHub:** Run the shell script below to trigger the data collection process.
    ```bash
    ./GH-collection.sh
    ```
- **Collecting StackOverflow posts:** Run the shell script below to trigger the data collection process.
    ```bash
    ./SO-collection.sh
    ```
The data will be saved in the `data` folder.

### RQ4: Getting SFConvertBot Data

#### Step 0: Install the required packages
- Download the [web driver](https://github.com/mozilla/geckodriver/releases) for the Firefox browser and extract it to your PATH (e.g., /usr/local/bin).
- If it is not in `PATH` you need to set its path in the `crawl_bot_activity.py` script.


#### Step 1: Extract Safetensors' versions 
- `get_sfconvertbot_tags.sh`: Script to get all the safetensors versions.
  ```bash
  ./get_sfconvertbot_tags.sh
  ```
  It will save the list of versions in `../data/safetensors_tags.csv`.
  Notice that safetensors has versions released on the same date (one named `v0.N.M` and the other `python-v0.N.M`). 
  We manually removed the `python-` suffixes and removed duplicates prior to generating our charts. 

#### Step 2: Crawling the PRs from the SFConvertBot's community activity
- `./bot/crawl_bot_activity.py`: Script to get a list of PRs from the SFConvertBot's community [activity](https://huggingface.co/SFconvertbot/activity/community).
  ```bash
  cd bot
  python crawl_bot_activity.py
  ```
  It will save the data in `../data/sfconvertbot_pr_urls.csv`.

#### Step 3: Get Conversion Dataset from HuggingFace
- `get_conversions_dataset.py`: Script to get the SFConvertBot's conversion [dataset](https://huggingface.co/datasets/safetensors/conversions).
  ```bash
  python get_sfconvert_dataset.py
  ```
  It will save the data in `../data/hf_conversions.csv`.

#### Step 4: Extract SFConvertBot activities' metadata and merge with convert dataset 
- `get_sfconvert_prs.py`: Script to get the metadata from the SFConvertBot's PR URLs obtained in step 2 and merge with the dataset obtained in step 3.
  ```bash
  python get_sfconvert_prs.py
  ```
  It will save the data in `../data/sfconvertbot_pr_metadata.csv.zip`.
  File is zipped because it is too large to be stored in the repository.

  

## Data Analysis

All of the analysis and charts shown in the paper are generated using the Jupyter notebooks in the `notebooks` folder.
Each RQ has a separate notebook for analysis.

- `./notebooks/rq1_analysis.ipynb`: Analysis of RQ1.
- `./notebooks/rq2_analysis.ipynb`: Analysis of RQ2.
- `./notebooks/rq3_analysis.ipynb`: Analysis of RQ3.
- `./notebooks/rq4_analysis.ipynb`: Analysis of RQ4.

To run the notebooks, you need to start the Jupyter server by running the command below:
```bash
cd notebooks
jupyter notebook
```
Then, open the desired notebook and run the cells.

## License
TBD.

## Citation
TBD.

## Contributors
J. 
Does