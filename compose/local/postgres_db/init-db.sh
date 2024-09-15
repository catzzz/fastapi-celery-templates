#!/bin/bash
set -e

# Function to check if database exists
database_exists() {
    psql -U "$POSTGRES_USER" -lqt | cut -d \| -f 1 | grep -qw "$1"
}

# Wait for PostgreSQL to start
until pg_isready -U "$POSTGRES_USER"; do
    echo "Waiting for PostgreSQL to start..."
    sleep 2
done

# Check if sample_db exists, if not create it
if ! database_exists "$POSTGRES_DB"; then
    echo "Database $POSTGRES_DB does not exist. Creating..."
    createdb -U "$POSTGRES_USER" "$POSTGRES_DB"
    echo "Database $POSTGRES_DB created."
else
    echo "Database $POSTGRES_DB already exists."
fi

# You can add additional initialization logic here if needed
