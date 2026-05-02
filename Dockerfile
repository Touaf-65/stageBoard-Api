# ============================================================
# [BACKEND] stageBoard-Api — Dockerfile
# ============================================================
 
# ── Étape 1 : Build des dépendances ──────────────────────────
FROM python:3.11-slim AS builder
 
WORKDIR /app
 
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential default-libmysqlclient-dev pkg-config curl \
    && rm -rf /var/lib/apt/lists/*
 
COPY requirements.txt .
 
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir Flask-WTF PyMySQL cryptography gunicorn
 
# ── Étape 2 : Image de production ────────────────────────────
FROM python:3.11-slim AS production
 
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*
 
# Utilisateur non-root sécurisé
RUN groupadd -r appuser && useradd -r -g appuser appuser
 
WORKDIR /app
 
# Copier uniquement les dépendances compilées
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin/gunicorn /usr/local/bin/gunicorn
 
# Copier le code source
COPY --chown=appuser:appuser app.py auth.py users.py echeances.py \
    journal.py entreprise.py models.py extensions.py config.py forms.py ./
 
# Variables d'environnement
ENV FLASK_ENV=production \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000

RUN mkdir -p /home/appuser && chown appuser:appuser /home/appuser
USER appuser
 
EXPOSE 5000
 
# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1
 
#  Lancement avec Gunicorn (remplace python app.py)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "app:app"]
#CMD ["gunicorn", "--worker-tmp-dir", "/dev/shm", "--bind", "0.0.0.0:5000", "app:app"]