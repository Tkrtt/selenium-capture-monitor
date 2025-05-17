import time
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logging.basicConfig(filename='automation.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Function to capture webpage screenshot
def capture_grafana(args):
#def capture_grafana(url, output_dir, timezone="Asia%2FHo_Chi_Minh", time_range="now-6h now", dashboard_uid=None, datasource=None, username=None, password=None):
    print(f"Running Grafana screen capture with parameters:")
    print(f"URL: {args.url}")
    print(f"Dashboard ID: {args.dashboard_id}")
    print(f"Time Range: {args.time_range}")
    print(f"Timezone: {args.timezone}")
    print(f"Output Directory: {args.output_dir}")
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

def main():
    parser = argparse.ArgumentParser(description='Screen capture tool for different platforms')
    
    # Create subparsers for each platform
    subparsers = parser.add_subparsers(dest='platform', required=True, help='Platform to capture')
    
    # Grafana subparser
    grafana_parser = subparsers.add_parser('grafana', help='Grafana screen capture')
    grafana_parser.add_argument('-u', '--url', required=True, help='Grafana base URL')
    grafana_parser.add_argument('-d', '--dashboard-id', required=True, help='Dashboard ID')
    grafana_parser.add_argument('-t', '--time-range', default='last1h', 
                               help='Time range (e.g., last1h, today)')
    grafana_parser.add_argument('-z', '--timezone', default='UTC', 
                               help='Timezone (e.g., UTC, America/New_York)')
    grafana_parser.add_argument('-o', '--output-dir', default='./output', 
                               help='Output directory for captures')
    grafana_parser.set_defaults(func=capture_grafana)
    
    # Dynatrace subparser
    dynatrace_parser = subparsers.add_parser('dynatrace', help='Dynatrace screen capture')
    dynatrace_parser.add_argument('-u', '--url', required=True, help='Dynatrace base URL')
    dynatrace_parser.add_argument('-e', '--environment', required=True, 
                                 help='Environment ID')
    dynatrace_parser.add_argument('-d', '--dashboard-id', required=True, 
                                 help='Dashboard ID')
    dynatrace_parser.add_argument('-m', '--management-zone', default='all', 
                                 help='Management zone filter')
    dynatrace_parser.add_argument('-t', '--time-range', default='last1h', 
                                 help='Time range (e.g., last1h, today)')
    dynatrace_parser.add_argument('-o', '--output-dir', default='./output', 
                                 help='Output directory for captures')
    dynatrace_parser.set_defaults(func=capture_dynatrace)
    
    # Splunk subparser (example - customize as needed)
    splunk_parser = subparsers.add_parser('splunk', help='Splunk screen capture')
    splunk_parser.add_argument('-u', '--url', required=True, help='Splunk base URL')
    splunk_parser.add_argument('-a', '--app', required=True, help='Splunk app')
    splunk_parser.add_argument('-d', '--dashboard', required=True, help='Dashboard name')
    splunk_parser.add_argument('-t', '--time-range', default='last1h', 
                              help='Time range (e.g., last1h, today)')
    splunk_parser.add_argument('-o', '--output-dir', default='./output', 
                              help='Output directory for captures')
    splunk_parser.set_defaults(func=lambda args: print("Splunk capture would run here"))
    
    args = parser.parse_args()
    args.func(args)


# Sane default
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

