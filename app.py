from flask import Flask, redirect, url_for
from flask_login import LoginManager
from models import db, Organizer
from routes import routes
from reminder import init_scheduler
from config import Config
import bcrypt
from flask_mail import Mail
from datetime import datetime, timezone
from dotenv import load_dotenv
import os

def create_app():
    load_dotenv()  # Load environment variables at the very beginning
    
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'routes.login'

    # Initialize Flask-Mail
    mail = Mail(app)
    app.mail = mail  # Attach mail instance to app for global access
    
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(Organizer, int(user_id))
    
    # Register blueprints
    app.register_blueprint(routes)
    
    @app.context_processor
    def inject_now():
        return {'now': datetime.now(timezone.utc)}
    
    # Create database tables
    with app.app_context():
        try:
            db.create_all()
            # Create admin account if it doesn't exist, using environment variables
            admin_email = os.getenv('ADMIN_EMAIL')
            admin_password = os.getenv('ADMIN_PASSWORD')
            
            if admin_email and admin_password:
                admin = Organizer.query.filter_by(email=admin_email).first()
                if not admin:
                    hashed_pw = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt())
                    admin = Organizer(
                        name="Admin",
                        email=admin_email,
                        passwordHash=hashed_pw.decode('utf-8'),
                        is_admin=True
                    )
                    db.session.add(admin)
                    db.session.commit()
                elif not admin.is_admin:
                    # If admin exists but is not marked as admin, update them
                    admin.is_admin = True
                    db.session.commit()
        except Exception as e:
            print(f"Database initialization error: {e}")
    
    # Initialize scheduler with app context
    init_scheduler(app)
    
    GOOGLE_ANALYTICS_ID = os.getenv('GOOGLE_ANALYTICS_ID')

    @app.context_processor
    def inject_google_analytics_id():
        return dict(google_analytics_id=GOOGLE_ANALYTICS_ID)
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
