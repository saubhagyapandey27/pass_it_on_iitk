from app import create_app, db
from flask_migrate import Migrate, upgrade
import os

app = create_app()

# Run migrations on first startup only
if __name__ != '__main__' and os.environ.get('FLASK_ENV') == 'production':
    with app.app_context():
        # Check if we need to run migrations (first deployment)
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        
        try:
            # If alembic_version table doesn't exist, we need to run migrations
            if not inspector.has_table('alembic_version'):
                app.logger.info('Running database migrations...')
                upgrade()
                app.logger.info('Database migrations completed successfully')
            else:
                app.logger.info('Database already initialized, skipping migrations')
        except Exception as e:
            app.logger.error(f"Error during migration: {str(e)}")
            # If migration fails, at least create tables
            db.create_all()
            app.logger.error("Falling back to db.create_all()")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode)