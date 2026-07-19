import os
import time
from functools import wraps
import requests
# pyrefly: ignore [missing-import]
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort  # type: ignore[import]
# pyrefly: ignore [missing-import]
from werkzeug.utils import secure_filename  # type: ignore[import]
from config import Config
from models import db, Project, Message, Profile, Skill, Settings

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)


# ─────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────

def allowed_file(filename):
    """Memeriksa apakah ekstensi file diperbolehkan."""
    return ('.' in filename and
            filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS'])


def get_settings():
    """Ambil settings dari DB, buat default jika belum ada."""
    s = Settings.query.first()
    if not s:
        s = Settings()
        s.set_admin_password(app.config.get('ADMIN_PASSWORD', 'admin123'))
        s.admin_username = app.config.get('ADMIN_USERNAME', 'admin')
        s.set_reader_password('visitor123')
        db.session.add(s)
        db.session.commit()
    return s


def login_required(f):
    """Decorator: wajib login (admin atau pembaca)."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'logged_in' not in session:
            flash('Silakan login terlebih dahulu.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """Decorator: hanya admin yang boleh akses (untuk dashboard)."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'logged_in' not in session:
            flash('Silakan login terlebih dahulu.', 'warning')
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            flash('Akses ditolak. Halaman ini hanya untuk Admin.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated


def save_uploaded_file(file, old_filename=None):
    """Menyimpan file upload (ke Supabase jika terkonfigurasi, fallback ke lokal jika tidak)."""
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        filename = f"{name}_{int(time.time())}{ext}"
        
        # Cek konfigurasi Supabase
        supabase_url = app.config.get('SUPABASE_URL')
        supabase_key = app.config.get('SUPABASE_KEY')
        supabase_bucket = app.config.get('SUPABASE_BUCKET', 'portfolio')
        
        if supabase_url and supabase_key:
            supabase_url = supabase_url.rstrip('/')
            upload_url = f"{supabase_url}/storage/v1/object/{supabase_bucket}/{filename}"
            headers = {
                "Authorization": f"Bearer {supabase_key}",
                "Content-Type": file.content_type
            }
            try:
                file.seek(0)
                file_data = file.read()
                response = requests.post(upload_url, headers=headers, data=file_data, timeout=15)
                if response.status_code == 200:
                    # Kembalikan URL publik Supabase langsung
                    public_url = f"{supabase_url}/storage/v1/object/public/{supabase_bucket}/{filename}"
                    return public_url
                else:
                    app.logger.error(f"Supabase upload failed: {response.status_code} - {response.text}")
            except Exception as e:
                app.logger.error(f"Supabase upload exception: {e}")
        
        # Fallback ke penyimpanan lokal
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        file.seek(0)
        file.save(upload_path)
        
        if old_filename and old_filename not in ('default.jpg', 'default_profile.jpg'):
            if not old_filename.startswith('http'):
                old_path = os.path.join(app.config['UPLOAD_FOLDER'], old_filename)
                if os.path.exists(old_path):
                    os.remove(old_path)
        return filename
    return None


# ─────────────────────────────────────────────
# CONTEXT PROCESSOR
# ─────────────────────────────────────────────

@app.context_processor
def inject_globals():
    profile = Profile.query.first()
    unread_count = Message.query.filter_by(is_read=False).count()
    is_admin = session.get('role') == 'admin'
    user_role = session.get('role', None)
    
    def get_upload_url(filename):
        if not filename:
            return ""
        if filename.startswith('http://') or filename.startswith('https://'):
            return filename
        return url_for('static', filename='uploads/' + filename)
        
    return dict(profile=profile, unread_count=unread_count,
                is_admin=is_admin, user_role=user_role, get_upload_url=get_upload_url)


# ─────────────────────────────────────────────
# HALAMAN PUBLIK (wajib login)
# ─────────────────────────────────────────────

@app.route('/')
def index():
    """Beranda — wajib login (admin atau pembaca)."""
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    profile = Profile.query.first()
    projects = Project.query.order_by(Project.created_at.desc()).limit(3).all()
    skills = Skill.query.all()
    return render_template('index.html', profile=profile,
                           projects=projects, skills=skills)


@app.route('/about')
@login_required
def about():
    """Halaman About."""
    profile = Profile.query.first()
    skills = Skill.query.all()
    skills_by_category = {}
    for skill in skills:
        cat = skill.category or 'Technical'
        if cat not in skills_by_category:
            skills_by_category[cat] = []
        skills_by_category[cat].append(skill)
    return render_template('about.html', profile=profile,
                           skills_by_category=skills_by_category)


@app.route('/portfolio')
@login_required
def portfolio():
    """Halaman daftar semua proyek portofolio."""
    projects = Project.query.order_by(Project.created_at.desc()).all()
    return render_template('portfolio.html', projects=projects)


@app.route('/portfolio/<int:project_id>')
@login_required
def project_detail(project_id):
    """Halaman detail sebuah proyek."""
    project = Project.query.get_or_404(project_id)
    other_projects = Project.query.filter(
        Project.id != project_id
    ).order_by(Project.created_at.desc()).limit(3).all()
    return render_template('project_detail.html',
                           project=project, other_projects=other_projects)


@app.route('/contact', methods=['GET', 'POST'])
@login_required
def contact():
    """Halaman kontak."""
    profile = Profile.query.first()
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        message_text = request.form.get('message', '').strip()
        if not name or not email or not message_text:
            flash('Semua field wajib diisi!', 'danger')
        else:
            msg = Message(name=name, email=email, message=message_text)
            db.session.add(msg)
            db.session.commit()
            flash('Pesan berhasil dikirim! Terima kasih.', 'success')
            return redirect(url_for('contact'))
    return render_template('contact.html', profile=profile)


# ─────────────────────────────────────────────
# AUTENTIKASI
# ─────────────────────────────────────────────

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Halaman login — entry point utama."""
    if 'logged_in' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        login_type = request.form.get('login_type', 'admin')
        password = request.form.get('password', '').strip()
        settings = get_settings()

        if login_type == 'admin':
            username = request.form.get('username', '').strip()
            if (username == settings.admin_username and
                    settings.check_admin_password(password)):
                session['logged_in'] = True
                session['username'] = username
                session['role'] = 'admin'
                flash(f'Selamat datang kembali, {username}!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Username atau password admin salah!', 'danger')

        elif login_type == 'reader':
            if not settings.reader_enabled:
                flash('Akses pembaca sedang dinonaktifkan oleh admin.', 'warning')
            elif settings.check_reader_password(password):
                session['logged_in'] = True
                session['username'] = 'Pembaca'
                session['role'] = 'reader'
                flash('Selamat datang! Anda masuk sebagai Pembaca.', 'success')
                return redirect(url_for('index'))
            else:
                flash('Password pembaca salah!', 'danger')

    return render_template('dashboard/login.html')


@app.route('/logout')
def logout():
    """Logout dari session."""
    username = session.get('username', 'Pengguna')
    role = session.get('role', 'reader')
    session.clear()
    if role == 'admin':
        flash(f'Sampai jumpa, {username}! Anda telah logout.', 'info')
    else:
        flash('Anda telah keluar. Sampai jumpa!', 'info')
    return redirect(url_for('login'))


# ─────────────────────────────────────────────
# DASHBOARD — UTAMA (admin only)
# ─────────────────────────────────────────────

@app.route('/dashboard')
@admin_required
def dashboard_index():
    total_projects = Project.query.count()
    total_messages = Message.query.count()
    unread_messages = Message.query.filter_by(is_read=False).count()
    recent_messages = Message.query.order_by(
        Message.created_at.desc()).limit(5).all()
    recent_projects = Project.query.order_by(
        Project.created_at.desc()).limit(5).all()
    return render_template('dashboard/index.html',
                           total_projects=total_projects,
                           total_messages=total_messages,
                           unread_messages=unread_messages,
                           recent_messages=recent_messages,
                           recent_projects=recent_projects)


# ─────────────────────────────────────────────
# DASHBOARD — MANAJEMEN PROYEK (CRUD)
# ─────────────────────────────────────────────

@app.route('/dashboard/projects')
@admin_required
def dashboard_projects():
    projects = Project.query.order_by(Project.created_at.desc()).all()
    return render_template('dashboard/projects.html', projects=projects)


@app.route('/dashboard/projects/add', methods=['GET', 'POST'])
@admin_required
def add_project():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        technologies = request.form.get('technologies', '').strip()
        github_link = request.form.get('github_link', '').strip()
        live_link = request.form.get('live_link', '').strip()
        if not title or not description:
            flash('Judul dan deskripsi wajib diisi!', 'danger')
            return render_template('dashboard/add_project.html')
        image_filename = 'default.jpg'
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                saved = save_uploaded_file(file)
                if saved:
                    image_filename = saved
                else:
                    flash('Format file tidak diizinkan!', 'danger')
                    return render_template('dashboard/add_project.html')
        project = Project(title=title, description=description,
                          technologies=technologies, image_file=image_filename,
                          github_link=github_link, live_link=live_link)
        db.session.add(project)
        db.session.commit()
        flash(f'Proyek "{title}" berhasil ditambahkan!', 'success')
        return redirect(url_for('dashboard_projects'))
    return render_template('dashboard/add_project.html')


@app.route('/dashboard/projects/edit/<int:project_id>', methods=['GET', 'POST'])
@admin_required
def edit_project(project_id):
    project = Project.query.get_or_404(project_id)
    if request.method == 'POST':
        project.title = request.form.get('title', '').strip()
        project.description = request.form.get('description', '').strip()
        project.technologies = request.form.get('technologies', '').strip()
        project.github_link = request.form.get('github_link', '').strip()
        project.live_link = request.form.get('live_link', '').strip()
        if not project.title or not project.description:
            flash('Judul dan deskripsi wajib diisi!', 'danger')
            return render_template('dashboard/edit_project.html', project=project)
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                saved = save_uploaded_file(file, old_filename=project.image_file)
                if saved:
                    project.image_file = saved
                else:
                    flash('Format file tidak diizinkan!', 'danger')
                    return render_template('dashboard/edit_project.html', project=project)
        db.session.commit()
        flash(f'Proyek "{project.title}" berhasil diperbarui!', 'success')
        return redirect(url_for('dashboard_projects'))
    return render_template('dashboard/edit_project.html', project=project)


@app.route('/dashboard/projects/delete/<int:project_id>', methods=['POST'])
@admin_required
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    title = project.title
    if project.image_file and project.image_file != 'default.jpg':
        img_path = os.path.join(app.config['UPLOAD_FOLDER'], project.image_file)
        if os.path.exists(img_path):
            os.remove(img_path)
    db.session.delete(project)
    db.session.commit()
    flash(f'Proyek "{title}" berhasil dihapus.', 'success')
    return redirect(url_for('dashboard_projects'))


# ─────────────────────────────────────────────
# DASHBOARD — MANAJEMEN PROFIL
# ─────────────────────────────────────────────

@app.route('/dashboard/profile', methods=['GET', 'POST'])
@admin_required
def dashboard_profile():
    profile = Profile.query.first()
    skills = Skill.query.all()
    if request.method == 'POST':
        action = request.form.get('action', 'update_profile')
        if action == 'update_profile':
            profile.name = request.form.get('name', '').strip() or profile.name
            profile.headline = request.form.get('headline', '').strip()
            profile.about = request.form.get('about', '').strip()
            profile.about_detail = request.form.get('about_detail', '').strip()
            profile.education = request.form.get('education', '').strip()
            profile.email = request.form.get('email', '').strip()
            profile.github = request.form.get('github', '').strip()
            profile.linkedin = request.form.get('linkedin', '').strip()
            if 'photo' in request.files:
                file = request.files['photo']
                if file and file.filename:
                    saved = save_uploaded_file(file, old_filename=profile.photo)
                    if saved:
                        profile.photo = saved
            db.session.commit()
            flash('Profil berhasil diperbarui!', 'success')
        elif action == 'add_skill':
            skill_name = request.form.get('skill_name', '').strip()
            skill_category = request.form.get('skill_category', 'Technical').strip()
            skill_level = int(request.form.get('skill_level', 80))
            if skill_name:
                db.session.add(Skill(name=skill_name, category=skill_category,
                                     level=skill_level))
                db.session.commit()
                flash(f'Skill "{skill_name}" berhasil ditambahkan!', 'success')
            else:
                flash('Nama skill tidak boleh kosong!', 'danger')
        return redirect(url_for('dashboard_profile'))
    return render_template('dashboard/profile.html', profile=profile, skills=skills)


@app.route('/dashboard/skills/delete/<int:skill_id>', methods=['POST'])
@admin_required
def delete_skill(skill_id):
    skill = Skill.query.get_or_404(skill_id)
    name = skill.name
    db.session.delete(skill)
    db.session.commit()
    flash(f'Skill "{name}" berhasil dihapus.', 'success')
    return redirect(url_for('dashboard_profile'))


# ─────────────────────────────────────────────
# DASHBOARD — KOTAK MASUK PESAN
# ─────────────────────────────────────────────

@app.route('/dashboard/messages')
@admin_required
def dashboard_messages():
    messages = Message.query.order_by(Message.created_at.desc()).all()
    return render_template('dashboard/messages.html', messages=messages)


@app.route('/dashboard/messages/read/<int:msg_id>', methods=['POST'])
@admin_required
def mark_message_read(msg_id):
    msg = Message.query.get_or_404(msg_id)
    msg.is_read = not msg.is_read
    db.session.commit()
    status = 'dibaca' if msg.is_read else 'belum dibaca'
    flash(f'Pesan dari {msg.name} ditandai sebagai {status}.', 'success')
    return redirect(url_for('dashboard_messages'))


@app.route('/dashboard/messages/delete/<int:msg_id>', methods=['POST'])
@admin_required
def delete_message(msg_id):
    msg = Message.query.get_or_404(msg_id)
    name = msg.name
    db.session.delete(msg)
    db.session.commit()
    flash(f'Pesan dari {name} berhasil dihapus.', 'success')
    return redirect(url_for('dashboard_messages'))


# ─────────────────────────────────────────────
# DASHBOARD — PENGATURAN AKUN
# ─────────────────────────────────────────────

@app.route('/dashboard/settings', methods=['GET', 'POST'])
@admin_required
def dashboard_settings():
    """Halaman pengaturan akun admin dan akses pembaca."""
    settings = get_settings()

    if request.method == 'POST':
        action = request.form.get('action', '')

        # ── Ganti Username ─────────────────────────
        if action == 'change_username':
            new_username = request.form.get('new_username', '').strip()
            if not new_username:
                flash('Username tidak boleh kosong!', 'danger')
            elif len(new_username) < 3:
                flash('Username minimal 3 karakter!', 'danger')
            else:
                settings.admin_username = new_username
                session['username'] = new_username
                db.session.commit()
                flash(f'Username berhasil diubah menjadi "{new_username}".', 'success')

        # ── Ganti Password Admin ────────────────────
        elif action == 'change_password':
            current_pw = request.form.get('current_password', '')
            new_pw = request.form.get('new_password', '')
            confirm_pw = request.form.get('confirm_password', '')
            if not settings.check_admin_password(current_pw):
                flash('Password saat ini salah!', 'danger')
            elif len(new_pw) < 6:
                flash('Password baru minimal 6 karakter!', 'danger')
            elif new_pw != confirm_pw:
                flash('Konfirmasi password tidak cocok!', 'danger')
            else:
                settings.set_admin_password(new_pw)
                db.session.commit()
                flash('Password admin berhasil diubah!', 'success')

        # ── Ganti Email Admin ───────────────────────
        elif action == 'change_email':
            new_email = request.form.get('new_email', '').strip()
            if not new_email or '@' not in new_email:
                flash('Email tidak valid!', 'danger')
            else:
                settings.admin_email = new_email
                db.session.commit()
                flash(f'Email berhasil diubah menjadi "{new_email}".', 'success')

        # ── Pengaturan Pembaca ──────────────────────
        elif action == 'reader_settings':
            reader_enabled = request.form.get('reader_enabled') == 'on'
            new_reader_pw = request.form.get('new_reader_password', '').strip()
            settings.reader_enabled = reader_enabled
            if new_reader_pw:
                if len(new_reader_pw) < 4:
                    flash('Password pembaca minimal 4 karakter!', 'danger')
                    return redirect(url_for('dashboard_settings'))
                settings.set_reader_password(new_reader_pw)
                flash('Pengaturan pembaca & password berhasil diperbarui!', 'success')
            else:
                flash('Pengaturan pembaca berhasil diperbarui!', 'success')
            db.session.commit()

        return redirect(url_for('dashboard_settings'))

    return render_template('dashboard/settings.html', settings=settings)


# ─────────────────────────────────────────────
# ERROR HANDLERS
# ─────────────────────────────────────────────

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(413)
def file_too_large(e):
    flash('File terlalu besar! Maksimal 5 MB.', 'danger')
    return redirect(request.referrer or url_for('dashboard_index'))


# ─────────────────────────────────────────────
# DATABASE INITIALIZATION
# ─────────────────────────────────────────────

with app.app_context():
    try:
        db.create_all()
        # Init profil default
        if not Profile.query.first():
            db.session.add(Profile(
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
            ))
        # Init settings default
        get_settings()
        db.session.commit()
    except Exception as e:
        app.logger.error(f"Error during database initialization: {e}")


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)


