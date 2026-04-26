#!/usr/bin/env bash
set -euo pipefail

python manage.py migrate --noinput

# Start the Django app via Gunicorn
exec gunicorn attendance_system.wsgi:application --bind "0.0.0.0:${PORT:-8000}" --workers "${WEB_CONCURRENCY:-2}"
