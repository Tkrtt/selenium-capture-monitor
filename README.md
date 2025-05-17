# GUIDE

This is a guide

## How to use

### For Grafana

python3 capture.py --grafana -u URL -d DASHBOARD_ID -t
Grafana: URL, DASHBOARD_ID, TIME_RANGE, OUTPUT
Grafana URL format: IP:PORT/d/UDdpyzz7z/prometheus-2-0-stats?orgId=1&from=now-1h&to=now&timezone=browser&refresh=1m

### For Dynatrace

python3 capture.py --dynatrace -u URL -e ENVIRONMENT -d DASHBOARD_ID -m MANAGEMENT_ZONE -t TIME_RANGE -o OUTPUT_DIR
Dynatrace: URL, ENVIRONMENT, DASHBOARD_ID, MANAGEMENT_ZONE, TIME_RANGE, OUTPUT_DIR
Dynatrace URL format: IP:PORT/e/ENVIRONMENT/#dashboard;gf=MANAGEMENT_ZONE;id=DASHBOARD_ID;gtf=TIME_RANGE
Dynatrace URL example: IP:PORT/e/ENVIRONMENT/#dashboard;gf=MANAGEMENT_ZONE;id=DASHBOARD_ID;gtf=-24h%20to%20now

<!-- python3 capture.py --splunk -u URL
Splunk: URL,
Splunk URL format: IP:PORT/en-US/app/search/roc_transactions_overview_dashboard?form.global_time.earliest=-60m%40m&form.global_time.latest=now&form.transaction_type=*&form.refresh+r%3D_ate=1m -->