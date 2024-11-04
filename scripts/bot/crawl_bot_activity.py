"""
This script crawls the Hugging Face Community Bot activity page and saves all discussion URLs to a CSV file.
The script uses Selenium to interact with the page and BeautifulSoup to parse the HTML content.
The discussion URLs are saved to a CSV file named discussion_urls.csv in the data directory.
@Author: Joanna C. S. Santos
"""
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


def get_num_contributions():
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'html.parser')
    # find div with class = "SVELTE_HYDRATER contents" and data-target = "UserProfile"
    user_profile = soup.find_all('div', class_='SVELTE_HYDRATER contents',
                                 attrs={'data-target': 'UserProfile'})
    # parse json in the attribute data-props
    user_profile_json = json.loads(user_profile[0].get('data-props'))
    return user_profile_json['communityScore']


def load_more():
    num_activities = get_num_contributions()
    num_pages = math.ceil(num_activities / 20) + 1
    sleep_time = 1.8
    # num_pages = 10
    for i in tqdm(range(num_pages)):
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


def parse_discussions() -> None:
    """
    Parse the page source to find and save new discussion URLs to CSV
    """
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'html.parser')

    # Find and save new discussion URLs to CSV
    with open(output_file, "w", newline="", encoding="utf8") as file:
        writer = csv.writer(file, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(["pr_url"])  # Write header once at the start
        print("Searching for URLs")
        links = soup.find_all('a', href=True)
        for link in tqdm(links):
            href = link['href']
            if '/discussions/' in href:
                full_url = f"https://huggingface.co{href}" if href.startswith("/") else href
                writer.writerow([full_url])


if __name__ == '__main__':
    # Initialize WebDriver
    driver = webdriver.Firefox()
    try:
        # other usernames to test the script
        # username = "julien-c"
        # username = "lsiddiqsunny"
        # username = "Linaqruf"
        username = "SFconvertbot"

        # Open the URL
        url = f"https://huggingface.co/{username}/activity/community"
        driver.get(url)

        # Load as many discussions as possible
        load_more()

        # Get the page source and parse it
        output_file = Path(f"../../data/{username.lower()}_pr_urls.csv")
        parse_discussions()

    finally:
        if driver:
            # Close the browser
            driver.quit()


"""
If the script gets stuck on the last step, we can do a manual workaround. We go to the Firefox instance, and run on the console:
```
const discussionLinks = Array.from(document.querySelectorAll('a'))
    .filter(link => link.href.includes('/discussion'))
    .map(link => link.href);

console.log(discussionLinks);

``` 
Once you see the array of links printed in the console, right-click on the output and select Copy Object.
Then, paste the copied object into a text file and save it as a CSV file.
"""