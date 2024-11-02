import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
from bs4 import BeautifulSoup
import time


# Initialize WebDriver
driver = webdriver.Firefox()

try:
    # Open the URL
    url = "https://huggingface.co/SFconvertbot/activity/community"
    driver.get(url)

    # Open the CSV file in append mode and write header once
    with open("discussion_urls.csv", "a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Discussion URL"])  # Write header once at the start


    # Function to load all discussions by clicking "Load More"
    def load_all_discussions():
        # Set to keep track of URLs to avoid duplicates in case of reloading parts of the page
        seen_links = set()

        while True:
            try:
                # Get the page source and parse it
                page_source = driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')

                # Find and save new discussion URLs to CSV
                with open("discussion_urls.csv", "a", newline="") as file:
                    writer = csv.writer(file)
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        if '/discussions/' in href:
                            full_url = f"https://huggingface.co{href}" if href.startswith("/") else href
                            if full_url not in seen_links:  # Save only if not already saved
                                writer.writerow([full_url])
                                seen_links.add(full_url)  # Track the saved URL

                # Locate and click the "Load More" button
                load_more_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Load more')]")
                load_more_button.click()

                # Wait for new content to load
                time.sleep(2)

            except (NoSuchElementException, ElementClickInterceptedException):
                # Break if the "Load More" button is not found or cannot be clicked
                break


    # Load all discussions and save continuously
    load_all_discussions()
finally:
    # Close the browser
    driver.quit()

print("All discussion URLs have been continuously saved to discussion_urls.csv")
