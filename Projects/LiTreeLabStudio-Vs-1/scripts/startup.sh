#!/bin/bash

# Azure App Service Startup Script for LiTree Social

# Set Python path
export PYTHONPATH=/home/site/wwwroot:$PYTHONPATH

# Change to app directory
cd /home/site/wwwroot

# Initialize database if needed
python -c "from app import Database; Database.init_db()"

# Seed content if first run
python -c "
import os
from pathlib import Path
if not Path('data/social.db').exists():
    print('First run detected, seeding database...')
    import subprocess
    subprocess.run(['python', 'content_bot.py'])
"

# Start Gunicorn with Socket.IO support
# Workers=4 for Azure F1 plan (can scale up for higher plans)
exec gunicorn --bind 0.0.0.0:$PORT \
    --workers 4 \
    --worker-class gevent \
    --worker-connections 1000 \
    --timeout 120 \
    --keep-alive 5 \
    --access-logfile '-' \
    --error-logfile '-' \
    --capture-output \
    --enable-stdio-inheritance \
    app:app
