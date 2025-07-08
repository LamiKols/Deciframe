/**
 * Landing Page JavaScript for DeciFrame
 * Handles animations, interactions, and dynamic content
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all features
    initNavbar();
    initScrollAnimations();
    initDashboardPreview();
    initHeroAnimations();
    initProgressBars();
    initFormValidation();
    
    console.log('DeciFrame landing page initialized');
});

/**
 * Navbar functionality
 */
function initNavbar() {
    const navbar = document.querySelector('.navbar');
    const mobileToggle = document.querySelector('.mobile-menu-toggle');
    const navLinks = document.querySelector('.nav-links');
    
    // Navbar scroll effect
    window.addEventListener('scroll', function() {
        if (window.scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    });
    
    // Mobile menu toggle
    if (mobileToggle && navLinks) {
        mobileToggle.addEventListener('click', function() {
            navLinks.classList.toggle('active');
            this.classList.toggle('active');
        });
    }
    
    // Smooth scroll for navigation links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const href = this.getAttribute('href');
            if (href && href !== '#') {
                const target = document.querySelector(href);
                if (target) {
                    const offsetTop = target.offsetTop - 80; // Account for fixed navbar
                    window.scrollTo({
                        top: offsetTop,
                        behavior: 'smooth'
                    });
                }
            }
        });
    });
}

/**
 * Scroll animations for sections
 */
function initScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('in-view');
                
                // Trigger specific animations for different elements
                if (entry.target.classList.contains('feature-card')) {
                    animateFeatureCard(entry.target);
                } else if (entry.target.classList.contains('metric-card')) {
                    animateMetricCard(entry.target);
                }
            }
        });
    }, observerOptions);
    
    // Observe all animatable elements
    document.querySelectorAll('.feature-card, .solution-card, .metric-card').forEach(el => {
        el.classList.add('scroll-animate');
        observer.observe(el);
    });
}

/**
 * Dashboard preview interactions
 */
function initDashboardPreview() {
    const tabs = document.querySelectorAll('.tab');
    const metricCards = document.querySelectorAll('.metric-card');
    
    // Tab switching functionality
    tabs.forEach((tab, index) => {
        tab.addEventListener('click', function() {
            // Remove active class from all tabs
            tabs.forEach(t => t.classList.remove('active'));
            // Add active class to clicked tab
            this.classList.add('active');
            
            // Update metric cards based on selected tab
            updateDashboardContent(index);
        });
    });
    
    // Hover effects for metric cards
    metricCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
            this.style.boxShadow = '0 8px 25px rgba(0, 0, 0, 0.15)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = '';
        });
    });
}

/**
 * Update dashboard content based on selected tab
 */
function updateDashboardContent(tabIndex) {
    const metricData = [
        // Problems tab (index 0)
        [
            { icon: '📊', value: '127', label: 'Active Cases' },
            { icon: '💡', value: (window.CURRENCY_SYMBOL || '$') + '4.2M', label: 'Projected ROI' },
            { icon: '⚡', value: '89%', label: 'Approval Rate' }
        ],
        // Business Cases tab (index 1)
        [
            { icon: '📈', value: '45', label: 'Active Cases' },
            { icon: '💰', value: (window.CURRENCY_SYMBOL || '$') + '12.8M', label: 'Total Value' },
            { icon: '✅', value: '73%', label: 'Success Rate' }
        ],
        // Projects tab (index 2)
        [
            { icon: '🚀', value: '23', label: 'In Progress' },
            { icon: '⏱️', value: '94%', label: 'On Time' },
            { icon: '👥', value: '156', label: 'Team Members' }
        ]
    ];
    
    const cards = document.querySelectorAll('.metric-card');
    const data = metricData[tabIndex] || metricData[0];
    
    cards.forEach((card, index) => {
        if (data[index]) {
            const icon = card.querySelector('.metric-icon');
            const value = card.querySelector('.metric-value');
            const label = card.querySelector('.metric-label');
            
            // Add animation
            card.style.opacity = '0.5';
            card.style.transform = 'scale(0.95)';
            
            setTimeout(() => {
                if (icon) icon.textContent = data[index].icon;
                if (value) value.textContent = data[index].value;
                if (label) label.textContent = data[index].label;
                
                card.style.opacity = '1';
                card.style.transform = 'scale(1)';
                card.style.transition = 'all 0.3s ease';
            }, 150);
        }
    });
}

/**
 * Hero section animations
 */
function initHeroAnimations() {
    const heroTitle = document.querySelector('.hero-title');
    const heroSubtitle = document.querySelector('.hero-subtitle');
    const heroButtons = document.querySelector('.hero-buttons');
    const heroStats = document.querySelector('.hero-stats');
    
    // Staggered animations for hero elements
    setTimeout(() => {
        if (heroTitle) heroTitle.classList.add('fade-in-up');
    }, 200);
    
    setTimeout(() => {
        if (heroSubtitle) heroSubtitle.classList.add('fade-in-up');
    }, 400);
    
    setTimeout(() => {
        if (heroButtons) heroButtons.classList.add('fade-in-up');
    }, 600);
    
    setTimeout(() => {
        if (heroStats) heroStats.classList.add('fade-in-up');
    }, 800);
    
    // Animate stats numbers
    animateStatsNumbers();
}

/**
 * Animate statistics numbers with counting effect
 */
function animateStatsNumbers() {
    const statNumbers = document.querySelectorAll('.stat-number');
    
    statNumbers.forEach(stat => {
        const finalValue = stat.textContent;
        const isPercentage = finalValue.includes('%');
        const isCurrency = finalValue.includes('$');
        const hasPlus = finalValue.includes('+');
        
        let numericValue = parseFloat(finalValue.replace(/[^0-9.]/g, ''));
        
        if (isNaN(numericValue)) return;
        
        let currentValue = 0;
        const increment = numericValue / 50; // Animate over 50 steps
        const duration = 1500; // 1.5 seconds
        const stepTime = duration / 50;
        
        const timer = setInterval(() => {
            currentValue += increment;
            
            if (currentValue >= numericValue) {
                currentValue = numericValue;
                clearInterval(timer);
            }
            
            let displayValue = Math.floor(currentValue);
            
            if (isCurrency) {
                displayValue = '$' + displayValue.toLocaleString();
                if (finalValue.includes('M')) displayValue += 'M';
            } else if (isPercentage) {
                displayValue = displayValue + '%';
            } else if (hasPlus) {
                displayValue = displayValue.toLocaleString() + '+';
            } else {
                displayValue = displayValue.toLocaleString();
            }
            
            stat.textContent = displayValue;
        }, stepTime);
    });
}

/**
 * Animate progress bars (if any are added later)
 */
function initProgressBars() {
    const progressBars = document.querySelectorAll('.progress-bar');
    
    progressBars.forEach(bar => {
        const width = bar.getAttribute('data-width') || '0%';
        
        const observer = new IntersectionObserver(entries => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    setTimeout(() => {
                        bar.style.width = width;
                    }, 200);
                    observer.unobserve(bar);
                }
            });
        });
        
        observer.observe(bar);
    });
}

/**
 * Feature card animations
 */
function animateFeatureCard(card) {
    const icon = card.querySelector('.feature-icon');
    const title = card.querySelector('h3');
    const description = card.querySelector('p');
    const list = card.querySelector('.feature-list');
    
    if (icon) {
        setTimeout(() => icon.style.transform = 'scale(1.1) rotate(5deg)', 100);
        setTimeout(() => icon.style.transform = 'scale(1) rotate(0deg)', 400);
    }
    
    if (list) {
        const items = list.querySelectorAll('li');
        items.forEach((item, index) => {
            setTimeout(() => {
                item.style.opacity = '1';
                item.style.transform = 'translateX(0)';
            }, 200 + (index * 100));
        });
    }
}

/**
 * Metric card animations
 */
function animateMetricCard(card) {
    const value = card.querySelector('.metric-value');
    
    if (value) {
        const originalValue = value.textContent;
        value.textContent = '0';
        
        setTimeout(() => {
            value.textContent = originalValue;
            value.style.transform = 'scale(1.2)';
            setTimeout(() => {
                value.style.transform = 'scale(1)';
            }, 200);
        }, 300);
    }
}

/**
 * Testimonial card animations
 */
function animateTestimonialCard(card) {
    const avatar = card.querySelector('.author-avatar');
    const content = card.querySelector('.testimonial-content');
    
    if (avatar) {
        avatar.style.transform = 'scale(0) rotate(180deg)';
        setTimeout(() => {
            avatar.style.transform = 'scale(1) rotate(0deg)';
        }, 200);
    }
    
    if (content) {
        const text = content.querySelector('p');
        if (text) {
            text.style.opacity = '0';
            setTimeout(() => {
                text.style.opacity = '1';
            }, 400);
        }
    }
}

/**
 * Form validation for waitlist and contact forms
 */
function initFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(this)) {
                e.preventDefault();
            }
        });
        
        // Real-time validation
        const inputs = form.querySelectorAll('input, textarea');
        inputs.forEach(input => {
            input.addEventListener('blur', () => validateField(input));
            input.addEventListener('input', () => clearFieldError(input));
        });
    });
}

/**
 * Validate entire form
 */
function validateForm(form) {
    let isValid = true;
    const inputs = form.querySelectorAll('input[required], textarea[required]');
    
    inputs.forEach(input => {
        if (!validateField(input)) {
            isValid = false;
        }
    });
    
    return isValid;
}

/**
 * Validate individual field
 */
function validateField(field) {
    const value = field.value.trim();
    const fieldType = field.type;
    const fieldName = field.name;
    
    // Clear previous errors
    clearFieldError(field);
    
    // Check if required field is empty
    if (field.hasAttribute('required') && !value) {
        showFieldError(field, `${getFieldLabel(field)} is required`);
        return false;
    }
    
    // Email validation
    if (fieldType === 'email' && value) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) {
            showFieldError(field, 'Please enter a valid email address');
            return false;
        }
    }
    
    // Phone validation (basic)
    if (fieldType === 'tel' && value) {
        const phoneRegex = /^[\+]?[1-9][\d]{0,15}$/;
        if (!phoneRegex.test(value.replace(/[\s\-\(\)]/g, ''))) {
            showFieldError(field, 'Please enter a valid phone number');
            return false;
        }
    }
    
    return true;
}

/**
 * Show field error
 */
function showFieldError(field, message) {
    field.classList.add('error');
    
    // Remove existing error message
    const existingError = field.parentNode.querySelector('.field-error');
    if (existingError) {
        existingError.remove();
    }
    
    // Add new error message
    const errorElement = document.createElement('div');
    errorElement.className = 'field-error';
    errorElement.textContent = message;
    field.parentNode.appendChild(errorElement);
}

/**
 * Clear field error
 */
function clearFieldError(field) {
    field.classList.remove('error');
    const errorElement = field.parentNode.querySelector('.field-error');
    if (errorElement) {
        errorElement.remove();
    }
}

/**
 * Get field label for error messages
 */
function getFieldLabel(field) {
    const label = document.querySelector(`label[for="${field.id}"]`);
    if (label) {
        return label.textContent.replace('*', '').trim();
    }
    return field.name.charAt(0).toUpperCase() + field.name.slice(1);
}

/**
 * Utility function for throttling scroll events
 */
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

/**
 * Add smooth transitions to elements
 */
function addTransitions() {
    const style = document.createElement('style');
    style.textContent = `
        .field-error {
            color: #ef4444;
            font-size: 0.875rem;
            margin-top: 0.25rem;
            animation: fadeInUp 0.3s ease;
        }
        
        input.error, textarea.error {
            border-color: #ef4444;
            box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1);
        }
        
        .scroll-animate {
            transition: all 0.6s cubic-bezier(0.16, 1, 0.3, 1);
        }
        
        .navbar.scrolled {
            background: rgba(255, 255, 255, 0.98);
            backdrop-filter: blur(20px);
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }
    `;
    document.head.appendChild(style);
}

// Initialize transitions
addTransitions();