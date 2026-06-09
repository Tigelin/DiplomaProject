#!/bin/bash
set -e

echo "=== Installing dependencies ==="
pip install -r requirements.txt

echo "=== Creating static directories ==="
mkdir -p staticfiles
mkdir -p /tmp/staticfiles

echo "=== Collecting static files ==="
python manage.py collectstatic --noinput --clear

echo "=== Copying static to multiple locations ==="
cp -r staticfiles/* /tmp/staticfiles/ 2>/dev/null || true
ls -la staticfiles/

echo "=== Build completed ==="