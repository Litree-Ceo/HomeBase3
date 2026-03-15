# 🚀 Azure Deployment Guide - LiTree Social

Complete guide to deploy LiTree Social to Azure App Service with OpenAI and Monitoring.

## Prerequisites

1. **Azure CLI** installed: https://aka.ms/installazurecliwindows
2. **Azure account** with active subscription
3. **PowerShell** (Windows) or **Bash** (Linux/Mac)

---

## Quick Deploy (One Command)

```powershell
# Open PowerShell in project folder
# Run the deployment script
.\deploy-azure.ps1 -AppName "litreesocial" -Location "canadacentral" -Sku "F1"
```

This will:
- ✅ Create Resource Group
- ✅ Create App Service Plan (F1 Free tier)
- ✅ Create Web App
- ✅ Configure settings
- ✅ Deploy your code
- ✅ Return the live URL

---

## Step-by-Step Manual Deployment

### Step 1: Login to Azure

```powershell
az login
# This opens browser for authentication
```

### Step 2: Set Variables

```powershell
$AppName = "litreesocial"  # Must be globally unique
$ResourceGroup = "$AppName-rg"
$Location = "canadacentral"
```

### Step 3: Create Resource Group

```powershell
az group create `
    --name $ResourceGroup `
    --location $Location
```

### Step 4: Create App Service Plan

```powershell
# For Free tier (F1):
az appservice plan create `
    --name "$AppName-plan" `
    --resource-group $ResourceGroup `
    --location $Location `
    --sku F1 `
    --is-linux

# For Production (S1):
az appservice plan create `
    --name "$AppName-plan" `
    --resource-group $ResourceGroup `
    --location $Location `
    --sku S1 `
    --is-linux
```

### Step 5: Create Web App

```powershell
az webapp create `
    --name $AppName `
    --resource-group $ResourceGroup `
    --plan "$AppName-plan" `
    --runtime "PYTHON|3.11" `
    --startup-file "startup.sh"
```

### Step 6: Configure Settings

```powershell
# Generate secret key
$SecretKey = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 64 | ForEach-Object { [char]$_ })

# Set app settings
az webapp config appsettings set `
    --name $AppName `
    --resource-group $ResourceGroup `
    --settings `
        "SECRET_KEY=$SecretKey" `
        "SCM_DO_BUILD_DURING_DEPLOYMENT=true" `
        "ENABLE_ORYX_BUILD=true"
```

### Step 7: Deploy Code

```powershell
# Create zip of your app
Compress-Archive -Path ".\*" -DestinationPath "litree-deploy.zip" -Force

# Deploy
az webapp deploy `
    --name $AppName `
    --resource-group $ResourceGroup `
    --src-path "litree-deploy.zip" `
    --type zip
```

### Step 8: Verify Deployment

```powershell
# Open in browser
Start-Process "https://$AppName.azurewebsites.net"
```

---

## Azure OpenAI Setup

### Option 1: Automated Script

```powershell
.\setup-openai.ps1 -AppName "litreesocial"
```

### Option 2: Manual Setup

```powershell
# Create OpenAI resource
az cognitiveservices account create `
    --name "litreesocial-openai" `
    --resource-group $ResourceGroup `
    --location "canadaeast" `
    --kind OpenAI `
    --sku S0

# Deploy GPT-3.5 model
az cognitiveservices account deployment create `
    --name "litreesocial-openai" `
    --resource-group $ResourceGroup `
    --deployment-name "litree-gpt35" `
    --model-name "gpt-35-turbo" `
    --model-version "0613" `
    --model-format OpenAI `
    --sku-capacity 1 `
    --sku-name "Standard"

# Get keys
$OpenAIKey = az cognitiveservices account keys list `
    --name "litreesocial-openai" `
    --resource-group $ResourceGroup `
    --query key1 --output tsv

# Configure app
az webapp config appsettings set `
    --name $AppName `
    --resource-group $ResourceGroup `
    --settings "OPENAI_API_KEY=$OpenAIKey"
```

---

## Application Insights Setup

### Option 1: Automated Script

```powershell
.\setup-monitoring.ps1 -AppName "litreesocial"
```

### Option 2: Manual Setup

```powershell
# Create Application Insights
az monitor app-insights component create `
    --app "$AppName-insights" `
    --location $Location `
    --resource-group $ResourceGroup `
    --application-type web

# Get key
$InsightsKey = az monitor app-insights component show `
    --app "$AppName-insights" `
    --resource-group $ResourceGroup `
    --query instrumentationKey --output tsv

# Configure
az webapp config appsettings set `
    --name $AppName `
    --resource-group $ResourceGroup `
    --settings "APPINSIGHTS_INSTRUMENTATIONKEY=$InsightsKey"
```

---

## Post-Deployment Checklist

- [ ] Website loads at `https://YOURAPP.azurewebsites.net`
- [ ] Can register new account
- [ ] Can create posts
- [ ] Can upload images
- [ ] Real-time chat works
- [ ] LitBit AI responds (if OpenAI configured)
- [ ] Application Insights shows data

---

## Scaling Up

### From Free (F1) to Production (S1):

```powershell
az appservice plan update `
    --name "$AppName-plan" `
    --resource-group $ResourceGroup `
    --sku S1
```

### Enable Auto-Scaling:

```powershell
az monitor autoscale create `
    --resource "$AppName-plan" `
    --resource-group $ResourceGroup `
    --min-count 1 `
    --max-count 3 `
    --count 1
```

---

## Custom Domain

```powershell
# Add custom domain
az webapp config hostname add `
    --webapp-name $AppName `
    --resource-group $ResourceGroup `
    --hostname "www.yourdomain.com"

# Upload SSL certificate (if needed)
az webapp config ssl upload `
    --name $AppName `
    --resource-group $ResourceGroup `
    --certificate-file "certificate.pfx" `
    --certificate-password "password"
```

---

## Troubleshooting

### Check Logs

```powershell
# Stream logs
az webapp log tail --name $AppName --resource-group $ResourceGroup

# Get last 100 lines
az webapp log download --name $AppName --resource-group $ResourceGroup
```

### Common Issues

| Issue | Solution |
|-------|----------|
| 500 Error | Check `az webapp log tail` for Python errors |
| Slow startup | Upgrade from F1 to S1 (always-on) |
| File upload fails | Check `MAX_CONTENT_LENGTH` setting |
| WebSocket fails | Ensure `eventlet` is in requirements.txt |
| Database locked | Use Azure SQL instead of SQLite for production |

---

## Production Checklist

Before going live:

- [ ] Upgrade from F1 to at least S1 (always-on)
- [ ] Migrate SQLite to Azure SQL Database
- [ ] Configure backup schedule
- [ ] Set up staging slot
- [ ] Enable HTTPS only
- [ ] Configure IP restrictions (if needed)
- [ ] Set up alerts in Application Insights
- [ ] Configure custom domain with SSL

---

## Estimated Costs

| Tier | Monthly Cost | Features |
|------|--------------|----------|
| F1 | FREE | 1GB storage, 60min CPU/day |
| S1 | ~$73 | Always on, custom domain, SSL |
| S2 | ~$146 | More CPU/memory |
| P1v2 | ~$146 | Premium performance, staging slots |
| OpenAI | ~$0.002/1K tokens | Pay per use |

---

## Support

Azure Resources:
- Azure Portal: https://portal.azure.com
- Azure CLI Docs: https://docs.microsoft.com/cli/azure
- App Service Docs: https://docs.microsoft.com/azure/app-service

Your Live URL will be:
**`https://YOURAPPNAME.azurewebsites.net`**

---

🎉 **Ready to deploy! Run the PowerShell scripts and your social network will be live!**
