#!/bin/sh
set -e

# Collect static files first, so that they are available by nginx
python manage.py collectstatic --noinput

if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

# Migrate DB before starting the server
python manage.py migrate --noinput

exec "$@"