import os
import logging
from pathlib import Path
import uuid

from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import yt_dlp

# Configuration de l'application
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Configuration du logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Dossiers de travail
BASE_DIR = Path(__file__).resolve().parent
DOWNLOAD_FOLDER = BASE_DIR / 'downloads'
DOWNLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

def clean_filename(filename):
    """Nettoie le nom de fichier pour éviter les caractères problématiques"""
    return "".join(c for c in filename if c.isalnum() or c in (' ', '.', '_', '-')).rstrip()

@app.route('/api/download', methods=['POST'])
def download_youtube():
    try:
        # Récupération des données
        data = request.get_json()
        logger.info(f"Données reçues : {data}")

        url = data.get('url', '').strip()
        format_type = data.get('format', 'audio')

        # Validation de l'URL
        if not url:
            return jsonify({"message": "URL est requise"}), 400

        # Configuration de yt-dlp
        unique_id = str(uuid.uuid4())[:8]
        output_template = str(DOWNLOAD_FOLDER / f"{unique_id}_%(title)s.%(ext)s")

        # Configuration des options yt-dlp
        ydl_opts = {
            'nooverwrites': True,
            'no_warnings': True,
            'ignoreerrors': False,
            'no_color': True,
            'age_limit': 99,
            'outtmpl': output_template,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
            },
        }

        # Configuration spécifique selon le format
        if format_type == 'audio':
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
            })
        else:  # video
            ydl_opts.update({
                # Sélectionner le meilleur format vidéo disponible
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'merge_output_format': 'mp4',
            })

        # Téléchargement
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.info(f"Tentative de téléchargement : {url}")
            
            # Vérifier les informations du format
            info_dict = ydl.extract_info(url, download=False)
            
            # Télécharger
            ydl.download([url])
            
            # Récupération du nom de fichier
            if 'entries' in info_dict:
                # Playlist ou plusieurs vidéos
                filename = ydl.prepare_filename(info_dict['entries'][0])
            else:
                filename = ydl.prepare_filename(info_dict)

            # Ajustement de l'extension
            if format_type == 'audio':
                filename = str(Path(filename).with_suffix('.mp3'))
            else:
                filename = str(Path(filename).with_suffix('.mp4'))

        # Nettoyer le nom de fichier
        safe_filename = clean_filename(os.path.basename(filename))
        full_path = str(Path(filename))

        logger.info(f"Téléchargement réussi : {safe_filename}")

        # Envoi du fichier
        return send_file(
            full_path, 
            as_attachment=True, 
            download_name=safe_filename
        )

    except yt_dlp.utils.DownloadError as e:
        logger.error(f"Erreur de téléchargement : {e}", exc_info=True)
        return jsonify({"message": f"Impossible de télécharger : {str(e)}"}), 400

    except Exception as e:
        logger.error(f"Erreur complète : {e}", exc_info=True)
        return jsonify({"message": f"Erreur serveur : {str(e)}"}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Point de contrôle de santé de l'application"""
    return jsonify({
        "status": "healthy", 
        "version": "1.0.0"
    }), 200

if __name__ == '__main__':
    # Configuration du serveur
    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.environ.get("DEBUG", "False").lower() in ("true", "1")
    
    logger.info(f"Démarrage du serveur sur le port {port}")
    app.run(host="0.0.0.0", port=port, debug=debug_mode)