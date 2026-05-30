# Azure Deployment Guide
## Smart Retail Assistant – Cloud Deployment
### Left Shift Program 2026 – Data & AI (T5)

---

## 1. Prerequisites

- Azure subscription (free tier works for dev)
- Azure CLI installed: `winget install Microsoft.AzureCLI`
- Docker Desktop installed
- GitHub account with the project repository

---

## 2. Azure Resources to Create

```bash
# Login
az login

# Set variables
RESOURCE_GROUP="rg-smart-retail"
LOCATION="eastus"
ACR_NAME="smartretailacr"
APP_NAME="smart-retail-assistant"
SQL_SERVER="smart-retail-sql"
SQL_DB="retaildb"
KEYVAULT_NAME="smart-retail-kv"
OPENAI_NAME="smart-retail-openai"
```

---

## 3. Step-by-Step Deployment

### Step 1 – Create Resource Group
```bash
az group create --name $RESOURCE_GROUP --location $LOCATION
```

### Step 2 – Azure Container Registry
```bash
az acr create \
  --resource-group $RESOURCE_GROUP \
  --name $ACR_NAME \
  --sku Basic \
  --admin-enabled true
```

### Step 3 – Azure SQL Database
```bash
# Create SQL server
az sql server create \
  --name $SQL_SERVER \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --admin-user sqladmin \
  --admin-password "RetailPass123!"

# Create database
az sql db create \
  --resource-group $RESOURCE_GROUP \
  --server $SQL_SERVER \
  --name $SQL_DB \
  --service-objective Basic

# Allow Azure services
az sql server firewall-rule create \
  --resource-group $RESOURCE_GROUP \
  --server $SQL_SERVER \
  --name AllowAzureServices \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0
```

### Step 4 – Azure Key Vault
```bash
az keyvault create \
  --name $KEYVAULT_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION

# Store secrets
az keyvault secret set --vault-name $KEYVAULT_NAME \
  --name "AzureOpenAIKey" --value "your-openai-key"

az keyvault secret set --vault-name $KEYVAULT_NAME \
  --name "SqlConnectionString" \
  --value "mssql+pyodbc://sqladmin:RetailPass123!@${SQL_SERVER}.database.windows.net/${SQL_DB}?driver=ODBC+Driver+18+for+SQL+Server"
```

### Step 5 – Azure OpenAI
```bash
az cognitiveservices account create \
  --name $OPENAI_NAME \
  --resource-group $RESOURCE_GROUP \
  --kind OpenAI \
  --sku S0 \
  --location eastus

# Deploy GPT-4o model
az cognitiveservices account deployment create \
  --name $OPENAI_NAME \
  --resource-group $RESOURCE_GROUP \
  --deployment-name gpt-4o \
  --model-name gpt-4o \
  --model-version "2024-05-13" \
  --model-format OpenAI \
  --sku-capacity 10 \
  --sku-name Standard

# Deploy embedding model
az cognitiveservices account deployment create \
  --name $OPENAI_NAME \
  --resource-group $RESOURCE_GROUP \
  --deployment-name text-embedding-ada-002 \
  --model-name text-embedding-ada-002 \
  --model-version "2" \
  --model-format OpenAI \
  --sku-capacity 10 \
  --sku-name Standard
```

### Step 5b – Azure AI Search (RAG Vector Store)
```bash
SEARCH_NAME="smart-retail-search"

# Create free-tier search service (1 replica, 1 partition)
az search service create \
  --name $SEARCH_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku free

# Get the admin key
SEARCH_KEY=$(az search admin-key show \
  --service-name $SEARCH_NAME \
  --resource-group $RESOURCE_GROUP \
  --query primaryKey -o tsv)

SEARCH_ENDPOINT="https://${SEARCH_NAME}.search.windows.net"

echo "AZURE_SEARCH_ENDPOINT=$SEARCH_ENDPOINT"
echo "AZURE_SEARCH_API_KEY=$SEARCH_KEY"

# After deployment, build the RAG index:
#   python scripts/build_rag_from_pdfs.py
```

### Step 6 – Build and Push Docker Image
```bash
# Build image
docker build -t smart-retail-assistant:latest .

# Tag for ACR
docker tag smart-retail-assistant:latest \
  ${ACR_NAME}.azurecr.io/smart-retail-assistant:latest

# Login to ACR
az acr login --name $ACR_NAME

# Push
docker push ${ACR_NAME}.azurecr.io/smart-retail-assistant:latest
```

### Step 7 – Deploy to Azure Container Apps
```bash
# Create Container Apps environment
az containerapp env create \
  --name smart-retail-env \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION

# Get ACR credentials
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query passwords[0].value -o tsv)

# Get OpenAI key and endpoint
OPENAI_KEY=$(az cognitiveservices account keys list \
  --name $OPENAI_NAME --resource-group $RESOURCE_GROUP \
  --query key1 -o tsv)
OPENAI_ENDPOINT=$(az cognitiveservices account show \
  --name $OPENAI_NAME --resource-group $RESOURCE_GROUP \
  --query properties.endpoint -o tsv)

# Deploy container app
az containerapp create \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --environment smart-retail-env \
  --image ${ACR_NAME}.azurecr.io/smart-retail-assistant:latest \
  --registry-server ${ACR_NAME}.azurecr.io \
  --registry-username $ACR_NAME \
  --registry-password $ACR_PASSWORD \
  --target-port 8000 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 3 \
  --cpu 1.0 \
  --memory 2.0Gi \
  --env-vars \
    AZURE_OPENAI_API_KEY=$OPENAI_KEY \
    AZURE_OPENAI_ENDPOINT=$OPENAI_ENDPOINT \
    AZURE_OPENAI_DEPLOYMENT=gpt-4o \
    APP_ENV=production \
    LOG_LEVEL=INFO

# Get the app URL
az containerapp show \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --query properties.configuration.ingress.fqdn -o tsv
```

---

## 4. GitHub Actions Secrets

Add these secrets to your GitHub repository (**Settings → Secrets → Actions**):

| Secret Name | Value |
|---|---|
| `ACR_LOGIN_SERVER` | `smartretailacr.azurecr.io` |
| `ACR_USERNAME` | ACR admin username |
| `ACR_PASSWORD` | ACR admin password |
| `AZURE_CREDENTIALS` | JSON output of `az ad sp create-for-rbac` |
| `AZURE_WEBAPP_NAME` | `smart-retail-assistant` |
| `DATABASE_URL` | Neon PostgreSQL connection string |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint URL |
| `AZURE_SEARCH_ENDPOINT` | Azure AI Search endpoint |
| `AZURE_SEARCH_API_KEY` | Azure AI Search admin key |
| `AZURE_STORAGE_CONNECTION_STRING` | Azure Blob Storage connection string |

---

## 5. Environment Variables Summary

| Variable | Source | Description |
|---|---|---|
| `AZURE_OPENAI_API_KEY` | Key Vault | Azure OpenAI API key |
| `AZURE_OPENAI_ENDPOINT` | Key Vault | Azure OpenAI endpoint |
| `AZURE_OPENAI_DEPLOYMENT` | Config | gpt-4o |
| `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` | Config | text-embedding-ada-002 |
| `AZURE_SEARCH_ENDPOINT` | Config | Azure AI Search endpoint |
| `AZURE_SEARCH_API_KEY` | Key Vault | Azure AI Search admin key |
| `AZURE_SEARCH_INDEX_NAME` | Config | retail-knowledge-base |
| `AZURE_STORAGE_CONNECTION_STRING` | Key Vault | Blob storage connection string |
| `AZURE_BLOB_CONTAINER` | Config | smart-retail-ai |
| `DATABASE_URL` | Key Vault | Neon PostgreSQL connection string |
| `APP_ENV` | Config | production |
| `LOG_LEVEL` | Config | INFO |

---

## 6. Health Check & Monitoring

```bash
# Check app health
curl https://your-app.azurecontainerapps.io/health

# View logs
az containerapp logs show \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --follow

# Scale manually
az containerapp update \
  --name $APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --min-replicas 2 \
  --max-replicas 5
```

---

## 7. Cost Estimate (Monthly)

| Service | Tier | Est. Cost/Month |
|---|---|---|
| Azure Container Apps | Consumption (1 replica) | ~$15 |
| Azure SQL Database | Basic (5 DTU) | ~$5 |
| Azure OpenAI | Pay-per-use (light usage) | ~$10–30 |
| Azure Container Registry | Basic | ~$5 |
| Azure Key Vault | Standard | ~$1 |
| Azure Monitor | Basic | ~$5 |
| **Total** | | **~$41–61/month** |

> Free tier credits cover most of this for a demo/capstone project.
