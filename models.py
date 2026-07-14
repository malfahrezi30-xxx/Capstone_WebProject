from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Project(db.Model):
    """Model untuk menyimpan data proyek portofolio."""
    __tablename__ = 'project'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    technologies = db.Column(db.String(300))  # Disimpan sebagai string, dipisah koma
    image_file = db.Column(db.String(120), default='default.jpg')
    github_link = db.Column(db.String(200))
    live_link = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def get_technologies_list(self):
        """Mengembalikan daftar teknologi sebagai list."""
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
    category = db.Column(db.String(50), default='Technical')  # Technical, Soft Skill, dll.
    level = db.Column(db.Integer, default=80)  # Level keahlian 0-100

    def __repr__(self):
        return f'<Skill {self.name}>'
