from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import yt_dlp
import os
from pathlib import Path
import requests
import signal
import functools

app = Flask(__name__)
CORS(app)

# Dossier de téléchargement
DOWNLOAD_FOLDER = Path("downloads")
if not DOWNLOAD_FOLDER.exists():
    DOWNLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

def timeout(seconds):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            def handler(signum, frame):
                raise TimeoutError(f"Function call timed out after {seconds} seconds")

            # Set the signal handler and a timeout
            signal.signal(signal.SIGALRM, handler)
            signal.alarm(seconds)
            try:
                result = func(*args, **kwargs)
            finally:
                # Cancel the alarm
                signal.alarm(0)
            return result
        return wrapper
    return decorator

@app.route('/api/download', methods=['POST'])
@timeout(60)  # 60 seconds timeout
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
        
        # Configuration avancée de yt-dlp pour contourner les restrictions
        ydl_opts = {
            'format': 'bestaudio/best' if format_type == 'audio' else 'best',
            'outtmpl': str(DOWNLOAD_FOLDER / '%(title)s.%(ext)s'),
            'nooverwrites': True,
            'no_warnings': True,
            'ignoreerrors': False,
            'no_color': True,
            'age_limit': 99,
            'socket_timeout': 30,  # Timeout for network operations
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://www.youtube.com/',
            },
            'retries': 3,
            'fragment_retries': 3,
            'retry_sleep': 5,
        }
        
        # Configuration spécifique pour l'audio
        if format_type == 'audio':
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        
        # Attempt to download with yt-dlp
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # First, extract video info to check availability
            info_dict = ydl.extract_info(url, download=False)
            
            # If video is available, proceed with download
            ydl.download([url])
            
            # Prepare filename
            filename = ydl.prepare_filename(info_dict)
            
            # Adjust extension for audio
            if format_type == 'audio':
                filename = str(Path(filename).with_suffix('.mp3'))
        
        # Envoi du fichier téléchargé
        return send_file(
            filename,
            as_attachment=True,
            download_name=os.path.basename(filename)
        )
    
    except TimeoutError:
        return jsonify({"message": "Download timed out. Please try again."}), 504
    
    except yt_dlp.DownloadError as e:
        return jsonify({"message": f"Download error: {str(e)}"}), 500
    
    except Exception as e:
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500
    
    finally:
        # Nettoyage des fichiers téléchargés
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
