
set -o errexit
set -o pipefail
set -o nounset

echo "Checking DNS resolution for 'db' hostname..."
if ! nslookup test-db; then
    echo "Failed to resolve 'db' hostname. Check your Docker network configuration."
    exit 1
fi

postgres_ready() {
python << END
import sys
import psycopg2
import urllib.parse as urlparse
import os

dbname = os.environ['DATABASE_NAME']
user = os.environ['DATABASE_USER']
password = os.environ['DATABASE_PASSWORD']
host = os.environ['DATABASE_HOST']
port = os.environ['DATABASE_PORT']

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
