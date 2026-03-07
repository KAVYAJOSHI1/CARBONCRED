/* ─── Landing Page JavaScript ─── */
/* Particles, Scroll Animations, Counters, Theme Toggle */

(function () {
    'use strict';

    // ═══ THEME MANAGEMENT ═══
    const root = document.documentElement;
    const themeToggle = document.getElementById('themeToggle');
    const themeIcon = document.getElementById('themeIcon');
    const savedTheme = localStorage.getItem('cv_theme') || 'dark';
    root.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);

    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            const current = root.getAttribute('data-theme');
            const next = current === 'dark' ? 'light' : 'dark';
            root.setAttribute('data-theme', next);
            localStorage.setItem('cv_theme', next);
            updateThemeIcon(next);
        });
    }

    function updateThemeIcon(theme) {
        if (!themeIcon) return;
        themeIcon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
    }

    // ═══ CURSOR GLOW ═══
    const cursorGlow = document.getElementById('cursorGlow');
    let mx = -500, my = -500;
    let cx = -500, cy = -500;

    document.addEventListener('mousemove', (e) => {
        mx = e.clientX;
        my = e.clientY;
    });

    function animateCursor() {
        cx += (mx - cx) * 0.08;
        cy += (my - cy) * 0.08;
        if (cursorGlow) {
            cursorGlow.style.left = cx + 'px';
            cursorGlow.style.top = cy + 'px';
        }
        requestAnimationFrame(animateCursor);
    }
    animateCursor();

    // ═══ NAVBAR SCROLL ═══
    const navbar = document.getElementById('navbar');
    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            navbar && navbar.classList.add('scrolled');
        } else {
            navbar && navbar.classList.remove('scrolled');
        }
    }, { passive: true });

    // ═══ HAMBURGER MENU ═══
    const hamburger = document.getElementById('hamburger');
    const navLinks = document.getElementById('navLinks');
    if (hamburger && navLinks) {
        hamburger.addEventListener('click', () => {
            navLinks.classList.toggle('open');
            // Animate hamburger bars
            hamburger.classList.toggle('open');
        });
        navLinks.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', () => navLinks.classList.remove('open'));
        });
    }

    // ═══ HERO PARTICLE CANVAS ═══
    const canvas = document.getElementById('particleCanvas');
    if (canvas) {
        const ctx = canvas.getContext('2d');
        let particles = [];
        let W, H;

        function resize() {
            W = canvas.width = canvas.offsetWidth;
            H = canvas.height = canvas.offsetHeight;
        }
        resize();
        window.addEventListener('resize', resize, { passive: true });

        const isDark = () => root.getAttribute('data-theme') !== 'light';

        class Particle {
            constructor() { this.reset(); }
            reset() {
                this.x = Math.random() * W;
                this.y = Math.random() * H;
                this.size = Math.random() * 2 + 0.5;
                this.speedX = (Math.random() - 0.5) * 0.4;
                this.speedY = -Math.random() * 0.6 - 0.2;
                this.life = 0;
                this.maxLife = Math.random() * 200 + 100;
                this.alpha = 0;
            }
            update() {
                this.x += this.speedX;
                this.y += this.speedY;
                this.life++;
                if (this.life < 30) this.alpha = this.life / 30;
                else if (this.life > this.maxLife - 30) this.alpha = (this.maxLife - this.life) / 30;
                else this.alpha = 1;
                if (this.life >= this.maxLife) this.reset();
            }
            draw() {
                const color = isDark() ? `rgba(0, 255, 135, ${this.alpha * 0.5})` : `rgba(5, 150, 82, ${this.alpha * 0.4})`;
                ctx.beginPath();
                ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
                ctx.fillStyle = color;
                ctx.fill();
            }
        }

        for (let i = 0; i < 100; i++) particles.push(new Particle());

        // Connections
        function drawConnections() {
            for (let i = 0; i < particles.length; i++) {
                for (let j = i + 1; j < particles.length; j++) {
                    const dx = particles[i].x - particles[j].x;
                    const dy = particles[i].y - particles[j].y;
                    const dist = Math.sqrt(dx * dx + dy * dy);
                    if (dist < 100) {
                        const alpha = (1 - dist / 100) * 0.15;
                        const color = isDark() ? `rgba(0, 255, 135, ${alpha})` : `rgba(5, 150, 82, ${alpha})`;
                        ctx.beginPath();
                        ctx.strokeStyle = color;
                        ctx.lineWidth = 0.5;
                        ctx.moveTo(particles[i].x, particles[i].y);
                        ctx.lineTo(particles[j].x, particles[j].y);
                        ctx.stroke();
                    }
                }
            }
        }

        function animateParticles() {
            ctx.clearRect(0, 0, W, H);
            particles.forEach(p => { p.update(); p.draw(); });
            drawConnections();
            requestAnimationFrame(animateParticles);
        }
        animateParticles();
    }

    // ═══ CTA CANVAS (Subtle flow) ═══
    const ctaCanvas = document.getElementById('ctaCanvas');
    if (ctaCanvas) {
        const ctx2 = ctaCanvas.getContext('2d');
        let W2, H2;

        function resize2() {
            W2 = ctaCanvas.width = ctaCanvas.offsetWidth;
            H2 = ctaCanvas.height = ctaCanvas.offsetHeight;
        }
        resize2();
        window.addEventListener('resize', resize2, { passive: true });

        let t2 = 0;
        function animateCTA() {
            ctx2.clearRect(0, 0, W2, H2);
            t2 += 0.003;
            const isDarkMode = root.getAttribute('data-theme') !== 'light';
            const c1 = isDarkMode ? 'rgba(0,255,135,0.06)' : 'rgba(5,150,82,0.05)';
            const c2 = isDarkMode ? 'rgba(0,212,255,0.04)' : 'rgba(0,119,182,0.04)';

            // Soft moving blobs
            for (let i = 0; i < 3; i++) {
                const angle = t2 + (i * Math.PI * 2 / 3);
                const bx = W2 / 2 + Math.cos(angle) * W2 * 0.25;
                const by = H2 / 2 + Math.sin(angle * 0.7) * H2 * 0.3;
                const grad = ctx2.createRadialGradient(bx, by, 0, bx, by, W2 * 0.4);
                grad.addColorStop(0, i % 2 === 0 ? c1 : c2);
                grad.addColorStop(1, 'rgba(0,0,0,0)');
                ctx2.fillStyle = grad;
                ctx2.beginPath();
                ctx2.arc(bx, by, W2 * 0.4, 0, Math.PI * 2);
                ctx2.fill();
            }
            requestAnimationFrame(animateCTA);
        }
        animateCTA();
    }

    // ═══ SCROLL REVEAL ═══
    function initReveal() {
        const elements = document.querySelectorAll('.reveal-up, .reveal-left, .reveal-right');
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const delay = entry.target.dataset.delay || 0;
                    setTimeout(() => entry.target.classList.add('visible'), parseInt(delay));
                }
            });
        }, { threshold: 0.15, rootMargin: '0px 0px -60px 0px' });

        elements.forEach(el => observer.observe(el));
    }
    initReveal();

    // ═══ COUNTER ANIMATION ═══
    function animateCounter(el) {
        const target = parseInt(el.dataset.target);
        const duration = 2000;
        const start = performance.now();
        const startVal = 0;

        function update(now) {
            const elapsed = now - start;
            const progress = Math.min(elapsed / duration, 1);
            // Ease out cubic
            const eased = 1 - Math.pow(1 - progress, 3);
            const current = Math.floor(startVal + (target - startVal) * eased);
            el.textContent = current.toLocaleString();
            if (progress < 1) requestAnimationFrame(update);
        }
        requestAnimationFrame(update);
    }

    function initCounters() {
        const counters = document.querySelectorAll('.counter, .counter-mega');
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting && !entry.target.dataset.counted) {
                    entry.target.dataset.counted = 'true';
                    animateCounter(entry.target);
                }
            });
        }, { threshold: 0.5 });

        counters.forEach(c => observer.observe(c));
    }
    initCounters();

    // ═══ HERO BG PARALLAX ═══
    const heroBg = document.querySelector('.hero-bg-image');
    window.addEventListener('scroll', () => {
        if (heroBg) {
            const scrolled = window.scrollY;
            heroBg.style.transform = `scale(1.05) translateY(${scrolled * 0.3}px)`;
        }
    }, { passive: true });

    // ═══ SMOOTH SCROLL for hero CTA ═══
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                e.preventDefault();
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });

    // ═══ TECH CARD STAGGER ON HOVER ═══
    document.querySelectorAll('.tech-card').forEach((card, i) => {
        card.style.transitionDelay = `${i * 30}ms`;
    });

    // ═══ ROLE CARDS: Magnetic tilt ═══
    function addMagneticEffect(selector) {
        document.querySelectorAll(selector).forEach(card => {
            card.addEventListener('mousemove', (e) => {
                const rect = card.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                const centerX = rect.width / 2;
                const centerY = rect.height / 2;
                const tiltX = ((y - centerY) / centerY) * 5;
                const tiltY = ((centerX - x) / centerX) * 5;
                card.style.transform = `perspective(1000px) rotateX(${tiltX}deg) rotateY(${tiltY}deg) translateY(-8px)`;
            });
            card.addEventListener('mouseleave', () => {
                card.style.transform = '';
            });
        });
    }
    addMagneticEffect('.tech-card');
    addMagneticEffect('.role-card');

    // ═══ NAV ACTIVE ON SCROLL ═══
    const sections = document.querySelectorAll('section[id]');
    const navLinks2 = document.querySelectorAll('.nav-link');

    window.addEventListener('scroll', () => {
        let current = '';
        sections.forEach(section => {
            if (window.scrollY >= section.offsetTop - 150) {
                current = section.getAttribute('id');
            }
        });
        navLinks2.forEach(link => {
            link.classList.remove('active-nav');
            if (link.getAttribute('href') === '#' + current) {
                link.classList.add('active-nav');
            }
        });
    }, { passive: true });

    // Add active style
    const style = document.createElement('style');
    style.textContent = `.nav-link.active-nav { color: var(--primary) !important; background: var(--primary-dim) !important; }`;
    document.head.appendChild(style);

    console.log('🌿 CarbonVerse Landing — Fully Initialized');
})();
