import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.urandom(24)
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')
    
    # Reminder settings
    REMINDER_DAYS_BEFORE = [7, 3, 1]  # Send reminders 7, 3, and 1 days before event
    
    # QR Code settings
    QR_CODE_VERSION = 1
    QR_CODE_BOX_SIZE = 10
    QR_CODE_BORDER = 4
    
    # File upload settings
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size