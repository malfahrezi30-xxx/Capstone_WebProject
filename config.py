import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'capstone-flask-secret-key-2024'
    
    # Handle PostgreSQL URL scheme change for SQLAlchemy 1.4+
    db_url = os.environ.get('DATABASE_URL')
    if db_url and db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
        
    # Jika dijalankan di Vercel dan DATABASE_URL tidak diset, gunakan /tmp/portfolio.db
    # agar tidak error karena filesystem read-only.
    if os.environ.get('VERCEL') and not db_url:
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join('/tmp', 'portfolio.db')
    else:
        SQLALCHEMY_DATABASE_URI = db_url or 'sqlite:///portfolio.db'
        
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # Batas 5 MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    # Supabase credentials (for Vercel deployment)
    SUPABASE_URL = os.environ.get('SUPABASE_URL')
    SUPABASE_KEY = os.environ.get('SUPABASE_KEY') or os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
    SUPABASE_BUCKET = os.environ.get('SUPABASE_BUCKET') or 'portfolio'
    
    # Akun admin default
    ADMIN_USERNAME = 'admin'
    ADMIN_PASSWORD = 'admin123'
