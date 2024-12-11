from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import yt_dlp
import os
from pathlib import Path

app = Flask(__name__)
CORS(app)

# Dossier de téléchargement
DOWNLOAD_FOLDER = Path("downloads")
if not DOWNLOAD_FOLDER.exists():
    DOWNLOAD_FOLDER.mkdir(parents=True, exist_ok=True)

@app.route('/api/download', methods=['POST'])
def download():
    try:
        data = request.form
        url = data.get('url')
        format_type = data.get('format')

        if not url:
            return jsonify({"message": "URL is required"}), 400

        # Configuration de yt-dlp selon le format
        if format_type == 'audio':
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'outtmpl': str(DOWNLOAD_FOLDER / '%(title)s.%(ext)s'),
            }
        else:  # video
            ydl_opts = {
                'format': 'best',
                'outtmpl': str(DOWNLOAD_FOLDER / '%(title)s.%(ext)s'),
            }

        # Téléchargement avec yt-dlp
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

            # Ajuster l'extension pour les fichiers audio
            if format_type == 'audio':
                filename = str(Path(filename).with_suffix('.mp3'))

        # Envoi du fichier
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
