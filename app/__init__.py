import os
from datetime import UTC, datetime

from dotenv import load_dotenv
from flask import Flask, render_template
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from werkzeug.middleware.proxy_fix import ProxyFix

from .config import CONFIG_MAP, DevelopmentConfig

load_dotenv()

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'warning'


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    os.makedirs(app.instance_path, exist_ok=True)

    config_name = os.getenv('FLASK_ENV', os.getenv('APP_ENV', 'development')).lower()
    config_class = CONFIG_MAP.get(config_name, DevelopmentConfig)
    app.config.from_object(config_class)

    app.wsgi_app = ProxyFix(
        app.wsgi_app,
        x_for=int(os.getenv('PROXY_FIX_X_FOR', '1')),
        x_proto=int(os.getenv('PROXY_FIX_X_PROTO', '1')),
        x_host=int(os.getenv('PROXY_FIX_X_HOST', '1')),
        x_port=int(os.getenv('PROXY_FIX_X_PORT', '1')),
        x_prefix=int(os.getenv('PROXY_FIX_X_PREFIX', '1')),
    )

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    from .models import CompanySettings, User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.context_processor
    def inject_globals():
        settings = CompanySettings.query.first()
        return {
            'now': datetime.now(UTC),
            'company_settings': settings,
            'stripe_public_key': app.config.get('STRIPE_PUBLIC_KEY', ''),
            'app_env': app.config.get('ENV_NAME', 'development'),
        }

    @app.errorhandler(404)
    def not_found(_error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(_error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    from .routes.auth import auth_bp
    from .routes.main import main_bp
    from .routes.client import client_bp
    from .routes.admin import admin_bp
    from .routes.billing import billing_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(client_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(billing_bp)

    with app.app_context():
        db.create_all()
        if not CompanySettings.query.first():
            db.session.add(CompanySettings(business_name=app.config['COMPANY_NAME']))
            db.session.commit()

    register_cli(app)
    return app


def register_cli(app):
    from .models import CompanySettings, User

    @app.cli.command('seed-demo')
    def seed_demo():
        db.create_all()
        user = User.query.filter_by(email='admin@neonroo.local').first()
        if not user:
            user = User(full_name='Neon Roo Admin', email='admin@neonroo.local', phone='918-000-0000', is_admin=True)
            user.set_password('ChangeMe123!')
            db.session.add(user)
        settings = CompanySettings.query.first()
        if settings:
            settings.business_name = app.config['COMPANY_NAME']
        db.session.commit()
        print('Demo admin ready: admin@neonroo.local / ChangeMe123!')
