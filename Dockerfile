FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential default-libmysqlclient-dev pkg-config curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir Flask-WTF PyMySQL cryptography

# =========================

FROM python:3.11-slim AS production

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# utilisateur sécurisé
RUN groupadd -r app_user && useradd -r -g app_user app_user

WORKDIR /app

# dépendances Python
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# code app
COPY --chown=app_user:app_user app.py auth.py users.py echeances.py \
     journal.py entreprise.py models.py extensions.py config.py forms.py ./

# variables d’environnement
ENV FLASK_ENV=production \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000

USER app_user

EXPOSE 5000

# healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

# lancement sans gunicorn
CMD ["python", "app.py"]