#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Deploy LiTree Social to Azure App Service
.DESCRIPTION
    Automates deployment of Flask app to Azure with all configurations
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$AppName,
    
    [Parameter(Mandatory=$false)]
    [string]$ResourceGroup = $AppName + "-rg",
    
    [Parameter(Mandatory=$false)]
    [string]$Location = "canadacentral",
    
    [Parameter(Mandatory=$false)]
    [string]$Sku = "F1"
)

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  LiTree Social - Azure Deployment Script" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# Check if Azure CLI is installed
if (!(Get-Command az -ErrorAction SilentlyContinue)) {
    Write-Error "Azure CLI not found. Please install it first:"
    Write-Host "https://aka.ms/installazurecliwindows"
    exit 1
}

# Check if logged in
$account = az account show 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Logging into Azure..." -ForegroundColor Yellow
    az login
}

Write-Host "[STEP 1/6] Checking/Creating Resource Group..." -ForegroundColor Green
$rg = az group show --name $ResourceGroup 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Creating Resource Group: $ResourceGroup in $Location" -ForegroundColor Yellow
    az group create --name $ResourceGroup --location $Location --output none
}
else {
    Write-Host "Resource Group already exists: $ResourceGroup" -ForegroundColor Gray
}

Write-Host "[STEP 2/6] Checking/Creating App Service Plan..." -ForegroundColor Green
$planName = "$AppName-plan"
$plan = az appservice plan show --name $planName --resource-group $ResourceGroup 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Creating App Service Plan: $planName ($Sku)" -ForegroundColor Yellow
    az appservice plan create `
        --name $planName `
        --resource-group $ResourceGroup `
        --location $Location `
        --sku $Sku `
        --is-linux `
        --output none
}

Write-Host "[STEP 3/6] Checking/Creating Web App..." -ForegroundColor Green
$webapp = az webapp show --name $AppName --resource-group $ResourceGroup 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Creating Web App: $AppName" -ForegroundColor Yellow
    az webapp create `
        --name $AppName `
        --resource-group $ResourceGroup `
        --plan $planName `
        --runtime "PYTHON|3.11" `
        --startup-file "startup.sh" `
        --output none
}
else {
    Write-Host "Web App already exists: $AppName" -ForegroundColor Gray
}

Write-Host "[STEP 4/6] Configuring App Settings..." -ForegroundColor Green

# Generate a secure secret key
$secretKey = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 64 | ForEach-Object { [char]$_ })

az webapp config appsettings set `
    --name $AppName `
    --resource-group $ResourceGroup `
    --settings `
        "SECRET_KEY=$secretKey" `
        "WEBSITE_RUN_FROM_PACKAGE=1" `
        "SCM_DO_BUILD_DURING_DEPLOYMENT=true" `
        "ENABLE_ORYX_BUILD=true" `
        "WEBSITE_HEALTHCHECK_MAXPINGFAILURES=5" `
        "PYTHON_VERSION=3.11" `
    --output none

Write-Host "[STEP 5/6] Configuring CORS..." -ForegroundColor Green
az webapp cors add `
    --name $AppName `
    --resource-group $ResourceGroup `
    --allowed-origins "*" `
    --output none

Write-Host "[STEP 6/6] Deploying Application..." -ForegroundColor Green
Write-Host "This may take a few minutes..." -ForegroundColor Yellow

# Create deployment package
$zipFile = "$env:TEMP\litree-deploy.zip"
if (Test-Path $zipFile) {
    Remove-Item $zipFile -Force
}

# Zip the app (excluding unnecessary files)
$exclude = @("venv", "__pycache__", "*.pyc", ".git", "node_modules", ".vscode", 
             "users.txt", "posts.txt", "*.log", "data/*.db")

Compress-Archive -Path ".\*" -DestinationPath $zipFile -Force

# Deploy
az webapp deploy `
    --name $AppName `
    --resource-group $ResourceGroup `
    --src-path $zipFile `
    --type zip `
    --async false

# Clean up
Remove-Item $zipFile -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "=============================================" -ForegroundColor Green
Write-Host "  DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Your site is live at:" -ForegroundColor Cyan
Write-Host "  https://$AppName.azurewebsites.net" -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Visit the URL above" -ForegroundColor White
Write-Host "  2. Register an account" -ForegroundColor White
Write-Host "  3. Configure Azure OpenAI (run: ./setup-openai.ps1)" -ForegroundColor White
Write-Host "  4. Enable Application Insights" -ForegroundColor White
Write-Host ""
