import requests
from bs4 import BeautifulSoup
import pandas as pd

# URL of the website to scrape
url = "https://caoe.asu.edu/projects/?show_all=true"

# Headers to mimic a browser request
headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/87.0.4280.88 Safari/537.36"
    )
}

# Send a GET request with headers
response = requests.get(url, headers=headers)
response.raise_for_status()  # Check if the request was successful

# Parse the HTML content with BeautifulSoup
soup = BeautifulSoup(response.text, "html.parser")

# Find all project elements
projects = soup.find_all("div", class_="card")

# List to store extracted project data
data = []

# Loop through each project element and extract metadata
for project in projects:
    project_data = {}

    # Extract project title
    title_tag = project.find("h3")
    project_data['title'] = title_tag.get_text(strip=True) if title_tag else "N/A"

    # Extract project description
    description_tag = project.find("div", class_="card-body")
    project_data['description'] = description_tag.get_text(strip=True) if description_tag else "N/A"

    # get project URL from div.card-button
    project_url = project.find("a", class_="btn btn-maroon")
    project_data['url'] = project_url['href'] if project_url else "N/A"

    # Extract additional metadata if available, e.g., Principal Investigator
    tags = project.find("div", class_="card-tags")
    if tags:
        # get children nodes of tags
        tags_children = tags.children

        project_data['tags'] = ";".join([ tag.get_text(strip=True) for tag in tags_children if tag.get_text(strip=True) != "" ])

    # Append the project data to the list
    data.append(project_data)

# Convert the data to a pandas DataFrame for easier manipulation and display
df = pd.DataFrame(data)

# Display or save the DataFrame to a CSV
print(df)
df.to_csv("projects_metadata.csv", index=False)
