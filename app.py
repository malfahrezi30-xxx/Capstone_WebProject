import os
import time
from functools import wraps
import requests
# pyrefly: ignore [missing-import]
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort  # type: ignore[import]
from werkzeug.utils import secure_filename  # type: ignore[import]
from config import Config
from models import db, Project, Message, Profile, Skill, User

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
    """Ambil settings dari DB, buat default jika belum ada (Backward compatibility helper)."""
    user_id = session.get('user_id')
    if user_id:
        return User.query.get(user_id)
    u = User.query.first()
    if not u:
        u = User(username=app.config.get('ADMIN_USERNAME', 'admin'))
        u.set_password(app.config.get('ADMIN_PASSWORD', 'admin123'))
        u.set_reader_password('visitor123')
        db.session.add(u)
        db.session.commit()
    return u


def get_current_portfolio_user_id():
    """Mendapatkan ID user portofolio yang sedang aktif diakses."""
    if session.get('role') == 'admin':
        return session.get('user_id')
    elif session.get('role') == 'reader':
        return session.get('portfolio_user_id')
    return None


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
    user_id = get_current_portfolio_user_id()
    profile = Profile.query.filter_by(user_id=user_id).first() if user_id else None
    unread_count = Message.query.filter_by(user_id=user_id, is_read=False).count() if user_id else 0
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
    user_id = get_current_portfolio_user_id()
    if not user_id:
        return redirect(url_for('login'))
    profile = Profile.query.filter_by(user_id=user_id).first()
    projects = Project.query.filter_by(user_id=user_id).order_by(Project.created_at.desc()).limit(3).all()
    skills = Skill.query.filter_by(user_id=user_id).all()
    return render_template('index.html', profile=profile,
                           projects=projects, skills=skills)


@app.route('/about')
@login_required
def about():
    """Halaman About."""
    user_id = get_current_portfolio_user_id()
    profile = Profile.query.filter_by(user_id=user_id).first()
    skills = Skill.query.filter_by(user_id=user_id).all()
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
    user_id = get_current_portfolio_user_id()
    projects = Project.query.filter_by(user_id=user_id).order_by(Project.created_at.desc()).all()
    return render_template('portfolio.html', projects=projects)


@app.route('/portfolio/<int:project_id>')
@login_required
def project_detail(project_id):
    """Halaman detail sebuah proyek."""
    user_id = get_current_portfolio_user_id()
    project = Project.query.filter_by(id=project_id, user_id=user_id).first_or_404()
    other_projects = Project.query.filter(
        Project.id != project_id,
        Project.user_id == user_id
    ).order_by(Project.created_at.desc()).limit(3).all()
    return render_template('project_detail.html',
                           project=project, other_projects=other_projects)


@app.route('/contact', methods=['GET', 'POST'])
@login_required
def contact():
    """Halaman kontak."""
    user_id = get_current_portfolio_user_id()
    profile = Profile.query.filter_by(user_id=user_id).first()
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        message_text = request.form.get('message', '').strip()
        if not name or not email or not message_text:
            flash('Semua field wajib diisi!', 'danger')
        else:
            msg = Message(user_id=user_id, name=name, email=email, message=message_text)
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

        if login_type == 'admin':
            username = request.form.get('username', '').strip()
            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                session['logged_in'] = True
                session['username'] = username
                session['user_id'] = user.id
                session['role'] = 'admin'
                flash(f'Selamat datang kembali, {username}!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Username atau password admin salah!', 'danger')

        elif login_type == 'reader':
            username = request.form.get('username', '').strip()
            user = User.query.filter_by(username=username).first()
            if not user:
                flash('Username portofolio tidak ditemukan!', 'danger')
            elif not user.reader_enabled:
                flash('Akses pembaca sedang dinonaktifkan oleh pemilik portofolio.', 'warning')
            elif user.check_reader_password(password):
                session['logged_in'] = True
                session['username'] = 'Pembaca'
                session['portfolio_user_id'] = user.id
                session['role'] = 'reader'
                flash(f'Selamat datang! Anda masuk sebagai Pembaca portofolio {username}.', 'success')
                return redirect(url_for('index'))
            else:
                flash('Password pembaca salah!', 'danger')

    return render_template('dashboard/login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Halaman registrasi akun baru."""
    if 'logged_in' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        reader_password = request.form.get('reader_password', '').strip()

        if not username or not password or not reader_password:
            flash('Username, password admin, dan password pembaca wajib diisi!', 'danger')
            return render_template('dashboard/register.html')

        if len(username) < 3:
            flash('Username minimal 3 karakter!', 'danger')
            return render_template('dashboard/register.html')

        if len(password) < 6:
            flash('Password admin minimal 6 karakter!', 'danger')
            return render_template('dashboard/register.html')

        # Cek jika username sudah ada
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username sudah digunakan oleh orang lain!', 'danger')
            return render_template('dashboard/register.html')

        # Cek email jika diisi
        if email:
            existing_email = User.query.filter_by(email=email).first()
            if existing_email:
                flash('Email sudah terdaftar!', 'danger')
                return render_template('dashboard/register.html')

        # Buat user baru
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        new_user.set_reader_password(reader_password)

        db.session.add(new_user)
        db.session.commit() # Simpan agar mendapatkan ID user baru

        # Buat profil kosong untuk user baru
        new_profile = Profile(
            user_id=new_user.id,
            name=username,
            headline='Web Developer',
            about='Halo! Saya baru saja mendaftar di web portofolio ini.',
            about_detail='Silakan edit profil lengkap Anda di dashboard admin.',
            education='Pendidikan belum diisi.',
            email=email or 'email@example.com',
            photo='default_profile.jpg'
        )
        db.session.add(new_profile)
        db.session.commit()

        flash('Pendaftaran berhasil! Silakan masuk dengan akun baru Anda.', 'success')
        return redirect(url_for('login'))

    return render_template('dashboard/register.html')


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
    user_id = session.get('user_id')
    total_projects = Project.query.filter_by(user_id=user_id).count()
    total_messages = Message.query.filter_by(user_id=user_id).count()
    unread_messages = Message.query.filter_by(user_id=user_id, is_read=False).count()
    recent_messages = Message.query.filter_by(user_id=user_id).order_by(
        Message.created_at.desc()).limit(5).all()
    recent_projects = Project.query.filter_by(user_id=user_id).order_by(
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
    user_id = session.get('user_id')
    projects = Project.query.filter_by(user_id=user_id).order_by(Project.created_at.desc()).all()
    return render_template('dashboard/projects.html', projects=projects)


@app.route('/dashboard/projects/add', methods=['GET', 'POST'])
@admin_required
def add_project():
    user_id = session.get('user_id')
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
        project = Project(user_id=user_id, title=title, description=description,
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
    user_id = session.get('user_id')
    project = Project.query.filter_by(id=project_id, user_id=user_id).first_or_404()
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
    user_id = session.get('user_id')
    project = Project.query.filter_by(id=project_id, user_id=user_id).first_or_404()
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
    user_id = session.get('user_id')
    profile = Profile.query.filter_by(user_id=user_id).first()
    skills = Skill.query.filter_by(user_id=user_id).all()
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
                db.session.add(Skill(user_id=user_id, name=skill_name, category=skill_category,
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
    user_id = session.get('user_id')
    skill = Skill.query.filter_by(id=skill_id, user_id=user_id).first_or_404()
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
    user_id = session.get('user_id')
    messages = Message.query.filter_by(user_id=user_id).order_by(Message.created_at.desc()).all()
    return render_template('dashboard/messages.html', messages=messages)


@app.route('/dashboard/messages/read/<int:msg_id>', methods=['POST'])
@admin_required
def mark_message_read(msg_id):
    user_id = session.get('user_id')
    msg = Message.query.filter_by(id=msg_id, user_id=user_id).first_or_404()
    msg.is_read = not msg.is_read
    db.session.commit()
    status = 'dibaca' if msg.is_read else 'belum dibaca'
    flash(f'Pesan dari {msg.name} ditandai sebagai {status}.', 'success')
    return redirect(url_for('dashboard_messages'))


@app.route('/dashboard/messages/delete/<int:msg_id>', methods=['POST'])
@admin_required
def delete_message(msg_id):
    user_id = session.get('user_id')
    msg = Message.query.filter_by(id=msg_id, user_id=user_id).first_or_404()
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
        # Init user default
        if not User.query.first():
            admin = User(username='admin', email='m.alfahrezi30@gmail.com')
            admin.set_password('admin123')
            admin.set_reader_password('visitor123')
            db.session.add(admin)
            db.session.commit() # dapatkan admin.id
            
            # Init profil untuk admin default
            db.session.add(Profile(
                user_id=admin.id,
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
            db.session.commit()
    except Exception as e:
        app.logger.error(f"Error during database initialization: {e}")


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)


