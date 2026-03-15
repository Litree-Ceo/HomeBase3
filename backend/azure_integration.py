"""
Azure Integration for HomeBase3 Backend
Provides utilities for Azure services integration
"""

import os
from typing import Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class AzureConfig:
    """Azure configuration handler"""
    
    # App Service
    AZURE_APP_NAME = os.getenv("WEBSITE_INSTANCE_ID", "local")
    AZURE_REGION = os.getenv("WEBSITE_LOCATION", "local")
    
    # Key Vault
    AZURE_KEYVAULT_URL = os.getenv("AZURE_KEYVAULT_URL")
    AZURE_KEYVAULT_TENANT_ID = os.getenv("AZURE_TENANT_ID")
    AZURE_KEYVAULT_CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
    AZURE_KEYVAULT_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")
    
    # Application Insights
    APPINSIGHTS_KEY = os.getenv("APPINSIGHTS_INSTRUMENTATIONKEY")
    APPINSIGHTS_CONNECTION_STRING = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    
    # OpenAI
    AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
    AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
    
    @staticmethod
    def is_azure() -> bool:
        """Check if running on Azure App Service"""
        return bool(os.getenv("WEBSITE_INSTANCE_ID"))
    
    @staticmethod
    def get_secret(secret_name: str) -> Optional[str]:
        """
        Get secret from Azure Key Vault
        Requires Managed Identity or Service Principal credentials
        """
        try:
            from azure.identity import DefaultAzureCredential
            from azure.keyvault.secrets import SecretClient
            
            if not AzureConfig.AZURE_KEYVAULT_URL:
                logger.warning("Key Vault URL not configured")
                return None
            
            credential = DefaultAzureCredential()
            client = SecretClient(
                vault_url=AzureConfig.AZURE_KEYVAULT_URL,
                credential=credential
            )
            
            secret = client.get_secret(secret_name)
            return secret.value
            
        except Exception as e:
            logger.error(f"Failed to get secret {secret_name}: {str(e)}")
            return None

class AzureOpenAIProvider:
    """Azure OpenAI integration"""
    
    def __init__(self):
        """Initialize Azure OpenAI client"""
        if not all([
            AzureConfig.AZURE_OPENAI_ENDPOINT,
            AzureConfig.AZURE_OPENAI_API_KEY
        ]):
            logger.warning("Azure OpenAI not configured")
            self.client = None
            return
        
        try:
            from openai import AzureOpenAI
            
            self.client = AzureOpenAI(
                api_version="2024-02-15-preview",
                azure_endpoint=AzureConfig.AZURE_OPENAI_ENDPOINT,
                api_key=AzureConfig.AZURE_OPENAI_API_KEY,
            )
            logger.info("Azure OpenAI client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Azure OpenAI: {str(e)}")
            self.client = None
    
    async def complete(self, prompt: str, system_prompt: str, max_tokens: int = 2000) -> str:
        """Get completion from Azure OpenAI"""
        if not self.client:
            raise Exception("Azure OpenAI client not configured")
        
        try:
            response = self.client.chat.completions.create(
                model=AzureConfig.AZURE_OPENAI_DEPLOYMENT,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Azure OpenAI error: {str(e)}")
            raise

class AzureMonitoring:
    """Application Insights monitoring"""
    
    @staticmethod
    def log_event(event_name: str, properties: dict = None, measurements: dict = None):
        """Log custom event to Application Insights"""
        if not AzureConfig.APPINSIGHTS_KEY:
            return
        
        try:
            from applicationinsights import TelemetryClient
            
            client = TelemetryClient(AzureConfig.APPINSIGHTS_KEY)
            client.track_event(event_name, properties, measurements)
            client.flush()
        except Exception as e:
            logger.warning(f"Failed to log event: {str(e)}")
    
    @staticmethod
    def log_exception(exception: Exception):
        """Log exception to Application Insights"""
        if not AzureConfig.APPINSIGHTS_KEY:
            return
        
        try:
            from applicationinsights import TelemetryClient
            
            client = TelemetryClient(AzureConfig.APPINSIGHTS_KEY)
            client.track_exception(exception)
            client.flush()
        except Exception as e:
            logger.warning(f"Failed to log exception: {str(e)}")
    
    @staticmethod
    def log_metric(metric_name: str, value: float, properties: dict = None):
        """Log metric to Application Insights"""
        if not AzureConfig.APPINSIGHTS_KEY:
            return
        
        try:
            from applicationinsights import TelemetryClient
            
            client = TelemetryClient(AzureConfig.APPINSIGHTS_KEY)
            client.track_metric(metric_name, value, properties=properties)
            client.flush()
        except Exception as e:
            logger.warning(f"Failed to log metric: {str(e)}")

# Configuration for FastAPI
AZURE_APP_CONFIG = {
    "is_azure": AzureConfig.is_azure(),
    "app_name": AzureConfig.AZURE_APP_NAME,
    "region": AzureConfig.AZURE_REGION,
    "insights_enabled": bool(AzureConfig.APPINSIGHTS_KEY)
}
