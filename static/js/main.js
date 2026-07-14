/**
 * Portfolio Flask — Main JavaScript
 * Pengantar Pemrograman — Capstone Project
 */

document.addEventListener('DOMContentLoaded', function () {

    // ─── 1. Navbar scroll effect ───────────────────────────────────
    const navbar = document.getElementById('mainNavbar');
    if (navbar) {
        const handleScroll = () => {
            if (window.scrollY > 50) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
        };
        window.addEventListener('scroll', handleScroll, { passive: true });
        handleScroll();
    }

    // ─── 2. Typing Animation (Hero) ────────────────────────────────
    const typingEl = document.getElementById('typingText');
    if (typingEl) {
        const originalText = typingEl.textContent.trim();
        const texts = [
            originalText,
            'Python Developer',
            'Flask Enthusiast',
            'Web Developer',
        ];
        let textIdx = 0, charIdx = 0, isDeleting = false;

        function type() {
            const current = texts[textIdx];
            if (isDeleting) {
                typingEl.textContent = current.substring(0, charIdx--);
            } else {
                typingEl.textContent = current.substring(0, charIdx++);
            }
            let delay = isDeleting ? 60 : 110;
            if (!isDeleting && charIdx > current.length) {
                delay = 2000;
                isDeleting = true;
            } else if (isDeleting && charIdx < 0) {
                isDeleting = false;
                textIdx = (textIdx + 1) % texts.length;
                delay = 400;
            }
            setTimeout(type, delay);
        }
        setTimeout(type, 1000);
    }

    // ─── 3. Skill Bar Animations ───────────────────────────────────
    const skillBars = document.querySelectorAll('.skill-bar-fill');
    if (skillBars.length) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const bar = entry.target;
                    const targetWidth = bar.dataset.width || bar.style.width;
                    bar.style.width = '0%';
                    setTimeout(() => {
                        bar.style.width = targetWidth + (targetWidth.toString().includes('%') ? '' : '%');
                    }, 100);
                    observer.unobserve(bar);
                }
            });
        }, { threshold: 0.3 });
        skillBars.forEach(bar => observer.observe(bar));
    }

    // ─── 4. Auto-dismiss Flash Messages ───────────────────────────
    const alerts = document.querySelectorAll('.alert.fade.show');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) bsAlert.close();
        }, 5000);
    });

    // ─── 5. Smooth Scroll for Anchor Links ────────────────────────
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                e.preventDefault();
                const offset = 80;
                const top = target.getBoundingClientRect().top + window.scrollY - offset;
                window.scrollTo({ top, behavior: 'smooth' });
            }
        });
    });

    // ─── 6. Active Nav Link Based on Scroll ───────────────────────
    const sections = document.querySelectorAll('section[id]');
    if (sections.length) {
        const navLinks = document.querySelectorAll('.nav-link[href*="#"]');
        const scrollSpy = () => {
            const scrollPos = window.scrollY + 100;
            sections.forEach(section => {
                if (scrollPos >= section.offsetTop &&
                    scrollPos < section.offsetTop + section.offsetHeight) {
                    navLinks.forEach(link => {
                        link.classList.toggle('active',
                            link.getAttribute('href').includes(section.id));
                    });
                }
            });
        };
        window.addEventListener('scroll', scrollSpy, { passive: true });
    }

    // ─── 7. Contact Form Validation ───────────────────────────────
    const contactForm = document.getElementById('contactForm');
    if (contactForm) {
        contactForm.addEventListener('submit', function (e) {
            const name    = document.getElementById('name');
            const email   = document.getElementById('email');
            const message = document.getElementById('message');
            let valid = true;

            [name, email, message].forEach(field => {
                field.classList.remove('is-invalid');
                if (!field.value.trim()) {
                    field.classList.add('is-invalid');
                    valid = false;
                }
            });

            if (!valid) {
                e.preventDefault();
                return;
            }

            // Loading state
            const btn = document.getElementById('submitBtn');
            if (btn) {
                btn.disabled = true;
                btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Mengirim...';
            }
        });
    }

    // ─── 8. Image Lazy Loading ────────────────────────────────────
    const lazyImages = document.querySelectorAll('img[data-src]');
    if (lazyImages.length) {
        const imgObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.removeAttribute('data-src');
                    imgObserver.unobserve(img);
                }
            });
        });
        lazyImages.forEach(img => imgObserver.observe(img));
    }

    // ─── 9. Tooltip initialization ────────────────────────────────
    const tooltipTriggers = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltipTriggers.forEach(el => new bootstrap.Tooltip(el));

    // ─── 10. Fade-in Animation on Scroll ─────────────────────────
    const fadeEls = document.querySelectorAll('[data-aos]');
    if (fadeEls.length) {
        const fadeObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const el = entry.target;
                    const delay = el.dataset.aosDelay || 0;
                    setTimeout(() => {
                        el.style.opacity = '1';
                        el.style.transform = 'translateY(0) scale(1)';
                    }, parseInt(delay));
                    fadeObserver.unobserve(el);
                }
            });
        }, { threshold: 0.1 });

        fadeEls.forEach(el => {
            el.style.opacity = '0';
            el.style.transform = 'translateY(24px)';
            el.style.transition = 'opacity .6s ease, transform .6s ease';
            fadeObserver.observe(el);
        });
    }

});
