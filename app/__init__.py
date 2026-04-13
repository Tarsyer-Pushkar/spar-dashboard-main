import os
from flask import Flask
from dotenv import load_dotenv
from .db import init_db

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", "change-me-in-production")

    init_db(app)

    @app.context_processor
    def inject_stores():
        import json
        stores_file = os.path.join(app.root_path, '..', 'stores.json')
        try:
            with open(stores_file, 'r') as f:
                stores = json.load(f)
        except Exception:
            stores = []
        return dict(stores=stores)

    from .routes.auth import auth_bp
    from .routes.dashboard import dashboard_bp
    from .routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    return app
