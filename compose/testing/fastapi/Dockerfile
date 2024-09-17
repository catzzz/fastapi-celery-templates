FROM python:3.12.0-slim-bookworm

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN apt-get update \
  && apt-get install -y build-essential libpq-dev telnet netcat-openbsd wget unzip dnsutils \
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*

# Copy the requirements file
COPY ./services/backend/requirements.txt /requirements.txt
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy the requirements.tests file
COPY ./services/backend/requirements.tests.txt /tests/requirements.txt
RUN pip install --upgrade pip && pip install --no-cache-dir -r /tests/requirements.txt

# COPY the pytest and pyproject.toml files
COPY ./pyproject.toml /pyproject.toml
COPY ./services/backend/pytest.ini /pytest.ini

# copy main backend code
COPY services/backend /app

# Copy the alembic folder to the container
COPY ./pyproject.toml /pyproject.toml

# Copy flake8 configuration file
COPY ./.flake8 /.flake8



# Add new script files
COPY ./compose/testing/fastapi/check_db_connect.sh /check_db_connect.sh

RUN chmod +x /check_db_connect.sh

WORKDIR /app
