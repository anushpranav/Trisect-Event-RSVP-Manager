from flask import Flask, redirect, url_for
from flask_login import LoginManager
from models import db, Organizer
from routes import routes
from reminder import init_scheduler
from config import Config
import bcrypt

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'routes.login'
    
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(Organizer, int(user_id))
    
    # Register blueprints
    app.register_blueprint(routes)
    
    # Create database tables
    with app.app_context():
        try:
            db.create_all()
            # Create admin account if it doesn't exist
            admin_email = "anushpranav@admin.com"
            admin = Organizer.query.filter_by(email=admin_email).first()
            if not admin:
                hashed_pw = bcrypt.hashpw(Config.ADMIN_PASSWORD.encode('utf-8'), bcrypt.gensalt())
                admin = Organizer(
                    name="Admin",
                    email=admin_email,
                    passwordHash=hashed_pw.decode('utf-8')
                )
                db.session.add(admin)
                db.session.commit()
        except Exception as e:
            print(f"Database initialization error: {e}")
    
    # Initialize scheduler with app context
    init_scheduler(app)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)