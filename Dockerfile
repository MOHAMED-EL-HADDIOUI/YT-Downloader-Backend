# Utiliser une image Python officielle comme base
FROM python:3.10-slim

# Installer les d�pendances syst�me n�cessaires
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# D�finir le r�pertoire de travail dans le conteneur
WORKDIR /app

# Copier les fichiers de d�pendances
COPY requirements.txt .

# Installer les d�pendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste du code source
COPY . .

# Cr�er le dossier de t�l�chargements
RUN mkdir -p downloads

# Exposer le port sur lequel l'application va tourner
EXPOSE 5000

# Variables d'environnement
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

# Commande pour lancer l'application
CMD ["flask", "run"]