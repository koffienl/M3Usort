from flask import Flask
import os


def create_app():
    app = Flask(__name__)

    CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
    CONFIG_PATH = os.path.join(CURRENT_DIR, '..', 'config.py')
    
    config_namespace = {}
    with open(CONFIG_PATH, 'r') as file:
        exec(file.read(), {}, config_namespace)
    app.config['SECRET_KEY'] = config_namespace.get('SECRET_KEY')

    with app.app_context():
        from .routes import main_bp, init
        init()
        
        # Register blueprints
        app.register_blueprint(main_bp)

    return app
