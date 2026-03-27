/**
 * UI Feedback and Interactive Elements Manager
 * Handles loading states, form validation, and user feedback
 * Feature: campus-explorer-enhancement, Task 9
 */

class UIFeedbackManager {
    constructor() {
        this.loadingStates = new Map();
        this.notifications = [];
        this.tooltips = new Map();
        
        this.init();
    }
    
    /**
     * Initialize UI feedback system
     */
    init() {
        this.setupFormValidation();
        this.setupInteractiveElements();
        this.setupLoadingStates();
        this.setupTooltips();
        this.setupKeyboardNavigation();
        this.setupTouchOptimizations();
    }
    
    /**
     * Setup form validation with real-time feedback
     */
    setupFormValidation() {
        const forms = document.querySelectorAll('form');
        
        forms.forEach(form => {
            const inputs = form.querySelectorAll('input, select, textarea');
            
            inputs.forEach(input => {
                // Add real-time validation
                input.addEventListener('input', (e) => {
                    this.validateField(e.target);
                });
                
                input.addEventListener('blur', (e) => {
                    this.validateField(e.target);
                });
                
                input.addEventListener('focus', (e) => {
                    this.clearFieldError(e.target);
                });
            });
            
            // Enhanced form submission
            form.addEventListener('submit', (e) => {
                if (!this.validateForm(form)) {
                    e.preventDefault();
                    this.showFormErrors(form);
                }
            });
        });
    }
    
    /**
     * Validate individual form field
     * @param {HTMLElement} field - Form field to validate
     */
    validateField(field) {
        const value = field.value.trim();
        const type = field.type;
        const required = field.hasAttribute('required');
        
        let isValid = true;
        let message = '';
        
        // Required field validation
        if (required && !value) {
            isValid = false;
            message = 'This field is required';
        }
        
        // Type-specific validation
        if (value && !isValid !== false) {
            switch (type) {
                case 'email':
                    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                    if (!emailRegex.test(value)) {
                        isValid = false;
                        message = 'Please enter a valid email address';
                    }
                    break;
                    
                case 'tel':
                    const phoneRegex = /^[\+]?[1-9][\d]{0,15}$/;
                    if (!phoneRegex.test(value.replace(/\s/g, ''))) {
                        isValid = false;
                        message = 'Please enter a valid phone number';
                    }
                    break;
                    
                case 'url':
                    try {
                        new URL(value);
                    } catch {
                        isValid = false;
                        message = 'Please enter a valid URL';
                    }
                    break;
                    
                case 'date':
                    const date = new Date(value);
                    if (isNaN(date.getTime())) {
                        isValid = false;
                        message = 'Please enter a valid date';
                    }
                    break;
                    
                case 'time':
                    const timeRegex = /^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$/;
                    if (!timeRegex.test(value)) {
                        isValid = false;
                        message = 'Please enter a valid time (HH:MM)';
                    }
                    break;
            }
        }
        
        // Custom validation attributes
        if (isValid && value) {
            const minLength = field.getAttribute('minlength');
            if (minLength && value.length < parseInt(minLength)) {
                isValid = false;
                message = `Minimum ${minLength} characters required`;
            }
            
            const maxLength = field.getAttribute('maxlength');
            if (maxLength && value.length > parseInt(maxLength)) {
                isValid = false;
                message = `Maximum ${maxLength} characters allowed`;
            }
            
            const pattern = field.getAttribute('pattern');
            if (pattern && !new RegExp(pattern).test(value)) {
                isValid = false;
                message = field.getAttribute('title') || 'Invalid format';
            }
        }
        
        this.updateFieldFeedback(field, isValid, message);
        return isValid;
    }
    
    /**
     * Update field visual feedback
     * @param {HTMLElement} field - Form field
     * @param {boolean} isValid - Validation result
     * @param {string} message - Feedback message
     */
    updateFieldFeedback(field, isValid, message) {
        const formGroup = field.closest('.form-group');
        if (!formGroup) return;
        
        // Remove existing classes
        field.classList.remove('error', 'success');
        
        // Remove existing feedback
        const existingFeedback = formGroup.querySelector('.form-feedback');
        if (existingFeedback) {
            existingFeedback.remove();
        }
        
        if (field.value.trim()) {
            if (isValid) {
                field.classList.add('success');
                this.addFieldFeedback(formGroup, 'success', '✓ Valid');
            } else {
                field.classList.add('error');
                this.addFieldFeedback(formGroup, 'error', message);
            }
        }
    }
    
    /**
     * Add feedback message to form group
     * @param {HTMLElement} formGroup - Form group element
     * @param {string} type - Feedback type (error, success, warning)
     * @param {string} message - Feedback message
     */
    addFieldFeedback(formGroup, type, message) {
        const feedback = document.createElement('div');
        feedback.className = `form-feedback ${type}`;
        
        const icon = document.createElement('i');
        icon.className = type === 'error' ? 'fas fa-exclamation-circle' :
                        type === 'success' ? 'fas fa-check-circle' :
                        'fas fa-info-circle';
        
        const text = document.createElement('span');
        text.textContent = message;
        
        feedback.appendChild(icon);
        feedback.appendChild(text);
        formGroup.appendChild(feedback);
    }
    
    /**
     * Clear field error state
     * @param {HTMLElement} field - Form field
     */
    clearFieldError(field) {
        field.classList.remove('error');
        const formGroup = field.closest('.form-group');
        if (formGroup) {
            const errorFeedback = formGroup.querySelector('.form-feedback.error');
            if (errorFeedback) {
                errorFeedback.remove();
            }
        }
    }
    
    /**
     * Validate entire form
     * @param {HTMLFormElement} form - Form to validate
     * @returns {boolean} Form validity
     */
    validateForm(form) {
        const fields = form.querySelectorAll('input, select, textarea');
        let isValid = true;
        
        fields.forEach(field => {
            if (!this.validateField(field)) {
                isValid = false;
            }
        });
        
        return isValid;
    }
    
    /**
     * Show form-level errors
     * @param {HTMLFormElement} form - Form with errors
     */
    showFormErrors(form) {
        const firstError = form.querySelector('.error');
        if (firstError) {
            firstError.focus();
            firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
        
        this.showNotification('Please correct the errors below', 'error');
    }
    
    /**
     * Setup interactive elements with feedback
     */
    setupInteractiveElements() {
        // Add interactive class to clickable elements
        const interactiveElements = document.querySelectorAll(
            'button, .btn, [role="button"], .interactive'
        );
        
        interactiveElements.forEach(element => {
            if (!element.classList.contains('interactive')) {
                element.classList.add('interactive');
            }
            
            // Add ripple effect on click
            element.addEventListener('click', (e) => {
                this.createRippleEffect(e);
            });
        });
    }
    
    /**
     * Create ripple effect on element click
     * @param {Event} event - Click event
     */
    createRippleEffect(event) {
        const element = event.currentTarget;
        const rect = element.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = event.clientX - rect.left - size / 2;
        const y = event.clientY - rect.top - size / 2;
        
        const ripple = document.createElement('span');
        ripple.style.cssText = `
            position: absolute;
            width: ${size}px;
            height: ${size}px;
            left: ${x}px;
            top: ${y}px;
            background: rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            transform: scale(0);
            animation: ripple 0.6s linear;
            pointer-events: none;
        `;
        
        element.style.position = 'relative';
        element.style.overflow = 'hidden';
        element.appendChild(ripple);
        
        setTimeout(() => {
            ripple.remove();
        }, 600);
    }
    
    /**
     * Setup loading states management
     */
    setupLoadingStates() {
        // Add CSS for ripple animation
        if (!document.getElementById('ripple-styles')) {
            const style = document.createElement('style');
            style.id = 'ripple-styles';
            style.textContent = `
                @keyframes ripple {
                    to {
                        transform: scale(4);
                        opacity: 0;
                    }
                }
            `;
            document.head.appendChild(style);
        }
    }
    
    /**
     * Show loading state on element
     * @param {HTMLElement|string} element - Element or selector
     * @param {string} type - Loading type (spinner, dots, pulse)
     */
    showLoading(element, type = 'spinner') {
        const el = typeof element === 'string' ? 
                   document.querySelector(element) : element;
        
        if (!el) return;
        
        const loadingId = Math.random().toString(36).substr(2, 9);
        
        // Store original content
        this.loadingStates.set(loadingId, {
            element: el,
            originalContent: el.innerHTML,
            originalDisabled: el.disabled
        });
        
        // Disable element if it's interactive
        if (el.tagName === 'BUTTON' || el.tagName === 'INPUT') {
            el.disabled = true;
        }
        
        // Add loading content
        let loadingHTML = '';
        switch (type) {
            case 'spinner':
                loadingHTML = '<span class="loading-spinner"></span>';
                break;
            case 'dots':
                loadingHTML = '<span class="loading-dots"><span></span><span></span><span></span></span>';
                break;
            case 'pulse':
                el.classList.add('loading-pulse');
                return loadingId;
        }
        
        if (el.tagName === 'BUTTON') {
            el.innerHTML = loadingHTML + ' Loading...';
        } else {
            el.innerHTML = loadingHTML;
        }
        
        return loadingId;
    }
    
    /**
     * Hide loading state
     * @param {string} loadingId - Loading state ID
     */
    hideLoading(loadingId) {
        const loadingState = this.loadingStates.get(loadingId);
        if (!loadingState) return;
        
        const { element, originalContent, originalDisabled } = loadingState;
        
        // Restore original content
        element.innerHTML = originalContent;
        element.disabled = originalDisabled;
        element.classList.remove('loading-pulse');
        
        // Clean up
        this.loadingStates.delete(loadingId);
    }
    
    /**
     * Show progress indicator
     * @param {HTMLElement|string} container - Container element
     * @param {number} progress - Progress percentage (0-100)
     * @param {string} label - Progress label
     */
    showProgress(container, progress = 0, label = '') {
        const el = typeof container === 'string' ? 
                   document.querySelector(container) : container;
        
        if (!el) return;
        
        let progressBar = el.querySelector('.progress-bar');
        if (!progressBar) {
            progressBar = document.createElement('div');
            progressBar.className = 'progress-bar';
            progressBar.innerHTML = `
                <div class="progress-bar-fill"></div>
                <div class="progress-label"></div>
            `;
            el.appendChild(progressBar);
        }
        
        const fill = progressBar.querySelector('.progress-bar-fill');
        const labelEl = progressBar.querySelector('.progress-label');
        
        fill.style.width = `${Math.max(0, Math.min(100, progress))}%`;
        labelEl.textContent = label;
        
        // Add completion animation
        if (progress >= 100) {
            setTimeout(() => {
                progressBar.style.opacity = '0';
                setTimeout(() => {
                    progressBar.remove();
                }, 300);
            }, 1000);
        }
    }
    
    /**
     * Setup tooltip system
     */
    setupTooltips() {
        const tooltipElements = document.querySelectorAll('[data-tooltip]');
        
        tooltipElements.forEach(element => {
            const tooltipText = element.getAttribute('data-tooltip');
            const tooltipPosition = element.getAttribute('data-tooltip-position') || 'top';
            
            this.createTooltip(element, tooltipText, tooltipPosition);
        });
    }
    
    /**
     * Create tooltip for element
     * @param {HTMLElement} element - Target element
     * @param {string} text - Tooltip text
     * @param {string} position - Tooltip position
     */
    createTooltip(element, text, position = 'top') {
        const tooltip = document.createElement('div');
        tooltip.className = 'tooltip-content';
        tooltip.textContent = text;
        
        element.style.position = 'relative';
        element.appendChild(tooltip);
        
        // Position tooltip
        switch (position) {
            case 'bottom':
                tooltip.style.top = '125%';
                tooltip.style.bottom = 'auto';
                break;
            case 'left':
                tooltip.style.right = '125%';
                tooltip.style.left = 'auto';
                tooltip.style.top = '50%';
                tooltip.style.transform = 'translateY(-50%)';
                break;
            case 'right':
                tooltip.style.left = '125%';
                tooltip.style.right = 'auto';
                tooltip.style.top = '50%';
                tooltip.style.transform = 'translateY(-50%)';
                break;
        }
        
        this.tooltips.set(element, tooltip);
    }
    
    /**
     * Setup keyboard navigation enhancements
     */
    setupKeyboardNavigation() {
        // Focus management
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                document.body.classList.add('keyboard-navigation');
            }
        });
        
        document.addEventListener('mousedown', () => {
            document.body.classList.remove('keyboard-navigation');
        });
        
        // Skip links for accessibility
        this.addSkipLinks();
    }
    
    /**
     * Add skip navigation links
     */
    addSkipLinks() {
        const skipLinks = document.createElement('div');
        skipLinks.className = 'skip-links';
        skipLinks.innerHTML = `
            <a href="#main-content" class="skip-link">Skip to main content</a>
            <a href="#navigation" class="skip-link">Skip to navigation</a>
        `;
        
        const style = document.createElement('style');
        style.textContent = `
            .skip-links {
                position: absolute;
                top: -100px;
                left: 0;
                z-index: 10000;
            }
            .skip-link {
                position: absolute;
                top: 0;
                left: 0;
                background: var(--primary-color);
                color: white;
                padding: 8px 16px;
                text-decoration: none;
                border-radius: 0 0 4px 0;
                transition: top 0.3s;
            }
            .skip-link:focus {
                top: 0;
            }
        `;
        
        document.head.appendChild(style);
        document.body.insertBefore(skipLinks, document.body.firstChild);
    }
    
    /**
     * Setup touch optimizations
     */
    setupTouchOptimizations() {
        // Increase touch targets on mobile
        if ('ontouchstart' in window) {
            const touchElements = document.querySelectorAll('button, .btn, a, input, select');
            
            touchElements.forEach(element => {
                const rect = element.getBoundingClientRect();
                if (rect.height < 44 || rect.width < 44) {
                    element.style.minHeight = '44px';
                    element.style.minWidth = '44px';
                }
            });
        }
    }
    
    /**
     * Show notification
     * @param {string} message - Notification message
     * @param {string} type - Notification type (success, error, info, warning)
     * @param {number} duration - Auto-hide duration in ms
     */
    showNotification(message, type = 'info', duration = 5000) {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        
        const icon = document.createElement('i');
        icon.className = type === 'success' ? 'fas fa-check-circle' :
                        type === 'error' ? 'fas fa-exclamation-circle' :
                        type === 'warning' ? 'fas fa-exclamation-triangle' :
                        'fas fa-info-circle';
        
        const content = document.createElement('div');
        content.className = 'notification-content';
        content.appendChild(icon);
        content.appendChild(document.createTextNode(message));
        
        const closeBtn = document.createElement('button');
        closeBtn.className = 'close-btn';
        closeBtn.innerHTML = '<i class="fas fa-times"></i>';
        closeBtn.onclick = () => this.hideNotification(notification);
        
        notification.appendChild(content);
        notification.appendChild(closeBtn);
        
        document.body.appendChild(notification);
        this.notifications.push(notification);
        
        // Auto-hide
        if (duration > 0) {
            setTimeout(() => {
                this.hideNotification(notification);
            }, duration);
        }
        
        return notification;
    }
    
    /**
     * Hide notification
     * @param {HTMLElement} notification - Notification element
     */
    hideNotification(notification) {
        notification.classList.add('fade-out');
        
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
            
            const index = this.notifications.indexOf(notification);
            if (index > -1) {
                this.notifications.splice(index, 1);
            }
        }, 300);
    }
    
    /**
     * Clear all notifications
     */
    clearNotifications() {
        this.notifications.forEach(notification => {
            this.hideNotification(notification);
        });
    }
}

// Initialize UI feedback manager
document.addEventListener('DOMContentLoaded', () => {
    window.uiFeedback = new UIFeedbackManager();
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = UIFeedbackManager;
}