from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

db = SQLAlchemy()
login_manager = LoginManager()

def create_app(config_name='default'):
    app = Flask(__name__)

    from config import config
    app.config.from_object(config[config_name])

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    # Ensure models directory exists
    models_dir = os.path.join(os.path.dirname(__file__), 'ml', 'models')
    os.makedirs(models_dir, exist_ok=True)

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.predict import predict_bp
    from app.routes.simulation import simulation_bp
    from app.routes.dashboard import dashboard_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(predict_bp)
    app.register_blueprint(simulation_bp)
    app.register_blueprint(dashboard_bp)

    with app.app_context():
        db.create_all()
        # Seed default data if needed
        from app.models import seed_defaults
        seed_defaults()

    return app
