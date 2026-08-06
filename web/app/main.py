import os
from flask import Flask
from dotenv import load_dotenv

from app.routes.auth import auth_bp
from app.routes.admin import admin_bp
from app.routes.pdv import pdv_bp
from app.routes.produtos import produtos_bp
from app.routes.loja import loja_bp

load_dotenv()


def criar_app():
    app = Flask(__name__)
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "troque-esta-chave-tambem")
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(pdv_bp)
    app.register_blueprint(produtos_bp)
    app.register_blueprint(loja_bp)
    return app


app = criar_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
