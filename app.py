from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import yt_dlp
import os
from pathlib import Path
import browser_cookie3  # Additional library for cookie extraction

app = Flask(__name__)
CORS(app)

# Dossier de téléchargement
DOWNLOAD_FOLDER = Path("downloads")
if not DOWNLOAD_FOLDER.exists():
    DOWNLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

@app.route('/api/download', methods=['POST'])
def download():
    try:
        # Récupération des données JSON envoyées dans le corps de la requête
        data = request.get_json()
        # Validation des paramètres reçus
        url = data.get('url')
        format_type = data.get('format')
        if not url:
            return jsonify({"message": "URL is required"}), 400
        if not format_type:
            return jsonify({"message": "Format type is required"}), 400
        
        # Configuration des cookies - essayez différents navigateurs
        try:
            # Essayez de récupérer les cookies de Chrome
            cookies = browser_cookie3.chrome(domain_name='.youtube.com')
        except Exception:
            try:
                # Si Chrome échoue, essayez Firefox
                cookies = browser_cookie3.firefox(domain_name='.youtube.com')
            except Exception:
                # Si aucun cookie n'est trouvé, utilisez une configuration alternative
                cookies = None
        
        # Configuration de yt-dlp selon le format
        ydl_opts = {
            'format': 'bestaudio/best' if format_type == 'audio' else 'best',
            'outtmpl': str(DOWNLOAD_FOLDER / '%(title)s.%(ext)s'),
        }
        
        # Configuration spécifique pour l'audio
        if format_type == 'audio':
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        
        # Ajouter les cookies s'ils sont disponibles
        if cookies:
            ydl_opts['cookiefile'] = str(DOWNLOAD_FOLDER / 'cookies.txt')
            # Écrire les cookies dans un fichier temporaire
            with open(ydl_opts['cookiefile'], 'w') as f:
                for cookie in cookies:
                    f.write(f"{cookie.domain}\t{str(cookie.domain_specified).upper()}\t{cookie.path}\t{str(cookie.secure).upper()}\t{cookie.expires or 0}\t{cookie.name}\t{cookie.value}\n")
        
        # Téléchargement avec yt-dlp
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # Ajuster l'extension pour les fichiers audio
            if format_type == 'audio':
                filename = str(Path(filename).with_suffix('.mp3'))
        
        # Envoi du fichier téléchargé
        return send_file(
            filename,
            as_attachment=True,
            download_name=os.path.basename(filename)
        )
    
    except yt_dlp.DownloadError as e:
        return jsonify({"message": f"Download error: {str(e)}"}), 500
    
    except Exception as e:
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500
    
    finally:
        # Nettoyage des fichiers téléchargés et des cookies
        for file in DOWNLOAD_FOLDER.iterdir():
            try:
                file.unlink()
            except Exception:
                pass

if __name__ == '__main__':
    # Port et mode de débogage à partir des variables d'environnement
    port = int(os.environ.get("PORT", 5000)) 
    debug_mode = os.environ.get("DEBUG", "False").lower() in ("true", "1")
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
