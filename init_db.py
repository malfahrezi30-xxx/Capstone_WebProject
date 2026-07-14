"""
Script untuk menginisialisasi database dengan data awal (seed data).
Jalankan: python init_db.py
"""

import os
import sys

# Pastikan path project sudah benar
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Project, Message, Profile, Skill


def init_database():
    """Membuat tabel dan mengisi data awal."""
    with app.app_context():
        # Buat semua tabel
        db.create_all()
        print("[OK] Tabel database berhasil dibuat.")

        # ─── Profil ───────────────────────────────────────────────
        if not Profile.query.first():
            profile = Profile(
                name='Muhammad Sadam Al-Fahrezi',
                headline='Mahasiswa Teknik Informatika | Python & Web Developer',
                about='Halo! Saya mahasiswa yang antusias dalam dunia pemrograman web dan pengembangan aplikasi menggunakan Python.',
                about_detail=(
                    'Saya adalah mahasiswa Teknik Informatika yang memiliki passion dalam '
                    'pengembangan web menggunakan Python dan Flask. Saya senang membangun '
                    'aplikasi yang fungsional, bersih, dan mudah digunakan. '
                    'Selain coding, saya juga tertarik dengan desain UI/UX dan pengembangan database. '
                    'Saya percaya bahwa teknologi dapat membantu memecahkan masalah nyata di masyarakat.'
                ),
                education=(
                    'S1 Teknik Informatika\n'
                    'Universitas — 2023 s/d sekarang\n'
                    'Fokus: Pengembangan Web, Algoritma, dan Basis Data'
                ),
                email='m.alfahrezi30@gmail.com',
                github='https://github.com/malfahrezi30-xxx',
                linkedin='https://linkedin.com/in/'
            )
            db.session.add(profile)
            print("[OK] Profil default berhasil dibuat.")

        # ─── Skills ───────────────────────────────────────────────
        if not Skill.query.first():
            skills_data = [
                # Technical
                {'name': 'Python',       'category': 'Technical',  'level': 85},
                {'name': 'Flask',        'category': 'Framework',  'level': 80},
                {'name': 'HTML5',        'category': 'Technical',  'level': 90},
                {'name': 'CSS3',         'category': 'Technical',  'level': 80},
                {'name': 'JavaScript',   'category': 'Technical',  'level': 75},
                {'name': 'Bootstrap',    'category': 'Framework',  'level': 85},
                # Database
                {'name': 'SQLite',       'category': 'Database',   'level': 80},
                {'name': 'SQLAlchemy',   'category': 'Framework',  'level': 75},
                # Tools
                {'name': 'Git & GitHub', 'category': 'Tools',      'level': 80},
                {'name': 'VS Code',      'category': 'Tools',      'level': 90},
                # Soft Skills
                {'name': 'Problem Solving', 'category': 'Soft Skill', 'level': 85},
                {'name': 'Teamwork',     'category': 'Soft Skill', 'level': 88},
            ]
            for s in skills_data:
                db.session.add(Skill(**s))
            print(f"[OK] {len(skills_data)} skill berhasil ditambahkan.")

        # ─── Proyek Demo ──────────────────────────────────────────
        if not Project.query.first():
            projects_data = [
                {
                    'title': 'Web Portfolio Dinamis dengan Flask',
                    'description': (
                        'Aplikasi web portofolio yang dibangun menggunakan Python Flask. '
                        'Fitur utama meliputi halaman publik (Home, About, Portfolio, Kontak) '
                        'dan dashboard admin dengan CRUD proyek, manajemen profil & skill, '
                        'upload gambar, serta kotak masuk pesan. '
                        'Database menggunakan SQLite via Flask-SQLAlchemy.'
                    ),
                    'technologies': 'Python, Flask, SQLite, Flask-SQLAlchemy, Jinja2, Bootstrap 5, JavaScript',
                    'github_link': 'https://github.com/malfahrezi30-xxx/Capstone_WebProject',
                    'live_link': '',
                },
                {
                    'title': 'Sistem Manajemen Nilai Mahasiswa',
                    'description': (
                        'Aplikasi CLI berbasis Python untuk mengelola data nilai mahasiswa. '
                        'Dapat menambah, mengedit, menghapus, dan menampilkan data nilai. '
                        'Data disimpan dalam format JSON. Menggunakan konsep OOP dan '
                        'struktur data list dan dictionary.'
                    ),
                    'technologies': 'Python, JSON, OOP',
                    'github_link': '',
                    'live_link': '',
                },
                {
                    'title': 'Kalkulator Sederhana dengan Tkinter',
                    'description': (
                        'Aplikasi kalkulator desktop menggunakan Python Tkinter. '
                        'Mendukung operasi dasar: penjumlahan, pengurangan, perkalian, dan pembagian. '
                        'Antarmuka grafis yang user-friendly dengan tombol yang responsif.'
                    ),
                    'technologies': 'Python, Tkinter, GUI',
                    'github_link': '',
                    'live_link': '',
                },
            ]
            for p in projects_data:
                db.session.add(Project(**p))
            print(f"[OK] {len(projects_data)} proyek demo berhasil ditambahkan.")

        # ─── Pesan Demo ───────────────────────────────────────────
        if not Message.query.first():
            messages_data = [
                {
                    'name': 'Pak Bayu',
                    'email': 'bayu@kampus.ac.id',
                    'message': 'Proyek capstone Anda terlihat menarik! Saya akan menguji fitur dashboard-nya.',
                    'is_read': False,
                },
                {
                    'name': 'Teman Kuliah',
                    'email': 'teman@email.com',
                    'message': 'Wah keren banget portofolionya! Bisa ajarin caranya?',
                    'is_read': True,
                },
            ]
            for m in messages_data:
                db.session.add(Message(**m))
            print(f"[OK] {len(messages_data)} pesan demo berhasil ditambahkan.")

        db.session.commit()
        print("\n[DONE] Database berhasil diinisialisasi!")
        print("   Username : admin")
        print("   Password : admin123")
        print("   URL      : http://127.0.0.1:5000")
        print("   Dashboard: http://127.0.0.1:5000/login\n")


if __name__ == '__main__':
    # Buat folder uploads jika belum ada
    uploads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               'static', 'uploads')
    os.makedirs(uploads_dir, exist_ok=True)
    init_database()
