FROM python:3.12.0-slim-bookworm

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN apt-get update \
  && apt-get install -y build-essential libpq-dev telnet netcat-openbsd wget unzip \
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*



COPY ./project/app/requirements.txt /requirements.txt
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt


COPY ./compose/local/fastapi/entrypoint.sh /entrypoint.sh
COPY ./compose/local/fastapi/start.sh /start.sh

RUN chmod +x /entrypoint.sh /start.sh

WORKDIR /app


ENTRYPOINT ["/entrypoint.sh"]
