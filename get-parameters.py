import requests
import sys
from requests.auth import HTTPBasicAuth

# Configuration
GRAFANA_URL = "http://localhost:3000/api/search"
GRAFANA_USER = "admin"
GRAFANA_PASSWORD = "admin"
EXPECTED_TITLES = ["CPU", "Grafana metrics", "Prometheus Stats", "Runner Mode"]

def get_grafana_dashboards():
    try:
        response = requests.get(
            GRAFANA_URL,
            params={"type": "dash-db"},  # Filter only dashboards
            auth=HTTPBasicAuth(GRAFANA_USER, GRAFANA_PASSWORD)
        )
        response.raise_for_status()
        return response.json()
        print(f"Missing dashboards: {', '.join(response)}")
    except requests.exceptions.RequestException as e:
        print(f"Error accessing Grafana API: {str(e)}")
        sys.exit(1)

def verify_dashboards(expected_titles):
    dashboards = get_grafana_dashboards()
    
    # Extract titles from dashboard data
    existing_titles = [db["title"] for db in dashboards if "title" in db]
    
    # Find missing titles
    missing_titles = [title for title in expected_titles if title not in existing_titles]
    
    if missing_titles:
        print(f"Missing dashboards: {', '.join(missing_titles)}")
        sys.exit(1)
    else:
        print("All expected dashboards are present")
        return True

if __name__ == "__main__":
    get_grafana_dashboards()
    # verify_dashboards(EXPECTED_TITLES)