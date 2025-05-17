import argparse
import os, sys
import csv
import logging
import json
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import re

class DashboardCapture:
    def __init__(self):
        self.driver = None
        self.csv_file = "dashboard_metadata.csv"
        self._init_csv()
        
    def _init_csv(self):
        """Initialize CSV file with headers if it doesn't exist"""
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'capture_time', 'platform', 'dashboard_name',
                    'datasource', 'time_range', 'url'
                ])

    def _sanitize_filename(self, name: str) -> str:
        """Remove invalid characters from filenames"""
        return re.sub(r'[^\w\-_.]', '_', name)

    def _parse_time_range(self, time_range: str) -> tuple:
        """
        Parse time range input in format:
        Absolute: %Y%m%d-%H:%M:%S_%Y%m%d-%H:%M:%S
        Relative: now-[value][unit] (e.g., now-2h)
        """
        if time_range.startswith('now-'):
            unit_map = {
                's': 'seconds',
                'm': 'minutes',
                'h': 'hours',
                'd': 'days',
                'w': 'weeks'
            }
            match = re.match(r'now-(\d+)(\w+)', time_range)
            if match:
                value, unit = match.groups()
                delta = timedelta(**{unit_map[unit]: int(value)})
                end_time = datetime.now()
                start_time = end_time - delta
                return start_time, end_time
            raise ValueError("Invalid relative time format")
        else:
            try:
                start_str, end_str = time_range.split('_')
                start_time = datetime.strptime(start_str, "%Y%m%d-%H:%M:%S")
                end_time = datetime.strptime(end_str, "%Y%m%d-%H:%M:%S")
                return start_time, end_time
            except ValueError:
                raise ValueError("Time range must be in format %Y%m%d-%H:%M:%S_%Y%m%d-%H:%M:%S")

    def _generate_filename(self, platform: str, dashboard: str, datasource: str,
                         start: datetime, end: datetime) -> str:
        """Generate standardized filename"""
        safe_dashboard = self._sanitize_filename(dashboard)
        safe_datasource = self._sanitize_filename(datasource)
        start_str = start.strftime("%Y%m%d-%H%M%S")
        end_str = end.strftime("%Y%m%d-%H%M%S")
        return f"{platform}_{safe_dashboard}_{safe_datasource}_{start_str}_{end_str}.png"

    def _record_metadata(self, platform: str, dashboard: str, datasource: str,
                       time_range: str, url: str):
        """Append metadata to CSV file"""
        with open(self.csv_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().isoformat(),
                platform,
                dashboard,
                datasource,
                time_range,
                url
            ])

    def _setup_driver(self, headless=True):
        """Configure Chrome WebDriver"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        self.driver = webdriver.Chrome(options=chrome_options)

    def capture_grafana(self, args):
        """Capture Grafana dashboards"""
        try:
            self._setup_driver(not args.debug)
            self._grafana_login(args.url, args.username, args.password)
            
            start_time, end_time = self._parse_time_range(args.time_range)
            
            for dashboard in args.dashboards:
                try:
                    url = f"{args.url}/d/{dashboard['uid']}?from={start_time.timestamp()*1000}&to={end_time.timestamp()*1000}"
                    self.driver.get(url)
                    WebDriverWait(self.driver, 30).until(
                        EC.visibility_of_element_located((By.CLASS_NAME, "panel-container")))
                    
                    filename = self._generate_filename(
                        "grafana", dashboard['name'], args.datasource, start_time, end_time
                    )
                    output_path = os.path.join(args.output_dir, filename)
                    self.driver.save_screenshot(output_path)
                    
                    self._record_metadata(
                        "grafana", dashboard['name'], args.datasource,
                        args.time_range, url
                    )
                    logging.info(f"Captured Grafana dashboard: {output_path}")
                    
                except Exception as e:
                    logging.error(f"Failed to capture {dashboard['name']}: {str(e)}")

        finally:
            if self.driver:
                self.driver.quit()

    def capture_dynatrace(self, args):
        """Capture Dynatrace dashboards"""
        try:
            self._setup_driver(not args.debug)
            self._dynatrace_login(args.url, args.token)
            
            start_time, end_time = self._parse_time_range(args.time_range)
            start_ts = int(start_time.timestamp() * 1000)
            end_ts = int(end_time.timestamp() * 1000)
            
            for dashboard in args.dashboards:
                try:
                    url = f"{args.url}/#dashboard;gtf=c_{start_ts}_{end_ts};id={dashboard['id']}"
                    self.driver.get(url)
                    WebDriverWait(self.driver, 45).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, "div.dashboard"))
                    )
                    time.sleep(5)  # Dynatrace needs extra render time
                    
                    filename = self._generate_filename(
                        "dynatrace", dashboard['name'], "dynatrace", start_time, end_time
                    )
                    output_path = os.path.join(args.output_dir, filename)
                    self.driver.save_screenshot(output_path)
                    
                    self._record_metadata(
                        "dynatrace", dashboard['name'], "dynatrace",
                        args.time_range, url
                    )
                    logging.info(f"Captured Dynatrace dashboard: {output_path}")
                    
                except Exception as e:
                    logging.error(f"Failed to capture {dashboard['name']}: {str(e)}")

        finally:
            if self.driver:
                self.driver.quit()

    def capture_splunk(self, args):
        """Capture Splunk dashboards"""
        try:
            self._setup_driver(not args.debug)
            self._splunk_login(args.url, args.username, args.password)
            
            start_time, end_time = self._parse_time_range(args.time_range)
            
            for dashboard in args.dashboards:
                try:
                    url = f"{args.url}/app/{args.app}/?earliest={start_time.timestamp()}&latest={end_time.timestamp()}"
                    self.driver.get(url)
                    WebDriverWait(self.driver, 30).until(
                        EC.visibility_of_element_located((By.CSS_SELECTOR, "div.dashboard-view")))
                    
                    filename = self._generate_filename(
                        "splunk", dashboard['name'], "splunk", start_time, end_time
                    )
                    output_path = os.path.join(args.output_dir, filename)
                    self.driver.save_screenshot(output_path)
                    
                    self._record_metadata(
                        "splunk", dashboard['name'], "splunk",
                        args.time_range, url
                    )
                    logging.info(f"Captured Splunk dashboard: {output_path}")
                    
                except Exception as e:
                    logging.error(f"Failed to capture {dashboard['name']}: {str(e)}")

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
    capture = DashboardCapture()
    parser = argparse.ArgumentParser(description="Multi-platform Dashboard Capture Tool")
    
    # Common arguments
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument("-d", "--dashboards", nargs="+",
                             help='JSON list of dashboard dicts (name and id/uid)')
    parent_parser.add_argument("-t", "--time-range", required=True,
                             help="Time range (absolute: %Y%m%d-%H:%M:%S_%Y%m%d-%H:%M:%S or relative: now-[value][unit])")
    parent_parser.add_argument("-o", "--output-dir", default="./output",
                             help="Output directory")
    parent_parser.add_argument("--debug", action="store_true",
                             help="Enable browser GUI for debugging")

    # Platform subparsers
    subparsers = parser.add_subparsers(dest="platform", required=True)

    # Grafana parser
    grafana_parser = subparsers.add_parser("grafana", parents=[parent_parser])
    grafana_parser.add_argument("-u", "--url", required=True, help="Grafana base URL")
    grafana_parser.add_argument("--username", default="admin", help="Grafana username")
    grafana_parser.add_argument("--password", required=True, help="Grafana password")
    grafana_parser.add_argument("--datasource", help="Grafana datasource name")

    # Dynatrace parser
    dt_parser = subparsers.add_parser("dynatrace", parents=[parent_parser])
    dt_parser.add_argument("-u", "--url", required=True, help="Dynatrace environment URL")
    dt_parser.add_argument("--token", required=True, help="Dynatrace API token")

    # Splunk parser
    splunk_parser = subparsers.add_parser("splunk", parents=[parent_parser])
    splunk_parser.add_argument("-u", "--url", required=True, help="Splunk base URL")
    splunk_parser.add_argument("-a", "--app", required=True, help="Splunk app name")
    splunk_parser.add_argument("--username", required=True, help="Splunk username")
    splunk_parser.add_argument("--password", required=True, help="Splunk password")

    args = parser.parse_args()

    try:
        os.makedirs(args.output_dir, exist_ok=True)
        
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