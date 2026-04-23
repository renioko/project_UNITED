release: python manage.py migrate && python manage.py collectstatic --noinput
web: gunicorn portal_united.wsgi --log-file -