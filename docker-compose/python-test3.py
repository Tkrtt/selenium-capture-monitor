import argparse
import logging
import os
import sys
import csv
import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from urllib.parse import urlparse
from typing import Tuple, List

class MonitoringCapture:
    def __init__(self):
        self.driver = None
        self.csv_file = "dashboard_links.csv"
        self._init_csv()

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

    def _get_safe_filename(self, dashboard: str, datasource: str, time_range: str) -> str:
        """Generate standardized filename"""
        # Clean strings for filename use
        clean_dashboard = "".join(c if c.isalnum() else "_" for c in dashboard)
        clean_datasource = "".join(c if c.isalnum() else "_" for c in datasource)
        
        # Parse time range into start/end
        start, end = self._parse_time_range(time_range)
        start_str = start.strftime("%Y%m%d-%H%M%S")
        end_str = end.strftime("%Y%m%d-%H%M%S")
        
        return f"{clean_dashboard}_{clean_datasource}_{start_str}_{end_str}.png"

    def _parse_time_range(self, time_range: str) -> Tuple[datetime, datetime]:
        """Parse time range string into start/end datetimes"""
        now = datetime.now()
        
        if time_range.startswith("now-"):
            parts = time_range.split()
            duration = parts[0][4:]  # Remove "now-"
            
            # Parse duration (e.g., "2h" -> 2 hours)
            unit = duration[-1]
            value = int(duration[:-1])
            
            time_units = {
                's': 'seconds',
                'm': 'minutes',
                'h': 'hours',
                'd': 'days',
                'w': 'weeks'
            }
            
            delta = timedelta(**{time_units[unit]: value})
            start_time = now - delta
            end_time = now if len(parts) == 1 else now  # Default to now
            
            return start_time, end_time

        # Handle absolute time ranges
        if " to " in time_range:
            start_str, end_str = time_range.split(" to ")
            start_time = datetime.strptime(start_str, "%Y-%m-%dT%H:%M:%S")
            end_time = datetime.strptime(end_str, "%Y-%m-%dT%H:%M:%S")
            return (
                int(start_time.timestamp() * 1000),
                int(end_time.timestamp() * 1000)
            )
        
        raise ValueError(f"Unsupported time range format: {time_range}")

    def _setup_driver(self, headless=True):
        """Configure Selenium WebDriver"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        self.driver = webdriver.Chrome(options=chrome_options)

    def capture_grafana(self, args):
        """Capture Grafana dashboards with Selenium"""
        try:
            self._setup_driver(not args.debug)
            self._grafana_login(args.url, args.username, args.password)
            
            for dashboard in args.dashboards:
                try:
                    # Construct URL with time range
                    start, end = self._parse_time_range(args.time_range)
                    start_ms = int(start.timestamp() * 1000)
                    end_ms = int(end.timestamp() * 1000)
                    
                    dashboard_url = (
                        f"{args.url}/d/{dashboard}"
                        f"?from={start_ms}&to={end_ms}"
                        f"&var-datasource={args.datasource}"
                    )
                    
                    # Generate filename
                    filename = self._get_safe_filename(
                        dashboard, args.datasource, args.time_range
                    )
                    output_path = os.path.join(args.output_dir, f"grafana_{filename}")
                    
                    # Capture screenshot
                    self.driver.get(dashboard_url)
                    WebDriverWait(self.driver, 30).until(
                        EC.visibility_of_element_located((By.CLASS_NAME, "panel-container"))
                    )
                    time.sleep(2)  # Allow for rendering
                    self.driver.save_screenshot(output_path)
                    
                    # Record metadata
                    self._append_to_csv({
                        'platform': 'grafana',
                        'dashboard_name': dashboard,
                        'datasource': args.datasource,
                        'time_range': args.time_range,
                        'url': dashboard_url
                    })
                    
                    logging.info(f"Saved Grafana screenshot: {output_path}")
                    
                except Exception as e:
                    logging.error(f"Failed to capture {dashboard}: {str(e)}")
                    continue

        finally:
            if self.driver:
                self.driver.quit()

    def capture_dynatrace(self, args):
        """Capture Dynatrace dashboards as screenshots"""
        try:
            self._setup_driver(not args.debug)
            self._dynatrace_login(args.url, args.token)
            
            for dashboard in args.dashboards:
                try:
                    # Construct Dynatrace URL
                    dashboard_url = (
                        f"{args.url}/#dashboard;id={dashboard};"
                        f"gtf={args.time_range}"
                    )
                    
                    # Generate filename
                    filename = self._get_safe_filename(
                        dashboard, "dynatrace", args.time_range
                    )
                    output_path = os.path.join(args.output_dir, f"dynatrace_{filename}")
                    
                    # Capture screenshot
                    self.driver.get(dashboard_url)
                    WebDriverWait(self.driver, 45).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, ".dashboard"))
                    )
                    time.sleep(5)  # Dynatrace needs more time to render
                    self.driver.save_screenshot(output_path)
                    
                    # Record metadata
                    self._append_to_csv({
                        'platform': 'dynatrace',
                        'dashboard_name': dashboard,
                        'datasource': "dynatrace",
                        'time_range': args.time_range,
                        'url': dashboard_url
                    })
                    
                    logging.info(f"Saved Dynatrace screenshot: {output_path}")
                    
                except Exception as e:
                    logging.error(f"Failed to capture {dashboard}: {str(e)}")
                    continue

        finally:
            if self.driver:
                self.driver.quit()

    def capture_splunk(self, args):
        """Capture Splunk dashboards as screenshots"""
        try:
            self._setup_driver(not args.debug)
            self._splunk_login(args.url, args.username, args.password)
            
            for dashboard in args.dashboards:
                try:
                    # Construct Splunk URL
                    dashboard_url = (
                        f"{args.url}/app/{args.app}/"
                        f"?earliest={args.time_range.split()[0]}"
                        f"&latest={args.time_range.split()[1]}" 
                        f"&q=search%20{dashboard}"
                    )
                    
                    # Generate filename
                    filename = self._get_safe_filename(
                        dashboard, "splunk", args.time_range
                    )
                    output_path = os.path.join(args.output_dir, f"splunk_{filename}")
                    
                    # Capture screenshot
                    self.driver.get(dashboard_url)
                    WebDriverWait(self.driver, 30).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, ".dashboard"))
                    )
                    time.sleep(3)  # Allow for rendering
                    self.driver.save_screenshot(output_path)
                    
                    # Record metadata
                    self._append_to_csv({
                        'platform': 'splunk',
                        'dashboard_name': dashboard,
                        'datasource': "splunk",
                        'time_range': args.time_range,
                        'url': dashboard_url
                    })
                    
                    logging.info(f"Saved Splunk screenshot: {output_path}")
                    
                except Exception as e:
                    logging.error(f"Failed to capture {dashboard}: {str(e)}")
                    continue

        finally:
            if self.driver:
                self.driver.quit()

    def _grafana_login(self, url: str, username: str, password: str):
        """Login to Grafana"""
        login_url = f"{url.split('/d/')[0]}/login"
        self.driver.get(login_url)
        try: 
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.NAME, "user"))
            )
            self.driver.find_element(By.NAME, "user").send_keys(username)
            self.driver.find_element(By.NAME, "password").send_keys(password)
            self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        except Exception as e:
            logging.error(f"Grafana login failed: {str(e)}")
            raise

        # WebDriverWait(self.driver, 15).until(
        #     EC.presence_of_element_located((By.CSS_SELECTOR, ".navbar-page-btn")))

    def _dynatrace_login(self, url: str, token: str):
        """Login to Dynatrace using API token"""
        login_url = f"{url}/#login;token={token}"
        self.driver.get(login_url)
        WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".dashboard")))

    def _splunk_login(self, url: str, username: str, password: str):
        """Login to Splunk"""
        login_url = f"{url}/account/login?return_to=/en-US/"
        self.driver.get(login_url)
        
        WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located((By.ID, "username")))
        self.driver.find_element(By.ID, "username").send_keys(username)
        self.driver.find_element(By.ID, "password").send_keys(password)
        self.driver.find_element(By.ID, "loginButton").click()
        
        WebDriverWait(self.driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".dashboard")))

def main():
    capture = MonitoringCapture()
    parser = argparse.ArgumentParser(description="Multi-platform Dashboard Capture Tool")
    
    # Common arguments
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument("-d", "--dashboards", nargs="+", required=True,
                             help="Dashboard IDs/names to capture")
    parent_parser.add_argument("-t", "--time-range", default="now-1h",
                             help="Time range (e.g., 'now-2h', 'now-7d now')")
    parent_parser.add_argument("-o", "--output-dir", default="./output",
                             help="Output directory")
    parent_parser.add_argument("--debug", action="store_true",
                             help="Enable browser GUI for debugging")

    # Platform subparsers
    subparsers = parser.add_subparsers(dest="platform", required=True)

    # Grafana
    grafana_parser = subparsers.add_parser("grafana", parents=[parent_parser])
    grafana_parser.add_argument("-u", "--url", required=True, help="Grafana base URL")
    grafana_parser.add_argument("--username", default="admin", help="Grafana username")
    grafana_parser.add_argument("--password", required=True, help="Grafana password")
    grafana_parser.add_argument("--datasource", help="Grafana datasource name")

    # Dynatrace
    dt_parser = subparsers.add_parser("dynatrace", parents=[parent_parser])
    dt_parser.add_argument("-u", "--url", required=True,
                         help="Dynatrace environment URL")
    dt_parser.add_argument("-k", "--token", required=True,
                         help="Dynatrace API token")

    # Splunk
    splunk_parser = subparsers.add_parser("splunk", parents=[parent_parser])
    splunk_parser.add_argument("-u", "--url", required=True, help="Splunk base URL")
    splunk_parser.add_argument("-a", "--app", required=True, help="Splunk app name")
    splunk_parser.add_argument("--username", required=True, help="Splunk username")
    splunk_parser.add_argument("--password", required=True, help="Splunk password")

    args = parser.parse_args()

    try:
        # Create output directory
        os.makedirs(args.output_dir, exist_ok=True)
        
        # Dispatch to appropriate capture method
        if args.platform == "grafana":
            capture.capture_grafana(args)
        elif args.platform == "dynatrace":
            capture.capture_dynatrace(args)
        elif args.platform == "splunk":
            capture.capture_splunk(args)
            
        logging.info("Capture process completed successfully")
        sys.exit(0)
        
    except Exception as e:
        logging.error(f"Capture failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()