#!/bin/bash

# Stop existing processes
pkill -f gunicorn 
sudo systemctl restart gunicorn-living-science 

# Activate virtual environment
source venv/bin/activate 

# Clean up Python cache
find . -type d -name "__pycache__" -exec rm -rf {} +

# Install/update dependencies
pip install -r requirements.txt

# Database migrations in correct order
# 1. Core app first (User, Publication, etc.)
python manage.py makemigrations core

# 2. Publications app (DocumentVersion)
python manage.py makemigrations publications

# 3. Comments app (Comment)
python manage.py makemigrations comments

# 4. AI Assistant app
python manage.py makemigrations ai_assistant

# Apply all migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Run tests to verify everything works
#python manage.py test

echo "Restart completed successfully!"