import csv
import json
import math
import time
from pathlib import Path

from bs4 import BeautifulSoup
from tqdm import tqdm
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.common.by import By
from scripts.bot.bot_utils import extract_discussion_metadata

def click_load_more():
    # how long to wait in between clicks
    sleep_time = 1.8
    # arbitrary number of pages to load (large enough to load all activities)
    for _ in tqdm(range(2 ** 32)):
        try:
            # Locate and click the "Load More" button
            load_more_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Load more')]")
            load_more_button.click()
            # Wait for new content to load
            time.sleep(sleep_time)
        except (NoSuchElementException, ElementClickInterceptedException):
            print("Stopped loading more data")
            # Break if the "Load More" button is not found or cannot be clicked
            break


def find_discussions() -> []:
    """
    Parse the page source to find and save new discussion URLs to CSV
    """
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'html.parser')
    output = []
    # Find and save new discussion URLs to CSV
    print("Searching for URLs")
    links = soup.find_all('a', href=True)
    for link in tqdm(links):
        href = link['href']
        if '/discussions/' in href and not href.endswith("/new"):
            full_url = f"https://huggingface.co{href}" if href.startswith("/") else href
            output.append(full_url)
    return output


if __name__ == '__main__':
    # Initialize WebDriver
    driver = webdriver.Firefox()
    try:
        discussions = []
        for status in ["open", "closed"]:
            url = f"https://huggingface.co/spaces/safetensors/convert/discussions?status={status}&type=discussion"
            # Open the URL
            driver.get(url)
            # Load as many discussions as possible
            click_load_more()
            # Get the page source and parse it
            for url in find_discussions():
                events, header = extract_discussion_metadata(url)
                discussions.append((url, status, events, header))

    finally:
        if driver:
            # Close the browser
            driver.quit()

    output_file = Path(f"../../data/converter_discussions.csv")
    # save the results
    with open(output_file, "w", newline="", encoding="utf8") as file:
        writer = csv.writer(file, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(["discussion_url", "discussion_status","events", "header"])  # Write header once at the start
        for url, status, events, header in discussions:
            writer.writerow([url, status, events, header])



