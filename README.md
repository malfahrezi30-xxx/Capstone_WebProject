# 🌐 Web Portofolio Dinamis dengan Python Flask

Capstone Project — Mata Kuliah Pengantar Pemrograman

**Nama:** Muhammad Sadam Al-Fahrezi  
**Dosen:** Pak Bayu  

---

## 📋 Deskripsi Proyek

Aplikasi web portofolio dinamis yang dibangun menggunakan Python Flask. Terdiri dari dua bagian utama:

- **Halaman Publik** — Menampilkan profil, portofolio proyek, dan form kontak
- **Dashboard Admin** — Manajemen konten (tambah/edit/hapus proyek, kelola profil & pesan)

## 🚀 Fitur Utama

- ✅ Halaman Beranda, About, Portofolio, Detail Proyek, Kontak
- ✅ Dashboard Admin dengan autentikasi Login/Logout
- ✅ CRUD Proyek (tambah, lihat, edit, hapus)
- ✅ Upload gambar proyek (PNG, JPG, JPEG, GIF, WEBP — maks 5MB)
- ✅ Manajemen Profil & Skill (dinamis dari database)
- ✅ Kotak Masuk Pesan dari form kontak
- ✅ Template inheritance dengan Jinja2
- ✅ Database SQLite via Flask-SQLAlchemy

## 🛠️ Teknologi yang Digunakan

| Komponen | Teknologi |
|----------|-----------|
| Backend | Python 3, Flask |
| Database | SQLite + Flask-SQLAlchemy |
| Template | Jinja2 |
| Frontend | HTML5, CSS3, Bootstrap 5, JavaScript |
| Version Control | Git + GitHub |

## ⚙️ Cara Instalasi & Menjalankan

### 1. Clone Repository
```bash
git clone https://github.com/malfahrezi30-xxx/Capstone_WebProject.git
cd Capstone_WebProject
```

### 2. Buat Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# atau
source venv/bin/activate  # Linux/Mac
```

### 3. Install Dependensi
```bash
pip install -r requirements.txt
```

### 4. Inisialisasi Database & Jalankan Aplikasi
```bash
python app.py
```

### 5. Buka di Browser
```
http://127.0.0.1:5000
```

## 🔐 Akun Demo Dashboard

| Field | Value |
|-------|-------|
| URL Dashboard | http://127.0.0.1:5000/dashboard |
| Username | `admin` |
| Password | `admin123` |

## 📁 Struktur Folder

```
Capstone_WebProject/
├── app.py              # Entry point Flask
├── config.py           # Konfigurasi aplikasi
├── models.py           # Model database
├── init_db.py          # Script inisialisasi data awal
├── requirements.txt    # Dependensi Python
├── .gitignore
├── README.md
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── about.html
│   ├── portfolio.html
│   ├── project_detail.html
│   ├── contact.html
│   └── dashboard/
│       ├── login.html
│       ├── index.html
│       ├── projects.html
│       ├── add_project.html
│       ├── edit_project.html
│       ├── profile.html
│       └── messages.html
└── static/
    ├── css/style.css
    ├── js/main.js
    └── uploads/
```

## 📚 Referensi

- Grinberg, M. (2018). *Flask Web Development* (2nd ed.). O'Reilly Media.
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Flask-SQLAlchemy Documentation](https://flask-sqlalchemy.palletsprojects.com/)
- [Bootstrap 5 Documentation](https://getbootstrap.com/docs/5.3/)
