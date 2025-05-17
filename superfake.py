import argparse
import csv
import os
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urlparse
import logging
from typing import Tuple, Dict

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("capture.log"), logging.StreamHandler()]
)

class CaptureApp:
    def __init__(self):
        self.driver = None
        self.csv_columns = [
            'platform', 'dashboard_name', 'dashboard_id', 'datasource',
            'start_date', 'end_date', 'capture_time', 'file_path', 'url'
        ]

    def _init_webdriver(self, headless=True):
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        self.driver = webdriver.Chrome(options=options)

    def _save_metadata(self, args: Dict, start_date: datetime, end_date: datetime, file_path: str):
        """Save dashboard metadata to CSV with append mode"""
        csv_path = os.path.join(args['output_dir'], 'capture_history.csv')
        file_exists = os.path.exists(csv_path)
        
        with open(csv_path, 'a', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.csv_columns)
            if not file_exists:
                writer.writeheader()
            
            writer.writerow({
                'platform': args['platform'],
                'dashboard_name': args['dashboard_name'],
                'dashboard_id': args['dashboard_id'],
                'datasource': args.get('datasource', 'N/A'),
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'capture_time': datetime.now().isoformat(),
                'file_path': file_path,
                'url': args['url']
            })

    def _construct_filename(self, args: Dict, start_date: datetime, end_date: datetime) -> str:
        """Generate filename based on requirements"""
        safe_name = args['dashboard_name'].replace(' ', '_').replace('/', '-')
        ds_name = args.get('datasource', 'unknown').replace(' ', '_')
        start_str = start_date.strftime('%Y%m%dT%H%M%S')
        end_str = end_date.strftime('%Y%m%dT%H%M%S')
        
        return f"{safe_name}_{args['dashboard_id']}_{ds_name}_{start_str}_{end_str}.png"

    def capture_grafana(self, base_url: str, dashboard_uid: str, time_range: str, 
                       datasource: str, output_dir: str, credentials: Dict):
        """Capture Grafana dashboard with Selenium"""
        try:
            self._init_webdriver()
            # Login
            self.driver.get(f"{base_url.split('/d/'[0])}/login")
            # login_url = f"{url.split('/d/')[0]}/login"
            WebDriverWait(self.driver, 15).until(EC.presence_of_element_located((By.NAME, "user")))
            self.driver.find_element(By.NAME, "user").send_keys(credentials['username'])
            self.driver.find_element(By.NAME, "password").send_keys(credentials['password'])
            self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            
            # Get dashboard info
            self.driver.get(f"{base_url}/api/dashboards/uid/{dashboard_uid}")
            dashboard_info = json.loads(self.driver.find_element(By.TAG_NAME, 'pre').text)
            dashboard_name = dashboard_info['dashboard']['title']
            
            # Construct URL with time range
            start_date, end_date = self.parse_time_range(time_range)
            url = (f"{base_url}/d/{dashboard_uid}"
                  f"?from={int(start_date.timestamp() * 1000)}"
                  f"&to={int(end_date.timestamp() * 1000)}")
            
            # Capture screenshot
            self.driver.get(url)
            WebDriverWait(self.driver, 30).until(
                EC.visibility_of_element_located((By.CLASS_NAME, "panel-container"))
            )
            # Create directory structure
            save_dir = os.path.join(output_dir, 'grafana', datasource)
            os.makedirs(save_dir, exist_ok=True)
            
            filename = self._construct_filename({
                'platform': 'grafana',
                'dashboard_name': dashboard_name,
                'dashboard_id': dashboard_uid,
                'datasource': datasource,
                'url': url
            }, start_date, end_date)
            
            file_path = os.path.join(save_dir, filename)
            self.driver.save_screenshot(file_path)
            
            # Save metadata
            self._save_metadata({
                'platform': 'grafana',
                'dashboard_name': dashboard_name,
                'dashboard_id': dashboard_uid,
                'datasource': datasource,
                'output_dir': output_dir,
                'url': url
            }, start_date, end_date, file_path)
            
            return file_path
            
        finally:
            if self.driver:
                self.driver.quit()

    def capture_dynatrace(self, base_url: str, dashboard_id: str, time_range: str, 
                         output_dir: str, credentials: Dict):
        """Capture Dynatrace dashboard with Selenium"""
        try:
            self._init_webdriver()
            
            # Login
            self.driver.get(f"{base_url}/login")
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.ID, "email")))
            self.driver.find_element(By.ID, "email").send_keys(credentials['username'])
            self.driver.find_element(By.ID, "password").send_keys(credentials['password'])
            self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            
            # Navigate to dashboard
            start_date, end_date = self.parse_time_range(time_range)
            url = (f"{base_url}/ui/dashboards/{dashboard_id}"
                  f"?gtf=CUSTOM&from={int(start_date.timestamp() * 1000)}"
                  f"&to={int(end_date.timestamp() * 1000)}")
            self.driver.get(url)
            
            # Get dashboard name
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".dashboard-title")))
            dashboard_name = self.driver.find_element(By.CSS_SELECTOR, ".dashboard-title").text
            
            # Capture screenshot
            save_dir = os.path.join(output_dir, 'dynatrace')
            os.makedirs(save_dir, exist_ok=True)
            
            filename = self._construct_filename({
                'platform': 'dynatrace',
                'dashboard_name': dashboard_name,
                'dashboard_id': dashboard_id,
                'url': url
            }, start_date, end_date)
            
            file_path = os.path.join(save_dir, filename)
            self.driver.save_screenshot(file_path)
            
            # Save metadata
            self._save_metadata({
                'platform': 'dynatrace',
                'dashboard_name': dashboard_name,
                'dashboard_id': dashboard_id,
                'output_dir': output_dir,
                'url': url
            }, start_date, end_date, file_path)
            
            return file_path
            
        finally:
            if self.driver:
                self.driver.quit()

    def capture_splunk(self, base_url: str, dashboard_name: str, time_range: str, 
                      output_dir: str, credentials: Dict):
        """Capture Splunk dashboard with Selenium"""
        try:
            self._init_webdriver()
            
            # Login
            self.driver.get(f"{base_url}/en-GB/account/login")
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.ID, "username")))
            self.driver.find_element(By.ID, "username").send_keys(credentials['username'])
            self.driver.find_element(By.ID, "password").send_keys(credentials['password'])
            self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
            
            # Navigate to dashboard
            start_date, end_date = self.parse_time_range(time_range)
            url = (f"{base_url}/en-GB/app/search/dashboard"
                  f"?earliest={start_date.timestamp()}"
                  f"&latest={end_date.timestamp()}"
                  f"&q=search%20dashboard%3D{dashboard_name}")
            self.driver.get(url)
            
            # Wait for dashboard load
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.CLASS_NAME, "dashboard-container")))
            
            # Capture screenshot
            save_dir = os.path.join(output_dir, 'splunk')
            os.makedirs(save_dir, exist_ok=True)
            
            filename = self._construct_filename({
                'platform': 'splunk',
                'dashboard_name': dashboard_name,
                'url': url
            }, start_date, end_date)
            
            file_path = os.path.join(save_dir, filename)
            self.driver.save_screenshot(file_path)
            
            # Save metadata
            self._save_metadata({
                'platform': 'splunk',
                'dashboard_name': dashboard_name,
                'output_dir': output_dir,
                'url': url
            }, start_date, end_date, file_path)
            
            return file_path
            
        finally:
            if self.driver:
                self.driver.quit()

    @staticmethod
    def parse_time_range(time_range: str) -> Tuple[datetime, datetime]:
        """Parse complex time ranges including relative and absolute formats"""
        now = datetime.now()
        
        # Handle relative time ranges
        if time_range.startswith("now"):
            parts = time_range.split()
            duration = parts[0].split("-")
            
            if len(duration) > 1:
                value = int(duration[1][:-1])
                unit = duration[1][-1]
                
                unit_map = {
                    's': 'seconds',
                    'm': 'minutes',
                    'h': 'hours',
                    'd': 'days',
                    'w': 'weeks'
                }
                
                delta = timedelta(**{unit_map[unit]: value})
                start = now - delta
                end = now
            else:
                start = now
                end = now
        else:
            # Handle absolute time ranges
            try:
                if ' to ' in time_range:
                    start_str, end_str = time_range.split(' to ')
                    start = datetime.fromisoformat(start_str)
                    end = datetime.fromisoformat(end_str)
                else:
                    start = datetime.fromisoformat(time_range)
                    end = now
            except ValueError:
                raise ValueError(f"Unsupported time format: {time_range}")

        return start, end

if __name__ == "__main__":
    app = CaptureApp()
    
    parser = argparse.ArgumentParser(description="Multi-platform Dashboard Capture Tool")
    parser.add_argument("-p", "--platform", required=True, 
                      choices=['grafana', 'dynatrace', 'splunk'])
    parser.add_argument("-u", "--url", required=True, help="Base URL of the platform")
    parser.add_argument("-n", "--dashboard-name", required=True, 
                      help="Dashboard name/identifier")
    parser.add_argument("-i", "--dashboard-id", help="Dashboard ID (for Grafana/Dynatrace)")
    parser.add_argument("-d", "--datasource", help="Datasource name (Grafana only)")
    parser.add_argument("-t", "--time-range", default="now-1h", 
                      help="Time range (e.g., 'now-2h', '2023-01-01T00:00:00 to 2023-01-02T00:00:00')")
    parser.add_argument("-o", "--output-dir", default="./captures",
                      help="Output directory for screenshots and metadata")
    parser.add_argument("--username", required=True, help="Login username")
    parser.add_argument("--password", required=True, help="Login password")
    
    args = parser.parse_args()
    
    try:
        if args.platform == 'grafana':
            if not args.dashboard_id or not args.datasource:
                raise ValueError("Grafana requires --dashboard-id and --datasource")
            
            app.capture_grafana(
                base_url=args.url,
                dashboard_uid=args.dashboard_id,
                time_range=args.time_range,
                datasource=args.datasource,
                output_dir=args.output_dir,
                credentials={'username': args.username, 'password': args.password}
            )
            
        elif args.platform == 'dynatrace':
            app.capture_dynatrace(
                base_url=args.url,
                dashboard_id=args.dashboard_id,
                time_range=args.time_range,
                output_dir=args.output_dir,
                credentials={'username': args.username, 'password': args.password}
            )
            
        elif args.platform == 'splunk':
            app.capture_splunk(
                base_url=args.url,
                dashboard_name=args.dashboard_name,
                time_range=args.time_range,
                output_dir=args.output_dir,
                credentials={'username': args.username, 'password': args.password}
            )
            
        logging.info("Capture completed successfully")
        sys.exit(0)
        
    except Exception as e:
        logging.error(f"Capture failed: {str(e)}")
        sys.exit(1)