"""
Azure Integration for LiTree Social Backend
Health checks, monitoring, and Azure OpenAI integration
"""

import os
import json
from datetime import datetime
from functools import wraps
import logging

# Setup logging
logging.basicConfig(level=os.getenv('LOG_LEVEL', 'INFO'))
logger = logging.getLogger(__name__)

class HealthCheck:
    """Health check endpoint for Azure App Service"""
    
    @staticmethod
    def get_status():
        """Get current app health status"""
        return {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0',
            'environment': os.getenv('FLASK_ENV', 'development'),
            'uptime': 'tracking enabled'
        }
    
    @staticmethod
    def check_database():
        """Check database connectivity"""
        try:
            import sqlite3
            from pathlib import Path
            db_path = Path(__file__).parent / 'data' / 'social.db'
            conn = sqlite3.connect(str(db_path))
            conn.execute("SELECT 1")
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return False

class AzureOpenAIIntegration:
    """Azure OpenAI integration for assistant responses"""
    
    def __init__(self):
        self.endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        self.api_key = os.getenv('AZURE_OPENAI_API_KEY')
        self.deployment = os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-4o-mini')
        self.api_version = os.getenv('OPENAI_API_VERSION', '2024-02-15-preview')
        self.enabled = bool(self.endpoint and self.api_key)
        
        if self.enabled:
            try:
                from openai import AzureOpenAI
                self.client = AzureOpenAI(
                    api_version=self.api_version,
                    azure_endpoint=self.endpoint,
                    api_key=self.api_key
                )
                logger.info("Azure OpenAI client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Azure OpenAI: {str(e)}")
                self.enabled = False
    
    def generate_response(self, message, context=None):
        """Generate AI response using Azure OpenAI"""
        if not self.enabled:
            return None
        
        try:
            system_prompt = """You are LitBit, a helpful and friendly AI assistant for LiTree Social. 
            You help users navigate the platform, answer questions about features, and provide suggestions.
            Be concise, friendly, and helpful. Always encourage users to explore the platform."""
            
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                temperature=0.7,
                max_tokens=150
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Azure OpenAI generation failed: {str(e)}")
            return None

class ApplicationInsights:
    """Application Insights monitoring"""
    
    @staticmethod
    def log_event(event_name, properties=None, measurements=None):
        """Log custom event to Application Insights"""
        insights_key = os.getenv('APPINSIGHTS_INSTRUMENTATIONKEY')
        if not insights_key:
            return
        
        try:
            from applicationinsights import TelemetryClient
            client = TelemetryClient(insights_key)
            client.track_event(event_name, properties, measurements)
            client.flush()
        except Exception as e:
            logger.warning(f"Failed to log event: {str(e)}")
    
    @staticmethod
    def log_exception(exception):
        """Log exception to Application Insights"""
        insights_key = os.getenv('APPINSIGHTS_INSTRUMENTATIONKEY')
        if not insights_key:
            return
        
        try:
            from applicationinsights import TelemetryClient
            client = TelemetryClient(insights_key)
            client.track_exception(exception)
            client.flush()
        except Exception as e:
            logger.warning(f"Failed to log exception: {str(e)}")

# Initialize Azure services
azure_openai = AzureOpenAIIntegration()
health_check = HealthCheck()

def register_health_routes(app):
    """Register health check and status endpoints"""
    
    @app.route('/health', methods=['GET'])
    def health():
        """Azure health check endpoint"""
        status = health_check.get_status()
        status['database'] = 'connected' if health_check.check_database() else 'disconnected'
        
        if status['database'] == 'connected':
            return status, 200
        else:
            return status, 503
    
    @app.route('/health/live', methods=['GET'])
    def health_live():
        """Kubernetes liveness probe"""
        return {'status': 'alive'}, 200
    
    @app.route('/health/ready', methods=['GET'])
    def health_ready():
        """Kubernetes readiness probe"""
        if health_check.check_database():
            return {'status': 'ready'}, 200
        else:
            return {'status': 'not_ready'}, 503
    
    @app.route('/status', methods=['GET'])
    def status():
        """Detailed status endpoint"""
        import sys
        
        return {
            'app': 'LiTree Social',
            'version': '1.0.0',
            'python': sys.version,
            'environment': os.getenv('FLASK_ENV', 'development'),
            'timestamp': datetime.utcnow().isoformat(),
            'azure': {
                'openai_enabled': azure_openai.enabled,
                'insights_enabled': bool(os.getenv('APPINSIGHTS_INSTRUMENTATIONKEY'))
            },
            'database': {
                'status': 'connected' if health_check.check_database() else 'disconnected'
            }
        }, 200

def log_request_metrics(f):
    """Decorator to log request metrics to Application Insights"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        import time
        start_time = time.time()
        
        try:
            result = f(*args, **kwargs)
            duration = time.time() - start_time
            
            ApplicationInsights.log_event(
                'request_completed',
                {
                    'endpoint': f.__name__,
                    'status': 'success'
                },
                {
                    'duration_ms': duration * 1000
                }
            )
            
            return result
        except Exception as e:
            ApplicationInsights.log_exception(e)
            raise
    
    return decorated_function
