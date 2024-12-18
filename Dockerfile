# Utiliser une image Python officielle comme base
FROM python:3.10-slim

# Installer les dépendances système nécessaires
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Copier les fichiers de dépendances
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste du code source
COPY . .

# Créer le dossier de téléchargements
RUN mkdir -p downloads

# Exposer le port sur lequel l'application va tourner
EXPOSE 5000

# Variables d'environnement
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

# Commande pour lancer l'application
CMD ["flask", "run"]