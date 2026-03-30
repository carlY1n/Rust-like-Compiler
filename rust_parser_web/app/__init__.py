from flask import Flask
import os

def create_app():
    app = Flask(__name__)
    app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'app', 'uploads')
    app.secret_key = 'secret-key'

    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app
