from selenium import webdriver
from bs4 import BeautifulSoup
import time

# Initialize the WebDriver (replace with your WebDriver path)
driver = webdriver.Firefox()#Chrome(executable_path='path/to/chromedriver')
url = 'https://huggingface.co/SFconvertbot/activity/community'

# Open the page
driver.get(url)

# Continuously click "Load more" until all content is loaded
while True:
    try:
        # Find the "Load more" button and click it
        load_more_button = driver.find_element_by_xpath('//button[contains(text(), "Load more")]')
        load_more_button.click()
        time.sleep(2)  # Wait for the content to load
    except Exception:
        # Break the loop if "Load more" button is not found (likely no more content)
        break

# After loading all activities, parse the HTML with BeautifulSoup
soup = BeautifulSoup(driver.page_source, 'html.parser')
activities = soup.find_all('div', class_='activity-entry')

# Extract details of each activity
for activity in activities:
    timestamp = activity.find('time')['datetime']
    description = activity.find('div', class_='activity-description').text.strip()
    link = activity.find('a', class_='activity-link')['href']
    print(f'Time: {timestamp}\nDescription: {description}\nLink: {link}\n')

# Close the WebDriver
driver.quit()
