FROM python:3.11-slim AS builder
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential default-libmysqlclient-dev pkg-config curl \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir gunicorn Flask-WTF PyMySQL cryptography

FROM python:3.11-slim AS production
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*
RUN groupadd -r app_user && useradd -r -g app_user app_user
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin/gunicorn /usr/local/bin/gunicorn
COPY --chown=stageboard:stageboard app.py auth.py users.py echeances.py \
     journal.py entreprise.py models.py extensions.py config.py forms.py ./
ENV FLASK_ENV=production PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
ENV PORT=5000 WORKERS=4
USER stageboard
EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1
CMD ["sh","-c","gunicorn -w ${WORKERS} -b 0.0.0.0:${PORT} app:app"]