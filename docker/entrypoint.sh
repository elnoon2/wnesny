#!/bin/sh
# Creates/updates the database schema and the interest catalogue, then runs the given command.
set -e
flask --app run.py db upgrade
python seed_interests.py
exec "$@"
