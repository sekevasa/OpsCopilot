# Manufacturing AI Copilot - Multi-Service Startup Script
# This script activates the venv and starts all 5 microservices

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Cyan
& .\venv\Scripts\Activate.ps1

# Create log directory
if (-not (Test-Path ".\logs")) {
    New-Item -ItemType Directory -Path ".\logs" | Out-Null
    Write-Host "Created logs directory" -ForegroundColor Green
}

# Define services and their configuration
$services = @(
    @{
        Name = "data-ingest-service"
        Port = 8001
        Dir  = "services/data-ingest-service"
    },
    @{
        Name = "unified-data-service"
        Port = 8002
        Dir  = "services/unified-data-service"
    },
    @{
        Name = "ai-runtime-service"
        Port = 8003
        Dir  = "services/ai-runtime-service"
    },
    @{
        Name = "forecast-service"
        Port = 8004
        Dir  = "services/forecast-service"
    },
    @{
        Name = "notification-service"
        Port = 8005
        Dir  = "services/notification-service"
    }
)

Write-Host "`n" + "="*70 -ForegroundColor Cyan
Write-Host "Manufacturing AI Copilot - Starting Services" -ForegroundColor Cyan
Write-Host "="*70 + "`n" -ForegroundColor Cyan

# Create a function to run each service in a separate window
function Start-Service {
    param([hashtable]$service)
    
    $scriptBlock = {
        param($svc)
        
        # Re-activate venv in this process
        & ".\venv\Scripts\Activate.ps1"
        
        # Set environment variables
        $env:SERVICE_NAME = $svc.Name
        $env:ENVIRONMENT = "development"
        $env:DEBUG = "true"
        $env:LOG_LEVEL = "INFO"
        $env:PYTHONUNBUFFERED = "1"
        
        # Add current directory to PYTHONPATH for imports
        $env:PYTHONPATH = "."
        
        Write-Host "Starting $($svc.Name) on port $($svc.Port)..." -ForegroundColor Yellow
        Write-Host "Service directory: $($svc.Dir)" -ForegroundColor Gray
        
        cd $svc.Dir
        
        # Run uvicorn
        & uvicorn "main:app" --host 0.0.0.0 --port $svc.Port --reload --log-level info
    }
    
    # Start in a new PowerShell window
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd $PWD; & `$([scriptblock]::Create(`$args[0])) `$args[1]", $scriptBlock.ToString(), ($service | ConvertTo-Json)
}

# Start each service
foreach ($service in $services) {
    Write-Host "Launching $($service.Name)..." -ForegroundColor Green
    Start-Service $service
    Start-Sleep -Milliseconds 500
}

Write-Host "`n" + "="*70 -ForegroundColor Cyan
Write-Host "All services are starting..." -ForegroundColor Cyan
Write-Host "="*70 -ForegroundColor Cyan

Write-Host @"
`nService endpoints:
  ✓ Data Ingest Service:    http://localhost:8001/docs
  ✓ Unified Data Service:   http://localhost:8002/docs
  ✓ AI Runtime Service:     http://localhost:8003/docs
  ✓ Forecast Service:       http://localhost:8004/docs
  ✓ Notification Service:   http://localhost:8005/docs

Health checks:
  GET http://localhost:8001/api/v1/health
  GET http://localhost:8002/api/v1/health
  GET http://localhost:8003/api/v1/health
  GET http://localhost:8004/api/v1/health
  GET http://localhost:8005/api/v1/health

Press Ctrl+C in any service window to stop that service.
To stop all services, close all windows or use: Get-Process pythonw | Stop-Process

"@ -ForegroundColor Cyan

# Keep the main window open
Read-Host "Press Enter to keep this window open (services are running in separate windows)"
