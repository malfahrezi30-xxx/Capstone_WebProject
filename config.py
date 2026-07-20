import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'capstone-flask-secret-key-2024'
    
    # ── Database URL ──────────────────────────────────────────────────────────
    # Vercel: set env var DATABASE_URL ke connection string PostgreSQL (Neon/Supabase)
    # Lokal : SQLite otomatis digunakan jika DATABASE_URL tidak diset
    db_url = os.environ.get('DATABASE_URL', '')
    
    # Fix skema URL untuk SQLAlchemy (Heroku/Neon kadang pakai 'postgres://')
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
    
    if db_url:
        # PostgreSQL — production (Vercel + Neon/Supabase)
        SQLALCHEMY_DATABASE_URI = db_url
    elif os.environ.get('VERCEL'):
        # Vercel tapi DATABASE_URL belum diset → fallback ephemeral SQLite
        SQLALCHEMY_DATABASE_URI = 'sqlite:////tmp/portfolio.db'
    else:
        # Lokal development → SQLite di folder instance/
        SQLALCHEMY_DATABASE_URI = 'sqlite:///portfolio.db'

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Opsi engine untuk PostgreSQL (koneksi pooling yang stabil di serverless)
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,       # Periksa koneksi sebelum dipakai
        'pool_recycle': 300,         # Recycle koneksi tiap 5 menit
        'connect_args': (
            {'sslmode': 'require'} if db_url and 'neon.tech' in db_url else {}
        ),
    }

    # ── Upload ────────────────────────────────────────────────────────────────
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # Batas 5 MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    # ── Supabase Storage (untuk upload foto di Vercel) ────────────────────────
    SUPABASE_URL = os.environ.get('SUPABASE_URL')
    SUPABASE_KEY = os.environ.get('SUPABASE_KEY') or os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
    SUPABASE_BUCKET = os.environ.get('SUPABASE_BUCKET') or 'portfolio'
    
    # ── Akun admin default (seed awal) ───────────────────────────────────────
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')
