import time
import logging
from datetime import datetime
from selenium import webdriver  
# from pyvirtualdisplay import Display
# from PIL import Image
from selenium.webdriver.common.by import By  
from selenium.webdriver.support.ui import WebDriverWait  
from selenium.webdriver.support import expected_conditions as EC  

logging.basicConfig(filename='automation.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Function to login
# def login_to_grafana(driver, url, username=None, password=None):
# def login_to_grafana(driver, url, username=None, password=None):


# Function to capture webpage screenshot  
def capture_grafana(url, output_dir, timezone="Asia%2FHo_Chi_Minh", time_range="now-6h now", dashboard_uid=None, datasource=None, username=None, password=None):
    # WebDriver options
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=2560,1440")
    driver = webdriver.Chrome(options=options)
    try:
        # Login first
        login_url = f"{url.split('/d/')[0]}/login"
        # Get login URL
        driver.get(login_url)
        # Wait 10s or until username/password prompt up
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "user"))
        )
        # Find element and login to grafana
        driver.find_element(By.NAME, "user").send_keys(username)
        driver.find_element(By.NAME, "password").send_keys(password)
        driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        # Sleep in order not to broke stream
        time.sleep(1)
        for dashboard_uid in dashboard_uid.split(','):
            base_url = url.split('/d/')[0]
            from_time, to_time = time_range.split()
            #dashboard_url = f"{base_url}/d/{dashboard_uid}?from={from_time}&to={to_time}&timezone={timezone}&var-datasource={datasource}"
            dashboard_url = f"{base_url}/d/{dashboard_uid}?from={from_time}&to={to_time}&timezone={timezone}"
            driver.get(dashboard_url)
            print(f"{dashboard_url}")
            # driver.set_window_size(2560, 1440)
            time.sleep(1)
            driver.save_screenshot(f"{output_dir}/{dashboard_uid}.png")
            print(f"Screenshot saved to {output_dir}/{dashboard_uid}.png")
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
    finally:
        if 'driver' in locals():
            driver.quit()
            logging.info("WebDriver closed successfully")
# Test run
if __name__ == "__main__":
    datasource = "prometheus"
    url="http://localhost:3000"
    output_dir="/home/solaris/test"
    time_range="now-6h now"
    dashboard_uid="UDdpyzz7z,rpfmFFz7z,1bde194d-fc4a-4010-91b3-cfead4fbab89"
    username="admin"
    password="admin"
    capture_grafana(
        url=url,
        output_dir=output_dir,
        time_range=time_range,
        dashboard_uid=dashboard_uid,
        datasource=datasource,
        username=username,
        password=password,
    )

