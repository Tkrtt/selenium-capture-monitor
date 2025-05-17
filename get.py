import requests
import sys
from requests.auth import HTTPBasicAuth

# Configuration
GRAFANA_URL = "http://localhost:3000/api/search"
GRAFANA_USER = "admin"
GRAFANA_PASSWORD = "admin"
TARGET_UID = "1bde194d-fc4a-4010-91b3-cfead4fbab89"  # Replace with your UID

def find_dashboard_by_uid(uid):
    try:
        response = requests.get(
            GRAFANA_URL,
            params={"type": "dash-db"},
            auth=HTTPBasicAuth(GRAFANA_USER, GRAFANA_PASSWORD)
        )
        response.raise_for_status()
        dashboards = response.json()
        
        for dashboard in dashboards:
            if dashboard.get("uid") == uid:
                return dashboard.get("title")
        
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"Error accessing Grafana API: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    title = find_dashboard_by_uid(TARGET_UID)
    
    if title:
        print(f"Dashboard Title for UID '{TARGET_UID}': {title}")
        sys.exit(0)
    else:
        print(f"No dashboard found with UID: {TARGET_UID}")
        sys.exit(1)