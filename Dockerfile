FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PROJECT_DIR=/usr/local/app \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

WORKDIR ${PROJECT_DIR}

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      build-essential \
      gcc \
      libpq-dev \
      fish \
      curl \
      ca-certificates && \
    python -m pip install --upgrade pip setuptools wheel && \
    pip install pipenv && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY Pipfile Pipfile.lock ./

RUN pipenv install --deploy --system --verbose

COPY . .

RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app ${PROJECT_DIR}

USER app

EXPOSE 8080
CMD ["gunicorn", "ahelp.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
