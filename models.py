from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class Project(db.Model):
    """Model untuk menyimpan data proyek portofolio."""
    __tablename__ = 'project'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    technologies = db.Column(db.String(300))
    image_file = db.Column(db.String(120), default='default.jpg')
    github_link = db.Column(db.String(200))
    live_link = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def get_technologies_list(self):
        if self.technologies:
            return [t.strip() for t in self.technologies.split(',')]
        return []

    def __repr__(self):
        return f'<Project {self.title}>'


class Message(db.Model):
    """Model untuk menyimpan pesan dari form kontak."""
    __tablename__ = 'message'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Message dari {self.name}>'


class Profile(db.Model):
    """Model untuk menyimpan data profil pemilik portofolio."""
    __tablename__ = 'profile'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, default='Nama Anda')
    headline = db.Column(db.String(200), default='Full Stack Developer')
    about = db.Column(db.Text, default='Tulis deskripsi singkat tentang diri Anda.')
    about_detail = db.Column(db.Text, default='Tulis deskripsi lengkap tentang diri Anda.')
    education = db.Column(db.Text, default='Riwayat pendidikan Anda.')
    email = db.Column(db.String(120), default='email@example.com')
    github = db.Column(db.String(200), default='https://github.com/')
    linkedin = db.Column(db.String(200), default='https://linkedin.com/in/')
    photo = db.Column(db.String(120), default='default_profile.jpg')

    def __repr__(self):
        return f'<Profile {self.name}>'


class Skill(db.Model):
    """Model untuk menyimpan daftar skill."""
    __tablename__ = 'skill'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), default='Technical')
    level = db.Column(db.Integer, default=80)

    def __repr__(self):
        return f'<Skill {self.name}>'


class Settings(db.Model):
    """Model untuk menyimpan pengaturan akun admin dan akses pembaca."""
    __tablename__ = 'settings'

    id = db.Column(db.Integer, primary_key=True)

    # Kredensial Admin
    admin_username = db.Column(db.String(50), nullable=False, default='admin')
    admin_password_hash = db.Column(db.String(256), nullable=False)
    admin_email = db.Column(db.String(120), default='')

    # Akses Pembaca (Visitor)
    reader_enabled = db.Column(db.Boolean, default=True)
    reader_password_hash = db.Column(db.String(256), nullable=False)

    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow)

    def set_admin_password(self, password):
        """Hash dan simpan password admin."""
        self.admin_password_hash = generate_password_hash(password)

    def check_admin_password(self, password):
        """Verifikasi password admin."""
        return check_password_hash(self.admin_password_hash, password)

    def set_reader_password(self, password):
        """Hash dan simpan password pembaca."""
        self.reader_password_hash = generate_password_hash(password)

    def check_reader_password(self, password):
        """Verifikasi password pembaca."""
        return check_password_hash(self.reader_password_hash, password)

    def __repr__(self):
        return f'<Settings admin={self.admin_username}>'
