import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'pm-internship-secret-key-12345')
    
    # Base directory
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    
    # Database
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'internships.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload Folder
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB limit
    
    # Ensure upload folder exists
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
