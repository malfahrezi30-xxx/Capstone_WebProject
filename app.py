import os
from flask import (Flask, render_template, request, redirect,
                   url_for, session, flash, abort)
from werkzeug.utils import secure_filename
from config import Config
from models import db, Project, Message, Profile, Skill

app = Flask(__name__)
app.config.from_object(Config)

# Inisialisasi ekstensi
db.init_app(app)

# ─────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────

def allowed_file(filename):
    """Memeriksa apakah ekstensi file diperbolehkan."""
    return ('.' in filename and
            filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS'])


def login_required(f):
    """Decorator untuk melindungi route dashboard."""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash('Silakan login terlebih dahulu.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def save_uploaded_file(file, old_filename=None):
    """Menyimpan file yang di-upload dan mengembalikan nama file."""
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Tambahkan timestamp agar nama file unik
        import time
        name, ext = os.path.splitext(filename)
        filename = f"{name}_{int(time.time())}{ext}"
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(upload_path)
        # Hapus file lama jika ada dan bukan default
        if old_filename and old_filename not in ('default.jpg', 'default_profile.jpg'):
            old_path = os.path.join(app.config['UPLOAD_FOLDER'], old_filename)
            if os.path.exists(old_path):
                os.remove(old_path)
        return filename
    return None


# ─────────────────────────────────────────────
# CONTEXT PROCESSOR — data global untuk semua template
# ─────────────────────────────────────────────

@app.context_processor
def inject_globals():
    """Menyuntikkan data global ke semua template."""
    profile = Profile.query.first()
    unread_count = Message.query.filter_by(is_read=False).count()
    return dict(profile=profile, unread_count=unread_count)


# ─────────────────────────────────────────────
# HALAMAN PUBLIK
# ─────────────────────────────────────────────

@app.route('/')
def index():
    """Halaman Beranda."""
    profile = Profile.query.first()
    projects = Project.query.order_by(Project.created_at.desc()).limit(3).all()
    skills = Skill.query.all()
    return render_template('index.html', profile=profile,
                           projects=projects, skills=skills)


@app.route('/about')
def about():
    """Halaman About."""
    profile = Profile.query.first()
    skills = Skill.query.all()
    # Kelompokkan skill berdasarkan kategori
    skills_by_category = {}
    for skill in skills:
        cat = skill.category or 'Technical'
        if cat not in skills_by_category:
            skills_by_category[cat] = []
        skills_by_category[cat].append(skill)
    return render_template('about.html', profile=profile,
                           skills_by_category=skills_by_category)


@app.route('/portfolio')
def portfolio():
    """Halaman daftar semua proyek portofolio."""
    projects = Project.query.order_by(Project.created_at.desc()).all()
    return render_template('portfolio.html', projects=projects)


@app.route('/portfolio/<int:project_id>')
def project_detail(project_id):
    """Halaman detail sebuah proyek."""
    project = Project.query.get_or_404(project_id)
    other_projects = Project.query.filter(
        Project.id != project_id
    ).order_by(Project.created_at.desc()).limit(3).all()
    return render_template('project_detail.html',
                           project=project, other_projects=other_projects)


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """Halaman kontak dengan form pengiriman pesan."""
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
    """Halaman login dashboard admin."""
    if 'logged_in' in session:
        return redirect(url_for('dashboard_index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if (username == app.config['ADMIN_USERNAME'] and
                password == app.config['ADMIN_PASSWORD']):
            session['logged_in'] = True
            session['username'] = username
            flash('Login berhasil! Selamat datang di Dashboard.', 'success')
            return redirect(url_for('dashboard_index'))
        else:
            flash('Username atau password salah!', 'danger')

    return render_template('dashboard/login.html')


@app.route('/logout')
def logout():
    """Logout dari session."""
    session.clear()
    flash('Anda telah logout.', 'info')
    return redirect(url_for('login'))


# ─────────────────────────────────────────────
# DASHBOARD — HALAMAN UTAMA
# ─────────────────────────────────────────────

@app.route('/dashboard')
@login_required
def dashboard_index():
    """Halaman utama dashboard dengan statistik."""
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
@login_required
def dashboard_projects():
    """Halaman daftar semua proyek di dashboard."""
    projects = Project.query.order_by(Project.created_at.desc()).all()
    return render_template('dashboard/projects.html', projects=projects)


@app.route('/dashboard/projects/add', methods=['GET', 'POST'])
@login_required
def add_project():
    """Halaman form tambah proyek baru."""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        technologies = request.form.get('technologies', '').strip()
        github_link = request.form.get('github_link', '').strip()
        live_link = request.form.get('live_link', '').strip()

        if not title or not description:
            flash('Judul dan deskripsi wajib diisi!', 'danger')
            return render_template('dashboard/add_project.html')

        # Proses upload gambar
        image_filename = 'default.jpg'
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                # Validasi ukuran
                saved = save_uploaded_file(file)
                if saved:
                    image_filename = saved
                elif file.filename:
                    flash('Format file tidak diizinkan! Gunakan PNG, JPG, JPEG, GIF, atau WEBP.', 'danger')
                    return render_template('dashboard/add_project.html')

        project = Project(
            title=title,
            description=description,
            technologies=technologies,
            image_file=image_filename,
            github_link=github_link,
            live_link=live_link
        )
        db.session.add(project)
        db.session.commit()
        flash(f'Proyek "{title}" berhasil ditambahkan!', 'success')
        return redirect(url_for('dashboard_projects'))

    return render_template('dashboard/add_project.html')


@app.route('/dashboard/projects/edit/<int:project_id>', methods=['GET', 'POST'])
@login_required
def edit_project(project_id):
    """Halaman form edit proyek yang sudah ada."""
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

        # Proses upload gambar baru (opsional)
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
@login_required
def delete_project(project_id):
    """Menghapus proyek dari database."""
    project = Project.query.get_or_404(project_id)
    title = project.title

    # Hapus file gambar jika bukan default
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
@login_required
def dashboard_profile():
    """Halaman edit profil."""
    profile = Profile.query.first()
    skills = Skill.query.all()

    if request.method == 'POST':
        action = request.form.get('action', 'update_profile')

        if action == 'update_profile':
            # Update data profil
            profile.name = request.form.get('name', '').strip() or profile.name
            profile.headline = request.form.get('headline', '').strip()
            profile.about = request.form.get('about', '').strip()
            profile.about_detail = request.form.get('about_detail', '').strip()
            profile.education = request.form.get('education', '').strip()
            profile.email = request.form.get('email', '').strip()
            profile.github = request.form.get('github', '').strip()
            profile.linkedin = request.form.get('linkedin', '').strip()

            # Upload foto profil
            if 'photo' in request.files:
                file = request.files['photo']
                if file and file.filename:
                    saved = save_uploaded_file(file, old_filename=profile.photo)
                    if saved:
                        profile.photo = saved

            db.session.commit()
            flash('Profil berhasil diperbarui!', 'success')

        elif action == 'add_skill':
            # Tambah skill baru
            skill_name = request.form.get('skill_name', '').strip()
            skill_category = request.form.get('skill_category', 'Technical').strip()
            skill_level = int(request.form.get('skill_level', 80))

            if skill_name:
                new_skill = Skill(name=skill_name, category=skill_category,
                                  level=skill_level)
                db.session.add(new_skill)
                db.session.commit()
                flash(f'Skill "{skill_name}" berhasil ditambahkan!', 'success')
            else:
                flash('Nama skill tidak boleh kosong!', 'danger')

        return redirect(url_for('dashboard_profile'))

    return render_template('dashboard/profile.html', profile=profile, skills=skills)


@app.route('/dashboard/skills/delete/<int:skill_id>', methods=['POST'])
@login_required
def delete_skill(skill_id):
    """Menghapus skill dari database."""
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
@login_required
def dashboard_messages():
    """Halaman kotak masuk pesan."""
    messages = Message.query.order_by(Message.created_at.desc()).all()
    return render_template('dashboard/messages.html', messages=messages)


@app.route('/dashboard/messages/read/<int:msg_id>', methods=['POST'])
@login_required
def mark_message_read(msg_id):
    """Menandai pesan sebagai sudah dibaca."""
    msg = Message.query.get_or_404(msg_id)
    msg.is_read = not msg.is_read  # Toggle read/unread
    db.session.commit()
    status = 'dibaca' if msg.is_read else 'belum dibaca'
    flash(f'Pesan dari {msg.name} ditandai sebagai {status}.', 'success')
    return redirect(url_for('dashboard_messages'))


@app.route('/dashboard/messages/delete/<int:msg_id>', methods=['POST'])
@login_required
def delete_message(msg_id):
    """Menghapus pesan dari database."""
    msg = Message.query.get_or_404(msg_id)
    name = msg.name
    db.session.delete(msg)
    db.session.commit()
    flash(f'Pesan dari {name} berhasil dihapus.', 'success')
    return redirect(url_for('dashboard_messages'))


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
# ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == '__main__':
    # Buat folder uploads jika belum ada
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    with app.app_context():
        db.create_all()
        # Buat profil default jika belum ada
        if not Profile.query.first():
            default_profile = Profile(
                name='Muhammad Sadam Al-Fahrezi',
                headline='Mahasiswa Teknik Informatika | Python Developer',
                about='Halo! Saya adalah mahasiswa yang antusias dalam dunia pemrograman.',
                about_detail='Saya memiliki minat dalam pengembangan web menggunakan Python dan Flask.',
                education='S1 Teknik Informatika',
                email='m.alfahrezi30@gmail.com',
                github='https://github.com/malfahrezi30-xxx',
                linkedin='https://linkedin.com/in/'
            )
            db.session.add(default_profile)
            db.session.commit()
    app.run(debug=True)
