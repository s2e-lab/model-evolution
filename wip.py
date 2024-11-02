from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
from bs4 import BeautifulSoup
import time

# Initialize WebDriver
driver = webdriver.Firefox()

# Open the URL
url = "https://huggingface.co/SFconvertbot/activity/community"
driver.get(url)

# Function to load all discussions by clicking "Load More"
def load_all_discussions():
    while True:
        try:
            # Locate and click the "Load More" button
            load_more_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Load more')]")
            load_more_button.click()
            # Wait for content to load
            time.sleep(2)
        except (NoSuchElementException, ElementClickInterceptedException):
            # Break if the "Load More" button is not found or cannot be clicked
            break

# Load all discussions
load_all_discussions()

# Get page source and parse with BeautifulSoup
page_source = driver.page_source
soup = BeautifulSoup(page_source, 'html.parser')

# Find all discussion URLs
discussion_links = []
for link in soup.find_all('a', href=True):
    href = link['href']
    if '/discussions/' in href:
        # Complete the URL if it's a relative path
        full_url = f"https://huggingface.co{href}" if href.startswith("/") else href
        discussion_links.append(full_url)

# Print all discussion URLs
for link in discussion_links:
    print(link)

# Close the browser
driver.quit()
