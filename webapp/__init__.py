"""Fábrica da aplicação Flask - Controle de Certificados Digitais."""
import os

from flask import Flask

try:  # opcional: carrega variáveis de um arquivo .env, se python-dotenv estiver instalado
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from src import db


def create_app() -> Flask:
    app = Flask(__name__)
    app.secret_key = os.environ.get("APP_SECRET_KEY") or os.urandom(24)
    app.jinja_env.trim_blocks = True
    app.jinja_env.lstrip_blocks = True

    db.init_db()

    from webapp.routes_dashboard import bp as dashboard_bp
    from webapp.routes_certificados import bp as certificados_bp
    from webapp.routes_mensagens import bp as mensagens_bp
    from webapp.routes_config import bp as config_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(certificados_bp)
    app.register_blueprint(mensagens_bp)
    app.register_blueprint(config_bp)

    from src.domain import formatar_data_br

    @app.template_filter("br_date")
    def _br_date(value):
        return formatar_data_br(value) if value else "-"

    from src.domain import badge_class

    @app.template_filter("badge_class")
    def _badge_class(situacao):
        return badge_class(situacao)

    from src.domain import formatar_documento

    @app.template_filter("documento")
    def _documento(value):
        return formatar_documento(value) if value else "-"

    @app.context_processor
    def inject_globals():
        return dict(cfg=db.get_all_config())

    from webapp.icons import icon
    app.jinja_env.globals["icon"] = icon

    return app
