# Startup command for Azure App Service
# This file gets executed when the app service starts

gunicorn --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind=0.0.0.0:8000 --timeout 120 main:app
