/**
 * effects.js — GSAP ScrollTrigger animations, 3D card tilt, scroll reveals.
 */

// Register GSAP plugin
gsap.registerPlugin(ScrollTrigger);

/**
 * Initialize all scroll-triggered effects.
 */
function initEffects() {
    setupNavScroll();
    setupScrollReveal();
    setupCardTilt();
    setupChartAnimations();
    setupNumberCountUp();
}

// ── Nav scroll state ─────────────────────────────────────────────────────────

function setupNavScroll() {
    const nav = document.getElementById('nav');
    const sections = document.querySelectorAll('.section');
    const links = document.querySelectorAll('.nav-link');

    // Scrolled state — show border
    window.addEventListener('scroll', () => {
        nav.classList.toggle('scrolled', window.scrollY > 50);
    }, { passive: true });

    // Active link tracking
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const id = entry.target.id;
                links.forEach(link => {
                    link.classList.toggle('active', link.dataset.section === id);
                });
            }
        });
    }, { threshold: 0.3 });

    sections.forEach(section => observer.observe(section));

    // Smooth scroll on click
    links.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const target = document.getElementById(link.dataset.section);
            if (target) {
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });
}

// ── Scroll Reveal (IntersectionObserver) ─────────────────────────────────────

function setupScrollReveal() {
    const elements = document.querySelectorAll('.scroll-reveal, .metric-card');

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });

    elements.forEach(el => observer.observe(el));
}

// ── 3D Card Tilt ─────────────────────────────────────────────────────────────

function setupCardTilt() {
    document.addEventListener('mousemove', (e) => {
        const cards = document.querySelectorAll('.metric-card.visible');
        cards.forEach(card => {
            const rect = card.getBoundingClientRect();

            // Only process if mouse is near the card
            const buffer = 50;
            if (
                e.clientX < rect.left - buffer ||
                e.clientX > rect.right + buffer ||
                e.clientY < rect.top - buffer ||
                e.clientY > rect.bottom + buffer
            ) return;

            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;

            const rotateX = ((y - centerY) / centerY) * -6;
            const rotateY = ((x - centerX) / centerX) * 6;

            card.style.transform =
                `perspective(800px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateZ(8px)`;
        });
    });

    // Reset on mouse leave
    document.addEventListener('mouseover', (e) => {
        const card = e.target.closest('.metric-card');
        if (!card) {
            document.querySelectorAll('.metric-card.visible').forEach(c => {
                c.style.transform = '';
            });
        }
    });
}

// ── GSAP Chart Animations ────────────────────────────────────────────────────

function setupChartAnimations() {
    // Animate chart containers sliding in
    gsap.utils.toArray('.chart-container').forEach(container => {
        gsap.from(container, {
            y: 40,
            opacity: 0,
            duration: 0.8,
            ease: 'power2.out',
            scrollTrigger: {
                trigger: container,
                start: 'top 85%',
                once: true,
            },
        });
    });
}

// ── Number Count-Up ──────────────────────────────────────────────────────────

function setupNumberCountUp() {
    const counters = document.querySelectorAll('[data-count-target]');

    counters.forEach(el => {
        const target = parseFloat(el.dataset.countTarget);
        const suffix = el.dataset.countSuffix || '';
        const decimals = el.dataset.countDecimals ? parseInt(el.dataset.countDecimals) : 0;

        ScrollTrigger.create({
            trigger: el,
            start: 'top 85%',
            once: true,
            onEnter: () => {
                gsap.fromTo(el, { textContent: 0 }, {
                    textContent: target,
                    duration: 1.5,
                    ease: 'power1.out',
                    snap: decimals === 0 ? { textContent: 1 } : {},
                    onUpdate: function () {
                        const val = parseFloat(gsap.getProperty(el, 'textContent'));
                        el.textContent = val.toFixed(decimals) + suffix;
                    },
                });
            },
        });
    });
}

// ── Refresh scroll triggers after dynamic content ────────────────────────────

function refreshEffects() {
    setupScrollReveal();
    ScrollTrigger.refresh();
}

// Expose globally
window.Effects = { initEffects, refreshEffects };
