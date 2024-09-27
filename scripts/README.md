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

### Getting Models Metadata from HuggingFace
***(Make sure that you've set up your [HF SSH keys](https://huggingface.co/docs/hub/en/security-git-ssh))***

- **Step 1:**
  - `get_models.py`: Script to get metadata of all models from HuggingFace. 
    ```bash
    python get_models.py
    ```
- **Step 2:**
  - `get_models_history.py`: Script to get metadata of all models from HuggingFace. 
  It will produce commit history for each model repository and save it on the data folder. 
  It requires the start and end index of the models to be processed.
    ```bash
    python get_repos_history.py <start_index> <end_index>
    ```
    Example: below it will process the first 517 models and then the next 517 models.
    ```bash
    python get_repos_history.py 0 517
    python get_repos_history.py 517 1035 
    ```

### Scraping StackOverflow posts
