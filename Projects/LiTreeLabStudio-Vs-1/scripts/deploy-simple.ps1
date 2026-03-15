# LiTree Social - Simple Azure Deployment Script
param(
    [Parameter(Mandatory=$false)]
    [string]$AppName = "litreesocial",
    
    [Parameter(Mandatory=$false)]
    [string]$ResourceGroup = "litreesocial-rg",
    
    [Parameter(Mandatory=$false)]
    [string]$Location = "canadacentral",
    
    [Parameter(Mandatory=$false)]
    [string]$PlanName = "litreesocial-plan"
)

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  LiTree Social - Azure Deployment Script" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# Check if Azure CLI is available
$azVersion = az --version 2>&1 | Select-String "azure-cli"
if (-not $azVersion) {
    Write-Host "ERROR: Azure CLI not found!" -ForegroundColor Red
    Write-Host "Please install Azure CLI from: https://aka.ms/installazurecliwindows"
    exit 1
}
Write-Host "Azure CLI found: $azVersion" -ForegroundColor Green

# Check if logged in to Azure
$account = az account show --output json 2>&1 | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Not logged in to Azure. Run 'az login' first." -ForegroundColor Red
    exit 1
}
Write-Host "Logged in as: $($account.user.name)" -ForegroundColor Green
Write-Host ""

# Create Resource Group
Write-Host "[STEP 1/5] Creating Resource Group..." -ForegroundColor Yellow
$rgExists = az group exists --name $ResourceGroup
if ($rgExists -eq "false") {
    az group create --name $ResourceGroup --location $Location --output none
    Write-Host "  Created Resource Group: $ResourceGroup" -ForegroundColor Green
} else {
    Write-Host "  Resource Group exists: $ResourceGroup" -ForegroundColor Green
}

# Create App Service Plan (Linux, Free F1 tier)
Write-Host "[STEP 2/5] Creating App Service Plan..." -ForegroundColor Yellow
$planExists = az appservice plan list --query "[?name=='$PlanName']" --output tsv
if (-not $planExists) {
    az appservice plan create --name $PlanName --resource-group $ResourceGroup --sku F1 --is-linux --output none
    Write-Host "  Created App Service Plan: $PlanName (F1 Free)" -ForegroundColor Green
} else {
    Write-Host "  App Service Plan exists: $PlanName" -ForegroundColor Green
}

# Create Web App with Python 3.11
Write-Host "[STEP 3/5] Creating Web App..." -ForegroundColor Yellow
$webappExists = az webapp list --query "[?name=='$AppName']" --output tsv
if (-not $webappExists) {
    Write-Host "  Creating Web App: $AppName (this may take a minute)..." -ForegroundColor Cyan
    az webapp create --name $AppName --resource-group $ResourceGroup --plan $PlanName --runtime "PYTHON|3.11" --output none
    Write-Host "  Created Web App: $AppName" -ForegroundColor Green
} else {
    Write-Host "  Web App exists: $AppName" -ForegroundColor Green
}

# Configure App Settings
Write-Host "[STEP 4/5] Configuring App Settings..." -ForegroundColor Yellow
$settings = @{
    "SCM_DO_BUILD_DURING_DEPLOYMENT" = "true"
    "ENABLE_ORYX_BUILD" = "true"
    "PYTHON_VERSION" = "3.11"
    "WEBSITE_PORT" = "8000"
}

$settingsList = @()
foreach ($key in $settings.Keys) {
    $settingsList += "$key=$($settings[$key])"
}

az webapp config appsettings set --name $AppName --resource-group $ResourceGroup --settings $settingsList --output none
Write-Host "  App Settings configured" -ForegroundColor Green

# Deploy Application
Write-Host "[STEP 5/5] Deploying Application..." -ForegroundColor Yellow
Write-Host "  Creating deployment zip..." -ForegroundColor Cyan

# Create temporary deployment directory
$deployDir = "deploy_temp"
if (Test-Path $deployDir) {
    Remove-Item -Recurse -Force $deployDir
}
New-Item -ItemType Directory -Path $deployDir | Out-Null

# Copy essential files
$filesToCopy = @(
    "app.py",
    "requirements.txt",
    "startup.sh",
    "data/social.db"
)

foreach ($file in $filesToCopy) {
    if (Test-Path $file) {
        $dest = Join-Path $deployDir (Split-Path $file -Leaf)
        Copy-Item $file $dest -Force
        Write-Host "    Copied: $file" -ForegroundColor Gray
    }
}

# Copy directories
$dirsToCopy = @("templates", "static", "backend", "uploads")
foreach ($dir in $dirsToCopy) {
    if (Test-Path $dir) {
        Copy-Item -Recurse $dir $deployDir -Force
        Write-Host "    Copied: $dir/" -ForegroundColor Gray
    }
}

# Create zip
$zipPath = "deployment.zip"
if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
}

Add-Type -Assembly System.IO.Compression.FileSystem
$compressionLevel = [System.IO.Compression.CompressionLevel]::Optimal
[System.IO.Compression.ZipFile]::CreateFromDirectory($deployDir, $zipPath, $compressionLevel, $false)

Write-Host "  Deploying to Azure..." -ForegroundColor Cyan
az webapp deploy --name $AppName --resource-group $ResourceGroup --src-path $zipPath --type zip --output none

# Cleanup
Remove-Item -Recurse -Force $deployDir
Remove-Item $zipPath -Force

Write-Host "  Deployment complete!" -ForegroundColor Green
Write-Host ""

# Get the app URL
$appUrl = "https://$AppName.azurewebsites.net"
Write-Host "=============================================" -ForegroundColor Green
Write-Host "  DEPLOYMENT SUCCESSFUL!" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Your app is available at:" -ForegroundColor Cyan
Write-Host "  $appUrl" -ForegroundColor White
Write-Host ""
Write-Host "Useful commands:" -ForegroundColor Yellow
Write-Host "  View logs: az webapp log tail --name $AppName --resource-group $ResourceGroup"
Write-Host "  SSH into app: az webapp ssh --name $AppName --resource-group $ResourceGroup"
Write-Host "  Restart app: az webapp restart --name $AppName --resource-group $ResourceGroup"
