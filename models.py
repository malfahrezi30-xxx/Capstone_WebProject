from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    """Model untuk menyimpan data akun user (admin portofolio)."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)

    # Pengaturan Akses Pembaca (Visitor)
    reader_enabled = db.Column(db.Boolean, default=True)
    reader_password_hash = db.Column(db.String(256), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships (cascade delete: hapus semua data terkait jika user dihapus)
    profile = db.relationship('Profile', backref='user', uselist=False, cascade="all, delete-orphan")
    projects = db.relationship('Project', backref='user', lazy=True, cascade="all, delete-orphan")
    skills = db.relationship('Skill', backref='user', lazy=True, cascade="all, delete-orphan")
    messages = db.relationship('Message', backref='user', lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        """Hash dan simpan password admin."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verifikasi password admin."""
        return check_password_hash(self.password_hash, password)

    def set_reader_password(self, password):
        """Hash dan simpan password pembaca."""
        self.reader_password_hash = generate_password_hash(password)

    def check_reader_password(self, password):
        """Verifikasi password pembaca."""
        return check_password_hash(self.reader_password_hash, password)

    # Aliases/properties untuk kompatibilitas ke belakang dengan templat settings
    @property
    def admin_username(self):
        return self.username

    @admin_username.setter
    def admin_username(self, value):
        self.username = value

    @property
    def admin_email(self):
        return self.email

    @admin_email.setter
    def admin_email(self, value):
        self.email = value

    def check_admin_password(self, password):
        return self.check_password(password)

    def set_admin_password(self, password):
        self.set_password(password)

    def __repr__(self):
        return f'<User {self.username}>'


class Project(db.Model):
    """Model untuk menyimpan data proyek portofolio."""
    __tablename__ = 'project'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
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
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
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
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
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
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), default='Technical')
    level = db.Column(db.Integer, default=80)

    def __repr__(self):
        return f'<Skill {self.name}>'
