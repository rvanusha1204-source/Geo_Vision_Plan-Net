"""
Reference /api/tts endpoint for the Geo Vision Plan-Net voice assistant.

Add this route to your existing Flask app (the one that already serves
/api/districts and /api/district/<slug>). It generates real native-language
speech for languages the browser's built-in speechSynthesis can't handle
(Tamil, Telugu, Malayalam, Kannada), using gTTS — free, no API key needed.

Install:
    pip install gtts

If you'd rather use a higher-quality paid engine later (Google Cloud TTS,
Azure Speech, or Sarvam.ai which specializes in Indian languages), just swap
the body of synthesize_speech() — the route contract (POST {text, lang} ->
audio/mpeg bytes) stays the same, so no frontend changes are needed.
"""

import io
from flask import Flask, request, send_file, jsonify
from gtts import gTTS

app = Flask(__name__)  # merge this into your existing Flask() instance

# Maps the 2-letter langKey the frontend sends to a gTTS-supported language code.
SUPPORTED_LANGS = {
    'ta': 'ta',  # Tamil
    'te': 'te',  # Telugu
    'ml': 'ml',  # Malayalam
    'kn': 'kn',  # Kannada
    'hi': 'hi',  # Hindi
    'en': 'en',  # English
}


@app.route('/api/tts', methods=['POST'])
def synthesize_speech():
    data = request.get_json(silent=True) or {}
    text = (data.get('text') or '').strip()
    lang = (data.get('lang') or 'en').strip().lower()

    if not text:
        return jsonify({'error': 'No text provided'}), 400

    gtts_lang = SUPPORTED_LANGS.get(lang, 'en')

    try:
        tts = gTTS(text=text, lang=gtts_lang)
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)

        return send_file(
            audio_buffer,
            mimetype='audio/mpeg',
            as_attachment=False,
            download_name='speech.mp3'
        )
    except Exception as e:
        # gTTS needs an internet connection (it calls Google Translate's TTS
        # endpoint under the hood). If your server has no outbound internet
        # access, this will fail — the frontend already falls back to the
        # local browser voice automatically in that case.
        app.logger.warning(f'TTS generation failed: {e}')
        return jsonify({'error': 'TTS generation failed'}), 500


if __name__ == '__main__':
    # Standalone test run only — in your real app, just register this route
    # on your existing Flask instance instead of running this file directly.
    app.run(port=8000, debug=True)
