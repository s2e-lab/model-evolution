import os
from dotenv import load_dotenv
# load the environment variables (needed for the Discord webhook URL)
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # GITHUB_TOKEN

