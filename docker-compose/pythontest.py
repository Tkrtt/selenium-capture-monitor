import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from datetime import datetime

# Configure logging

try:
    # Initialize the WebDriver
    driver = webdriver.Chrome()

    # Navigate to Grafana login page
    driver.get("Your-Grafana-Login-url")

    # Find username/email input field and enter your username/email
    username_field = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "user")))
    username_field.send_keys("admin")

    # Find password input field and enter your password
    password_field = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "password")))
    password_field.send_keys("admin")

    # Find the login button and click it
    login_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']")))
    login_button.click()

    # Wait for the login process to complete and handle any post-login prompts
    skip_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, "btn.btn-link")))
    skip_button.click()

    # Navigate to the specific Grafana dashboard
    driver.get("Your-Grafana-Dashboard-Url")
    time.sleep(5)

    # Prompt the user to enter 'from' and 'to' dates
    from_date_str = input("Enter 'from' date (YYYY-MM-DD): ")
    to_date_str = input("Enter 'to' date (YYYY-MM-DD): ")

    # Append default time of '00:00:00' (midnight) to the input date
    from_date_str += " 00:00:00"
    to_date_str += " 00:00:00"

    # Convert user input strings to datetime objects
    from_date_obj = datetime.strptime(from_date_str, "%Y-%m-%d %H:%M:%S")
    to_date_obj = datetime.strptime(to_date_str, "%Y-%m-%d %H:%M:%S")

    # Convert datetime objects to milliseconds since epoch
    from_date_ms = int(from_date_obj.timestamp() * 1000)
    to_date_ms = int(to_date_obj.timestamp() * 1000)

    # Construct the Grafana URL with converted dates
    grafana_url = f"your-Grafana-URL-with-converted-dates{from_date_ms}&to={to_date_ms}"

    # Navigate to Grafana URL
    driver.get(grafana_url)

    # Wait for the page to load and take a screenshot
    time.sleep(10)
    driver.save_screenshot('screenshot.png')

except Exception as e:
    # Log any exceptions
    logging.error(f"An error occurred: {str(e)}")

finally:
    # Close the browser in the finally block to ensure it always closes
    if 'driver' in locals():
        driver.quit()
        logging.info("WebDriver closed successfully")