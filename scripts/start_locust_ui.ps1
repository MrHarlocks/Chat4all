# Script to start Locust Web UI
$HostUrl = "http://localhost:8000/api/v1"

Write-Host "Starting Locust Web UI..."
Write-Host "Target: $HostUrl"
Write-Host "Access http://localhost:8089 to configure and start the test."

# Ensure directory exists
New-Item -ItemType Directory -Force -Path "tests/load" | Out-Null

# Run Locust in UI mode
locust -f tests/load/locustfile.py --host $HostUrl
