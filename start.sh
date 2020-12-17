#!/bin/sh
export PYTHONPATH=`pwd`
exec gunicorn -b :8042 --timeout 120 --access-logfile - --error-logfile - app:app