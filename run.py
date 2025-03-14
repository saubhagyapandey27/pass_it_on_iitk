from app import create_app, db
from flask_migrate import Migrate, upgrade
import os

app = create_app()

# Run migrations on startup in production
if __name__ != '__main__' and os.environ.get('FLASK_ENV') == 'production':
    with app.app_context():
        # Check if we need to run migrations (first deployment)
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        
        try:
            # First create any missing tables
            app.logger.info('Creating any missing database tables...')
            db.create_all()
            
            # Then apply migrations to ensure proper structure
            app.logger.info('Running database migrations...')
            upgrade()
            
            app.logger.info('Database initialization completed successfully')
        except Exception as e:
            app.logger.error(f"Error during database initialization: {str(e)}")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode)