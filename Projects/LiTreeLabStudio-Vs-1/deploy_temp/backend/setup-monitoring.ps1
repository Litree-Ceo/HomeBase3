#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Setup Application Insights for LiTree Social
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$AppName,
    
    [Parameter(Mandatory=$false)]
    [string]$ResourceGroup = $AppName + "-rg",
    
    [Parameter(Mandatory=$false)]
    [string]$InsightsName = $AppName + "-insights"
)

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  Application Insights Setup" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# Check Azure CLI
if (!(Get-Command az -ErrorAction SilentlyContinue)) {
    Write-Error "Azure CLI not found."
    exit 1
}

# Login check
$account = az account show 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Logging into Azure..." -ForegroundColor Yellow
    az login
}

Write-Host "[STEP 1/3] Creating Application Insights..." -ForegroundColor Green

$insights = az monitor app-insights component show `
    --app $InsightsName `
    --resource-group $ResourceGroup 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "Creating Application Insights: $InsightsName" -ForegroundColor Yellow
    
    az monitor app-insights component create `
        --app $InsightsName `
        --location "canadacentral" `
        --resource-group $ResourceGroup `
        --application-type web `
        --output none
}
else {
    Write-Host "Application Insights already exists" -ForegroundColor Gray
}

Write-Host "[STEP 2/3] Getting Instrumentation Key..." -ForegroundColor Green

$instrumentationKey = az monitor app-insights component show `
    --app $InsightsName `
    --resource-group $ResourceGroup `
    --query instrumentationKey `
    --output tsv

$connectionString = az monitor app-insights component show `
    --app $InsightsName `
    --resource-group $ResourceGroup `
    --query connectionString `
    --output tsv

Write-Host "[STEP 3/3] Configuring App Settings..." -ForegroundColor Green

az webapp config appsettings set `
    --name $AppName `
    --resource-group $ResourceGroup `
    --settings `
        "APPINSIGHTS_INSTRUMENTATIONKEY=$instrumentationKey" `
        "APPLICATIONINSIGHTS_CONNECTION_STRING=$connectionString" `
        "ApplicationInsightsAgent_EXTENSION_VERSION=~2" `
        "XDT_MicrosoftApplicationInsights_Mode=default" `
    --output none

Write-Host ""
Write-Host "=============================================" -ForegroundColor Green
Write-Host "  MONITORING ENABLED!" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
Write-Host ""
Write-Host "View your metrics at:" -ForegroundColor Cyan
Write-Host "  https://portal.azure.com/#resource/subscriptions/$((az account show --query id -o tsv))/resourceGroups/$ResourceGroup/providers/Microsoft.Insights/components/$InsightsName" -ForegroundColor White
Write-Host ""
Write-Host "Features enabled:" -ForegroundColor Yellow
Write-Host "  - Request tracking" -ForegroundColor White
Write-Host "  - Exception logging" -ForegroundColor White
Write-Host "  - Performance metrics" -ForegroundColor White
Write-Host "  - User analytics" -ForegroundColor White
Write-Host ""
