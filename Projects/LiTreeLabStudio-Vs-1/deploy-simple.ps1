# LiTree Social - Simple Azure Deployment Script
param(
    [string]$AppName = "litreesocial",
    [string]$ResourceGroup = "litreesocial-rg",
    [string]$Location = "canadacentral",
    [string]$PlanName = "litreesocial-plan"
)

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  LiTree Social - Azure Deployment Script" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Azure CLI found" -ForegroundColor Green
Write-Host "Logged in as: litbit439@outlook.com" -ForegroundColor Green
Write-Host ""

# Create Resource Group
Write-Host "[STEP 1/5] Creating Resource Group..." -ForegroundColor Yellow
az group create --name $ResourceGroup --location $Location --output none
Write-Host "  Resource Group ready: $ResourceGroup" -ForegroundColor Green

# Create App Service Plan
Write-Host "[STEP 2/5] Creating App Service Plan..." -ForegroundColor Yellow
az appservice plan create --name $PlanName --resource-group $ResourceGroup --sku F1 --is-linux --output none
Write-Host "  App Service Plan ready: $PlanName (F1 Free)" -ForegroundColor Green

# Create Web App with Python 3.11 using --% to stop PowerShell parsing
Write-Host "[STEP 3/5] Creating Web App..." -ForegroundColor Yellow
Write-Host "  Creating Web App: $AppName (this may take a minute)..." -ForegroundColor Cyan

# Use cmd.exe to avoid PowerShell parsing issues
$cmdArgs = "az webapp create --name $AppName --resource-group $ResourceGroup --plan $PlanName --runtime `"PYTHON|3.11`" --output none"
cmd /c $cmdArgs

if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR: Failed to create Web App" -ForegroundColor Red
    exit 1
}
Write-Host "  Web App ready: $AppName" -ForegroundColor Green

# Configure App Settings
Write-Host "[STEP 4/5] Configuring App Settings..." -ForegroundColor Yellow
az webapp config appsettings set --name $AppName --resource-group $ResourceGroup --settings "SCM_DO_BUILD_DURING_DEPLOYMENT=true" "ENABLE_ORYX_BUILD=true" "WEBSITE_PORT=8000" --output none
Write-Host "  App Settings configured" -ForegroundColor Green

# Deploy Application
Write-Host "[STEP 5/5] Deploying Application..." -ForegroundColor Yellow
Write-Host "  Creating deployment zip..." -ForegroundColor Cyan

# Create temporary deployment directory
$deployDir = "deploy_temp"
if (Test-Path $deployDir) { Remove-Item -Recurse -Force $deployDir }
New-Item -ItemType Directory -Path $deployDir | Out-Null

# Copy essential files
@("app.py", "requirements.txt", "startup.sh") | ForEach-Object { 
    if (Test-Path $_) { 
        Copy-Item $_ $deployDir -Force
        Write-Host "    Copied: $_" -ForegroundColor Gray
    }
}

# Copy data directory
if (Test-Path "data") {
    Copy-Item -Recurse "data" "$deployDir/data" -Force
    Write-Host "    Copied: data/" -ForegroundColor Gray
}

# Copy directories
@("templates", "static", "backend", "uploads") | ForEach-Object {
    if (Test-Path $_) {
        Copy-Item -Recurse $_ "$deployDir/$_" -Force
        Write-Host "    Copied: $_/" -ForegroundColor Gray
    }
}

# Create zip
$zipPath = "deployment.zip"
if (Test-Path $zipPath) { Remove-Item $zipPath -Force }

Add-Type -Assembly System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory($deployDir, $zipPath, "Optimal", $false)

Write-Host "  Deploying to Azure (this may take 2-3 minutes)..." -ForegroundColor Cyan
az webapp deploy --name $AppName --resource-group $ResourceGroup --src-path $zipPath --type zip --output none

# Cleanup
Remove-Item -Recurse -Force $deployDir
Remove-Item $zipPath -Force

Write-Host "  Deployment complete!" -ForegroundColor Green
Write-Host ""

# Success message
Write-Host "=============================================" -ForegroundColor Green
Write-Host "  DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Your app should be available at:" -ForegroundColor Cyan
Write-Host "  https://$AppName.azurewebsites.net" -ForegroundColor White
Write-Host ""
Write-Host "NOTE: It may take 1-2 minutes for the app to start up." -ForegroundColor Yellow
