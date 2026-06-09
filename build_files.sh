#!/bin/bash
set -e

echo "=== Installing dependencies ==="
pip install -r requirements.txt

echo "=== Creating static directories ==="
mkdir -p staticfiles

echo "=== Collecting static files ==="
python manage.py collectstatic --noinput -v 2

echo "=== Checking static files ==="
echo "Files in staticfiles:"
find staticfiles -type f | head -20

echo "=== Admin static files ==="
ls -la staticfiles/admin/css/ 2>/dev/null || echo "No admin CSS found"

echo "=== Build completed ==="