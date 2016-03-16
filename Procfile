web: gunicorn manage:app
init: python manage.py db init
upgrade: python manage.py db upgrade
worker: celery worker -A celery_worker.celery --loglevel=info
