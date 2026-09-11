import os
import requests
from flask import Flask, jsonify, send_from_directory
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder="jarvis_static")

ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "")
ELEVENLABS_AGENT_ID = os.environ.get("ELEVENLABS_AGENT_ID", "")


@app.route("/")
def index():
    return send_from_directory("jarvis_static", "index.html")


@app.route("/signed-url")
def signed_url():
    if not ELEVENLABS_API_KEY or not ELEVENLABS_AGENT_ID:
        return jsonify({"error": "ElevenLabs nicht konfiguriert. ELEVENLABS_API_KEY und ELEVENLABS_AGENT_ID setzen."}), 400

    resp = requests.get(
        "https://api.elevenlabs.io/v1/convai/conversation/get_signed_url",
        params={"agent_id": ELEVENLABS_AGENT_ID},
        headers={"xi-api-key": ELEVENLABS_API_KEY},
        timeout=10,
    )

    if resp.ok:
        return jsonify({"signed_url": resp.json()["signed_url"]})
    return jsonify({"error": f"ElevenLabs Fehler: {resp.status_code}"}), 500


@app.route("/config")
def config():
    return jsonify({
        "agent_id": ELEVENLABS_AGENT_ID,
        "configured": bool(ELEVENLABS_API_KEY and ELEVENLABS_AGENT_ID),
    })


if __name__ == "__main__":
    port = int(os.environ.get("JARVIS_PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
