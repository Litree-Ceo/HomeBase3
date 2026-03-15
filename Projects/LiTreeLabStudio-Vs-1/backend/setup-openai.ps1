#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Setup Azure OpenAI for LiTree Social
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$AppName,
    
    [Parameter(Mandatory=$false)]
    [string]$ResourceGroup = $AppName + "-rg",
    
    [Parameter(Mandatory=$false)]
    [string]$OpenAIResourceName = $AppName + "-openai"
)

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "  Azure OpenAI Setup for LiTree Social" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# Check if Azure CLI is installed
if (!(Get-Command az -ErrorAction SilentlyContinue)) {
    Write-Error "Azure CLI not found. Please install it first."
    exit 1
}

# Check if logged in
$account = az account show 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Logging into Azure..." -ForegroundColor Yellow
    az login
}

Write-Host "[STEP 1/4] Creating Azure OpenAI Resource..." -ForegroundColor Green

$openai = az cognitiveservices account show `
    --name $OpenAIResourceName `
    --resource-group $ResourceGroup 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "Creating Azure OpenAI: $OpenAIResourceName" -ForegroundColor Yellow
    
    az cognitiveservices account create `
        --name $OpenAIResourceName `
        --resource-group $ResourceGroup `
        --location "canadaeast" `
        --kind OpenAI `
        --sku S0 `
        --output none
}
else {
    Write-Host "Azure OpenAI already exists: $OpenAIResourceName" -ForegroundColor Gray
}

Write-Host "[STEP 2/4] Deploying GPT-3.5 Model..." -ForegroundColor Green

# Check if deployment exists
$deployment = az cognitiveservices account deployment show `
    --name $OpenAIResourceName `
    --resource-group $ResourceGroup `
    --deployment-name "litree-gpt35" 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "Creating GPT-3.5 deployment..." -ForegroundColor Yellow
    
    az cognitiveservices account deployment create `
        --name $OpenAIResourceName `
        --resource-group $ResourceGroup `
        --deployment-name "litree-gpt35" `
        --model-name "gpt-35-turbo" `
        --model-version "0613" `
        --model-format OpenAI `
        --sku-capacity 1 `
        --sku-name "Standard" `
        --output none
}

Write-Host "[STEP 3/4] Getting API Keys..." -ForegroundColor Green

$apiKey = az cognitiveservices account keys list `
    --name $OpenAIResourceName `
    --resource-group $ResourceGroup `
    --query key1 `
    --output tsv

$endpoint = az cognitiveservices account show `
    --name $OpenAIResourceName `
    --resource-group $ResourceGroup `
    --query properties.endpoint `
    --output tsv

Write-Host "[STEP 4/4] Configuring App Settings..." -ForegroundColor Green

az webapp config appsettings set `
    --name $AppName `
    --resource-group $ResourceGroup `
    --settings `
        "OPENAI_API_KEY=$apiKey" `
        "OPENAI_ENDPOINT=$endpoint" `
        "OPENAI_MODEL=litree-gpt35" `
        "AI_ENABLED=true" `
    --output none

Write-Host ""
Write-Host "=============================================" -ForegroundColor Green
Write-Host "  AZURE OPENAI CONFIGURED!" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Details:" -ForegroundColor Cyan
Write-Host "  Resource: $OpenAIResourceName" -ForegroundColor White
Write-Host "  Model: gpt-35-turbo" -ForegroundColor White
Write-Host "  Endpoint: $endpoint" -ForegroundColor Gray
Write-Host ""
Write-Host "LiBit AI Assistant is now powered by Azure OpenAI!" -ForegroundColor Yellow
Write-Host ""
