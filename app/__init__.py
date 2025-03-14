from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from config import Config
import os
# app/__init__.py - Add security headers
from flask_talisman import Talisman 
# app/__init__.py - Add rate limiting
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging
from logging.handlers import RotatingFileHandler

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()
csrf = CSRFProtect()
# Security
talisman = Talisman()
limiter = Limiter(key_func=get_remote_address)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)  # Initialize rate limiter here

    # Initialize Cloudinary if configured
    if os.environ.get('CLOUDINARY_URL') or (
        os.environ.get('CLOUDINARY_CLOUD_NAME') and 
        os.environ.get('CLOUDINARY_API_KEY') and 
        os.environ.get('CLOUDINARY_API_SECRET')
    ):
        import cloudinary
        try:
            if os.environ.get('CLOUDINARY_URL'):
                app.logger.info('Initializing Cloudinary with CLOUDINARY_URL')
                # Let cloudinary use the URL environment variable automatically
                cloudinary.config()
            else:
                app.logger.info('Initializing Cloudinary with individual credentials')
                cloudinary.config(
                    cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
                    api_key=os.environ.get('CLOUDINARY_API_KEY'),
                    api_secret=os.environ.get('CLOUDINARY_API_SECRET')
                )
            
            # Test the Cloudinary configuration
            test_response = cloudinary.api.ping()
            app.logger.info(f'Cloudinary connection test: {test_response}')
            app.logger.info('Cloudinary initialized successfully')
        except Exception as e:
            app.logger.error(f'Cloudinary initialization failed: {str(e)}')

    # Configure Content Security Policy
    csp = {
        'default-src': '\'self\'',
        'script-src': [
            '\'self\'', 
            'https://cdn.jsdelivr.net', 
            'https://cdnjs.cloudflare.com'
        ],
        'style-src': [
            '\'self\'', 
            'https://cdn.jsdelivr.net', 
            'https://cdnjs.cloudflare.com',
            '\'unsafe-inline\''  # Allow inline styles for Bootstrap
        ],
        'img-src': [
            '\'self\'', 
            'data:',
            'https://res.cloudinary.com'  # Allow Cloudinary images
        ],
        'font-src': [
            '\'self\'', 
            'https://cdn.jsdelivr.net', 
            'https://cdnjs.cloudflare.com'
        ]
    }
    
    # Determine if we're in production environment
    is_production = os.environ.get('FLASK_ENV') == 'production'
    
    # Initialize Talisman with enhanced security settings
    talisman.init_app(
        app,
        content_security_policy=csp,
        force_https=is_production,  # Enable HTTPS in production
        session_cookie_secure=app.config.get('SESSION_COOKIE_SECURE'),
        session_cookie_http_only=app.config.get('SESSION_COOKIE_HTTPONLY'),
        session_cookie_samesite=app.config.get('SESSION_COOKIE_SAMESITE'),
        strict_transport_security=True,
        strict_transport_security_max_age=31536000,
        strict_transport_security_include_subdomains=True
    )
    
    # Set up login configuration
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    # Create upload directory if it doesn't exist
    upload_folder = os.path.join(app.static_folder, 'uploads')
    app.config['UPLOAD_FOLDER'] = upload_folder
    os.makedirs(upload_folder, exist_ok=True)

    # Register blueprints
    from app.routes import main, auth, items, requests
    app.register_blueprint(main.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(items.bp)
    app.register_blueprint(requests.bp)

    # Register admin blueprint last
    from app.routes import admin
    app.register_blueprint(admin.bp)

    # Register error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
        
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()  # In case of database error
        return render_template('errors/500.html'), 500
    
    # Set up logging (only in production)
    if not app.debug:
        if not os.path.exists('logs'):
            os.makedirs('logs', exist_ok=True)
        file_handler = RotatingFileHandler('logs/passitoniitk.log', maxBytes=10240, backupCount=5)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Pass-it-on IITK startup')

    return app

from app import models 