# Use the official PostgreSQL 16 image as a parent image
FROM postgres:16-alpine

# Set environment variables
ENV POSTGRES_DB=sample_db
ENV POSTGRES_USER=admin
ENV POSTGRES_PASSWORD=password

# Copy the initialization script into the container
COPY ./compose/local/postgres_db/init-db.sh /docker-entrypoint-initdb.d/

# Give execution rights on the script
RUN chmod +x /docker-entrypoint-initdb.d/init-db.sh
