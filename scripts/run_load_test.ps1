# Script to run Locust Load Test
# Usage: ./scripts/run_load_test.ps1 [Users] [SpawnRate] [Duration]

param (
    [int]$Users = 50,
    [int]$SpawnRate = 5,
    [string]$Duration = "1m"
)

$ReportFile = "tests/load/report_$(Get-Date -Format 'yyyyMMdd_HHmmss').html"
$HostUrl = "http://localhost:8000/api/v1"

Write-Host "Starting Load Test..."
Write-Host "Users: $Users"
Write-Host "Spawn Rate: $SpawnRate users/s"
Write-Host "Duration: $Duration"
Write-Host "Target: $HostUrl"
Write-Host "Report: $ReportFile"

# Ensure directory exists
New-Item -ItemType Directory -Force -Path "tests/load" | Out-Null

# Run Locust
locust -f tests/load/locustfile.py `
    --headless `
    -u $Users `
    -r $SpawnRate `
    --run-time $Duration `
    --html $ReportFile `
    --host $HostUrl

Write-Host "Load Test Completed."
Write-Host "Report generated at: $ReportFile"
