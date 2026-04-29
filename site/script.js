// AutoBot Solutions Forum - Interactive JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize particles
    createParticles();
    
    // Initialize smooth scrolling
    initSmoothScroll();
    
    // Initialize copy buttons
    initCopyButtons();
    
    // Initialize stat counters
    initStatCounters();
    
    // Initialize navbar scroll effect
    initNavbarScroll();
    
    // Initialize intersection observer for animations
    initAnimations();
});

// Create floating particles
function createParticles() {
    const particlesContainer = document.querySelector('.particles');
    if (!particlesContainer) return;
    
    const particleCount = 50;
    
    for (let i = 0; i < particleCount; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        particle.style.left = Math.random() * 100 + '%';
        particle.style.top = Math.random() * 100 + '%';
        particle.style.animationDelay = Math.random() * 15 + 's';
        particle.style.animationDuration = (10 + Math.random() * 10) + 's';
        particlesContainer.appendChild(particle);
    }
}

// Smooth scrolling for navigation links
function initSmoothScroll() {
    const navLinks = document.querySelectorAll('a[href^="#"]');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            
            if (targetElement) {
                const offsetTop = targetElement.offsetTop - 80;
                window.scrollTo({
                    top: offsetTop,
                    behavior: 'smooth'
                });
            }
        });
    });
}

// Copy button functionality
function initCopyButtons() {
    const copyButtons = document.querySelectorAll('.copy-btn');
    
    copyButtons.forEach(button => {
        button.addEventListener('click', function() {
            const code = this.getAttribute('data-code');
            
            if (code) {
                navigator.clipboard.writeText(code).then(() => {
                    const originalText = this.textContent;
                    this.textContent = 'Copied!';
                    this.style.background = 'rgba(0, 255, 136, 0.2)';
                    this.style.borderColor = 'var(--neon-green)';
                    this.style.color = 'var(--neon-green)';
                    
                    setTimeout(() => {
                        this.textContent = originalText;
                        this.style.background = '';
                        this.style.borderColor = '';
                        this.style.color = '';
                    }, 2000);
                }).catch(err => {
                    console.error('Failed to copy:', err);
                });
            }
        });
    });
}

// Animated stat counters
function initStatCounters() {
    const statNumbers = document.querySelectorAll('.stat-number[data-target]');
    
    const observerOptions = {
        threshold: 0.5
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const target = parseInt(entry.target.getAttribute('data-target'));
                animateCounter(entry.target, target);
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    statNumbers.forEach(number => {
        observer.observe(number);
    });
}

function animateCounter(element, target) {
    const duration = 2000;
    const start = 0;
    const increment = target / (duration / 16);
    let current = start;
    
    const timer = setInterval(() => {
        current += increment;
        
        if (current >= target) {
            element.textContent = target + '+';
            clearInterval(timer);
        } else {
            element.textContent = Math.floor(current) + '+';
        }
    }, 16);
}

// Navbar scroll effect
function initNavbarScroll() {
    const navbar = document.querySelector('.navbar');
    let lastScroll = 0;
    
    window.addEventListener('scroll', () => {
        const currentScroll = window.pageYOffset;
        
        if (currentScroll > 50) {
            navbar.style.background = 'rgba(10, 10, 15, 0.98)';
            navbar.style.boxShadow = '0 0 20px rgba(0, 245, 255, 0.1)';
        } else {
            navbar.style.background = 'rgba(10, 10, 15, 0.95)';
            navbar.style.boxShadow = 'none';
        }
        
        lastScroll = currentScroll;
    });
}

// Intersection observer for scroll animations
function initAnimations() {
    const animatedElements = document.querySelectorAll(
        '.feature-card, .tech-item, .stat-item, .step'
    );
    
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);
    
    animatedElements.forEach(element => {
        element.style.opacity = '0';
        element.style.transform = 'translateY(30px)';
        element.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(element);
    });
}

// Typing effect for terminal
function initTypingEffect() {
    const terminalLines = document.querySelectorAll('.terminal-line .command');
    
    terminalLines.forEach((line, index) => {
        const text = line.textContent;
        line.textContent = '';
        let charIndex = 0;
        
        setTimeout(() => {
            const typeInterval = setInterval(() => {
                if (charIndex < text.length) {
                    line.textContent += text.charAt(charIndex);
                    charIndex++;
                } else {
                    clearInterval(typeInterval);
                }
            }, 50);
        }, index * 500);
    });
}

// Initialize typing effect after a delay
setTimeout(initTypingEffect, 1000);

// Add hover sound effect (optional - requires audio files)
function addHoverSound() {
    const interactiveElements = document.querySelectorAll(
        '.btn-primary, .btn-secondary, .feature-card, .nav-link'
    );
    
    interactiveElements.forEach(element => {
        element.addEventListener('mouseenter', () => {
            // Play hover sound if audio files are available
            // const audio = new Audio('/sounds/hover.mp3');
            // audio.play();
        });
    });
}

// Add parallax effect to hero section
function initParallax() {
    const hero = document.querySelector('.hero');
    const heroVisual = document.querySelector('.hero-visual');
    
    window.addEventListener('scroll', () => {
        const scrolled = window.pageYOffset;
        const rate = scrolled * -0.3;
        
        if (hero && heroVisual) {
            heroVisual.style.transform = `translateY(${rate}px)`;
        }
    });
}

initParallax();

// Add keyboard navigation
document.addEventListener('keydown', (e) => {
    // Press 'F' to scroll to features
    if (e.key === 'f' || e.key === 'F') {
        const featuresSection = document.querySelector('#features');
        if (featuresSection) {
            featuresSection.scrollIntoView({ behavior: 'smooth' });
        }
    }
    
    // Press 'T' to scroll to tech stack
    if (e.key === 't' || e.key === 'T') {
        const techSection = document.querySelector('#tech');
        if (techSection) {
            techSection.scrollIntoView({ behavior: 'smooth' });
        }
    }
    
    // Press 'I' to scroll to install
    if (e.key === 'i' || e.key === 'I') {
        const installSection = document.querySelector('#install');
        if (installSection) {
            installSection.scrollIntoView({ behavior: 'smooth' });
        }
    }
});

// Add loading animation
window.addEventListener('load', () => {
    document.body.style.opacity = '1';
});

// Prevent FOUC (Flash of Unstyled Content)
document.body.style.opacity = '0';
