from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import yt_dlp
import os
from pathlib import Path

app = Flask(__name__)
CORS(app)

DOWNLOAD_FOLDER = Path("downloads")
DOWNLOAD_FOLDER.mkdir(exist_ok=True)

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

    except Exception as e:
        return jsonify({"message": str(e)}), 500

    finally:
        # Nettoyage des fichiers téléchargés
        for file in DOWNLOAD_FOLDER.iterdir():
            try:
                file.unlink()
            except:
                pass

if __name__ == '__main__':
    app.run(debug=True, port=5000)