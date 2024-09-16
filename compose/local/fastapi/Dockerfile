FROM python:3.12.0-slim-bookworm

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN apt-get update \
  && apt-get install -y build-essential libpq-dev telnet netcat-openbsd wget unzip dnsutils \
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*




COPY ./services/backend/requirements.txt /requirements.txt
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt


# copy main backend code
COPY services/backend /app

# Copy the alembic folder to the container

# FastAPI
COPY ./compose/local/fastapi/entrypoint.sh /entrypoint.sh
COPY ./compose/local/fastapi/start.sh /start.sh
RUN chmod +x /entrypoint.sh /start.sh

# Celery worker
COPY ./compose/local/fastapi/celery/worker/start.sh /start-celeryworker.sh
RUN chmod +x /start-celeryworker.sh

# Celery beat
COPY ./compose/local/fastapi/celery/beat/start.sh /start-celerybeat.sh
RUN chmod +x /start-celerybeat.sh

WORKDIR /app


ENTRYPOINT ["/entrypoint.sh"]
