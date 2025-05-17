import argparse
import os
import sys
import time
import logging
import requests
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from requests.auth import HTTPBasicAuth
from urllib.parse import urlparse
from typing import Tuple

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("capture.log"), logging.StreamHandler()]
)

class CaptureApp:
    # Init Nothing
    def __init__(self):
        self.driver = None
        self.csv_file = "dashboard_links.csv"
        self._init_csv()
    # CSV
    def _init_csv(self):
        """Initialize CSV file with headers if it doesn't exist"""
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp', 'platform', 'dashboard_name', 
                    'datasource', 'time_range', 'url'
                ])

    def _append_to_csv(self, record: dict):
        """Append a new record to the CSV file"""
        with open(self.csv_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().isoformat(),
                record['platform'],
                record['dashboard_name'],
                record['datasource'],
                record['time_range'],
                record['url']
            ])

    # Init Chrome Driver
    def configure_driver(self, headless=True):
        options = webdriver.ChromeOptions()
        # options.add_argument("--headless=new") # Headless
        options.add_argument("--start-maximized")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=2560,1440") # 2K
        self.driver = webdriver.Chrome(options=options)

    # Find Dashboard Name by UID
    def find_dashboard_by_uid(self, grafana_url: str, grafana_username: str, grafana_password: str):
        try:
            grafana_api_url= "{grafana_url}" + "/api/search"
            print(f"Dashboard Title for UID '{grafana_api_url}'")
            response = requests.get(
                {grafana_api_url},
                params={"type": "dash-db"},
                auth=HTTPBasicAuth({args.grafana_username}, {args.grafana_password})
            )
            response.raise_for_status()
            dashboards = response.json()
            
            for dashboard in dashboards:
                if dashboard.get("args.grafana_dashboard_uid") == uid:
                    return dashboard.get("title")
            return None
            print(f"Dashboard Title for UID '{TARGET_UID}': {title}")
            sys.exit(0)
        except requests.exceptions.RequestException as e:
            print(f"Error accessing Grafana API for scraping: {str(e)}")

    # Capture Grafana
    def capture_grafana(self, args):
        """Capture Grafana dashboards with Selenium"""
        try:
            self.configure_driver(headless=not args.debug)
            #### LOGIN GRAFANA
            grafana_login_url = f"{args.grafana_url.split('/d/')[0]}/login"
            self.driver.get(grafana_login_url)
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.NAME, "user")))
                self.driver.find_element(By.NAME, "user").send_keys(args.grafana_username)
                self.driver.find_element(By.NAME, "password").send_keys(args.grafana_password)
                self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            except Exception as e:
                logging.error(f"Grafana login failed: {str(e)}")
                raise
            #### CAPTURE GRAFANA DASHBOARDS
            for dashboard in args.grafana_dashboards_uid:
                start_time, end_time = self.parse_time_range(args.grafana_time_range)
                dashboard_url = (
                    f"{args.grafana_url}/d/{dashboard}" # Dashboard
                    f"?from={start_time}&to={end_time}" # Date
                    # f"&timezone={args.timezone}" # Timezone
                )
                logging.info(f"Capturing {dashboard} at {dashboard_url}")
                self.driver.get(dashboard_url)
                self.find_dashboard_by_uid(args.grafana_url, args.grafana_username, args.grafana_password)
            ### GET DASHBOARD NAME
                # try:
                #     response = requests.get(
                #         args.grafana_url,
                #         params={"type": "dash-db"},
                #         auth=HTTPBasicAuth(args.grafana_username, args.grafana_password)
                #     )
                #     response.raise_for_status()
                #     dashboards = response.json()
                    
                #     for dashboard2 in dashboards:
                #         if dashboard2.get("uid") == uid:
                #             return dashboard2.get("title")
                #     return None
                    
                # except requests.exceptions.RequestException as e:
                #     print(f"Error accessing Grafana API: {str(e)}")
                #     sys.exit(1)
                try:
                    time.sleep(2)  # Allow final rendering
                    output_path = os.path.join(args.grafana_output_dir, f"grafana_{dashboard}_{start_time}_{end_time}.png")
                    os.makedirs(args.grafana_output_dir, exist_ok=True)
                    self.driver.save_screenshot(output_path)
                    logging.info(f"Saved Grafana screenshot: {output_path}")
                    
                except Exception as e:
                    logging.error(f"Failed to capture {dashboard}: {str(e)}")
                    continue

        finally:
            if self.driver:
                self.driver.quit() # Exit browser
    # Time Range Handling
    @staticmethod
    def parse_time_range(time_range: str) -> Tuple[int, int]:
        """Parse various time range formats to epoch milliseconds"""
        now = datetime.now()
        
        if time_range.lower() == "now":
            return int(now.timestamp() * 1000), int(now.timestamp() * 1000)
        try:
            # Handle relative time ranges
            if time_range.startswith("now-"):
                parts = time_range.split()
                duration = parts[0].split("-")[1]
                unit = duration[-1]
                value = int(duration[:-1])
                # Time units
                time_units = {
                    's': 'seconds',
                    'm': 'minutes',
                    'h': 'hours',
                    'd': 'days',
                    'w': 'weeks'
                }
                # 
                delta = timedelta(**{time_units[unit]: value})
                start_time = now - delta
                end_time = now if len(parts) == 1 else datetime.strptime(parts[1], "%Y:%m:%d-%H:%M:%S")
                # Return time as Unix epoch
                return (
                    int(start_time.timestamp() * 1000),
                    int(end_time.timestamp() * 1000)
                )
            # Handle absolute time ranges
            if " to " in time_range:
                start_str, end_str = time_range.split(" to ")
                start_time = datetime.strptime(start_str, "%Y:%m:%d-%H:%M:%S")
                end_time = datetime.strptime(end_str, "%Y:%m:%d-%H:%M:%S")
                # Return time as Unix epoch
                return (
                    int(start_time.timestamp() * 1000),
                    int(end_time.timestamp() * 1000)
                )
        except Exception as e:
            logging.error(f"Invalid time format: {time_range}")
            raise ValueError(f"Unsupported time range format: {time_range}") from e
        return 0, 0

def main():
    app = CaptureApp()
    parser = argparse.ArgumentParser(description="Monitoring Capture Tool")
    
    # Common arguments
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument("--debug", action="store_true",
                              help="Debug mode")

    # Platform subparsers
    subparsers = parser.add_subparsers(dest="platform", required=True)

    # Grafana
    grafana_parser = subparsers.add_parser("grafana", parents=[parent_parser])
    grafana_parser.add_argument("--grafana-url", required=True, help="Grafana base URL")
    grafana_parser.add_argument("--grafana-username", required=True, help="Grafana username")
    grafana_parser.add_argument("--grafana-password", required=True, help="Grafana password")
    # grafana_parser.add_argument("-z", "--timezone", default="Asia", help="Timezone (e.g., UTC, America/New_York)")
    grafana_parser.add_argument("--grafana-time-range", default="now-1h", help="Time range (e.g., 'now-2h now', 'today')")
    grafana_parser.add_argument("--grafana-dashboards-uid", nargs="+", required=True, help="Dashboard UIDs to capture")
    grafana_parser.add_argument("--grafana-output-dir", default="./grafana", help="Output directory")

    # Dynatrace
    dynatrace_parser = subparsers.add_parser("dynatrace", parents=[parent_parser])
    dynatrace_parser.add_argument("--dynatrace-url", required=True, help="Dynatrace environment URL")
    dynatrace_parser.add_argument("--dynatrace-username", required=True, help="Dynatrace API token")
    dynatrace_parser.add_argument("--dynatrace-management-zone", default="all", help="Management zone filter")
    dynatrace_parser.add_argument("--dynatrace-time-range", default="now-1h", help="Time range (e.g., 'now-2h now', 'today')")
    dynatrace_parser.add_argument("--dynatrace-output-dir", default="./dynatrace", help="Output directory")

    # Splunk
    splunk_parser = subparsers.add_parser("splunk", parents=[parent_parser])
    splunk_parser.add_argument("--splunk-url", required=True, help="Splunk base URL")
    splunk_parser.add_argument("--splunk-username", required=True, help="Splunk username")
    splunk_parser.add_argument("--splunk-password", required=True, help="Splunk password")
    splunk_parser.add_argument("--splunk-app", required=True, help="Splunk app")
    splunk_parser.add_argument("--splunk-time-range", default="now-1h", help="Time range (e.g., 'now-2h now', 'today')")

    args = parser.parse_args()

    try:
        # Dispatch to appropriate capture method
        if args.platform == "grafana":
            app.capture_grafana(args)
        elif args.platform == "dynatrace":
            app.capture_dynatrace(args)
        elif args.platform == "splunk":
            app.capture_splunk(args)
            
        logging.info("Capture process completed")
        sys.exit(0)

    except Exception as e:
        logging.error(f"Capture failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()