import logging, os, sys
from flask import Flask, send_from_directory
from flask_cors import CORS

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s", handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger(__name__)

from otel_setup import setup_otel
setup_otel()

import db_helper as db
db.init_db()
logger.info("[APP] DB initialised at %s", db.DB_PATH)

from ltm_routes import ltm_bp

app = Flask(__name__, static_folder="static")
CORS(app)
app.register_blueprint(ltm_bp)

@app.route("/")
def index():
    return send_from_directory(os.path.dirname(__file__), "chat_ui.html")

@app.route("/chat")
def chat():
    return send_from_directory(os.path.dirname(__file__), "chat_ui.html")

@app.route("/health")
def health():
    return {"status": "ok", "service": "ltm-chat-service"}, 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info("[APP] Starting on port %s", port)
    app.run(host="0.0.0.0", port=port, debug=False)
