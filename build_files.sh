echo "Building project..."
pip install -r requirements.txt
python manage.py collectstatic --noinput --clear
