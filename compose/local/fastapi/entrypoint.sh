#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

echo "Checking DNS resolution for 'db' hostname..."
if ! nslookup db; then
    echo "Failed to resolve 'db' hostname. Check your Docker network configuration."
    exit 1
fi

postgres_ready() {
python << END
import sys
import psycopg2
import urllib.parse as urlparse
import os

url = urlparse.urlparse(os.environ['DATABASE_URL'])
dbname = url.path[1:]
user = url.username
password = url.password
host = url.hostname
port = url.port

print(f"Attempting to connect to PostgreSQL database:")
print(f"Host: {host}")
print(f"Port: {port}")
print(f"Database: {dbname}")
print(f"User: {user}")
print(f"Password: {'*' * len(password)}")

try:
    conn = psycopg2.connect(
        dbname=dbname,
        user=user,
        password=password,
        host=host,
        port=port
    )
    cursor = conn.cursor()
    cursor.execute("SELECT 1")
    cursor.close()
    conn.close()
    print("Successfully connected to the database!")
    sys.exit(0)
except psycopg2.OperationalError as e:
    print(f"Error connecting to PostgreSQL: {e}")
    sys.exit(-1)

END
}

echo "Starting database connection check..."
until postgres_ready; do
  >&2 echo 'Waiting for PostgreSQL to become available...'
  sleep 5
done
>&2 echo 'PostgreSQL is available'

exec "$@"
# #!/bin/bash

# set -o errexit
# set -o pipefail
# set -o nounset

# postgres_ready() {
# python << END
# import sys
# import psycopg2
# try:
#     psycopg2.connect(
#         dbname="${POSTGRES_DB}",
#         user="${POSTGRES_USER}",
#         password="${POSTGRES_PASSWORD}",
#         host="${POSTGRES_HOST}",
#         port="${POSTGRES_PORT}",
#     )
# except psycopg2.OperationalError:
#     sys.exit(-1)
# sys.exit(0)
# END
# }

# until postgres_ready; do
#   >&2 echo 'Waiting for PostgreSQL to become available...'
#   sleep 1
# done
# >&2 echo 'PostgreSQL is available'

# exec "$@"
