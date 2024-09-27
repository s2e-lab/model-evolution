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
- **Step 1:**
  - `get_models.py`: Script to get metadata of all models from HuggingFace. 
  Make sure that you've setup your [HF SSH keys](https://huggingface.co/docs/hub/en/security-git-ssh).
    ```bash
    python get_models.py
    ```
- **Step 2:**
  - `get_models_history.py`: Script to get metadata of all models from HuggingFace. 
  It will produce commit history for each model repository and save it on the data folder. 
  It requires the start and end index of the models to be processed.
    ```bash
    python get_models_history.py <start_index> <end_index>
    ```

### Scraping StackOverflow posts
