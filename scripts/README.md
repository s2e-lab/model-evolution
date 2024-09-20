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

## Getting Models Metadata from HuggingFace
- `get_models.py`: Script to get metadata of all models from HuggingFace. 
Make sure to setup your [SSH](https://huggingface.co/docs/hub/en/security-git-ssh) keys to access the HuggingFace API. 


## Scraping StackOverflow posts
