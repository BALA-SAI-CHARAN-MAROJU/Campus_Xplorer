/**
 * Enhanced Theme Manager
 * Handles theme switching, persistence, and smooth transitions
 * Feature: campus-explorer-enhancement, Task 8
 */

class ThemeManager {
    constructor() {
        this.currentTheme = 'light';
        this.themeToggleBtn = null;
        this.prefersDarkScheme = window.matchMedia('(prefers-color-scheme: dark)');
        this.transitionDuration = 300;
        
        this.init();
    }
    
    /**
     * Initialize theme manager
     */
    init() {
        this.loadSavedTheme();
        // Apply theme immediately (no animation on page load)
        document.documentElement.setAttribute('data-theme', this.currentTheme);
        if (this.currentTheme === 'dark') {
            document.body.classList.add('dark-theme');
        }
        this.setupThemeToggle();
        this.setupSystemThemeListener();
        this.updateMetaThemeColor(this.currentTheme);
    }
    
    /**
     * Load theme from localStorage or system preference
     */
    loadSavedTheme() {
        const savedTheme = localStorage.getItem('campus-explorer-theme');
        
        if (savedTheme && ['light', 'dark'].includes(savedTheme)) {
            this.currentTheme = savedTheme;
        } else {
            // Use system preference if no saved theme
            this.currentTheme = this.prefersDarkScheme.matches ? 'dark' : 'light';
        }
    }
    
    /**
     * Setup theme toggle button
     */
    setupThemeToggle() {
        this.themeToggleBtn = document.getElementById('theme-toggle');
        
        if (this.themeToggleBtn) {
            // Add both sun and moon icons
            this.themeToggleBtn.innerHTML = `
                <i class="fas fa-sun"></i>
                <i class="fas fa-moon" style="position: absolute;"></i>
            `;
            
            this.themeToggleBtn.addEventListener('click', () => {
                this.toggleTheme();
            });
            
            // Add keyboard support
            this.themeToggleBtn.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    this.toggleTheme();
                }
            });
            
            // Update button state
            this.updateToggleButton();
        }
    }
    
    /**
     * Setup system theme change listener
     */
    setupSystemThemeListener() {
        this.prefersDarkScheme.addEventListener('change', (e) => {
            // Only auto-switch if user hasn't manually set a preference
            const savedTheme = localStorage.getItem('campus-explorer-theme');
            if (!savedTheme) {
                const newTheme = e.matches ? 'dark' : 'light';
                this.applyTheme(newTheme, true);
            }
        });
    }
    
    /**
     * Toggle between light and dark themes
     */
    toggleTheme() {
        const newTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        this.applyTheme(newTheme, true);
        
        // Add haptic feedback on supported devices
        if (navigator.vibrate) {
            navigator.vibrate(50);
        }
        
        // Announce theme change for screen readers
        this.announceThemeChange(newTheme);
    }
    
    /**
     * Apply theme with smooth transition
     * @param {string} theme - Theme to apply ('light' or 'dark')
     * @param {boolean} animate - Whether to animate the transition
     */
    applyTheme(theme, animate = true) {
        if (!['light', 'dark'].includes(theme)) {
            console.warn(`Invalid theme: ${theme}. Using 'light' as fallback.`);
            theme = 'light';
        }
        
        const previousTheme = this.currentTheme;
        this.currentTheme = theme;
        
        if (animate) {
            this.animateThemeTransition(previousTheme, theme);
        } else {
            // Apply theme using both class and attribute for compatibility
            document.documentElement.setAttribute('data-theme', theme);
            if (theme === 'dark') {
                document.body.classList.add('dark-theme');
            } else {
                document.body.classList.remove('dark-theme');
            }
        }
        
        // Save theme preference
        localStorage.setItem('campus-explorer-theme', theme);
        
        // Update toggle button
        this.updateToggleButton();
        
        // Dispatch theme change event
        this.dispatchThemeChangeEvent(theme, previousTheme);
        
        // Update meta theme-color for mobile browsers
        this.updateMetaThemeColor(theme);
    }
    
    /**
     * Animate theme transition
     * @param {string} fromTheme - Previous theme
     * @param {string} toTheme - New theme
     */
    animateThemeTransition(fromTheme, toTheme) {
        // Add transition class to prevent flash
        document.body.classList.add('theme-switching');
        
        // Apply new theme using both class and attribute
        document.documentElement.setAttribute('data-theme', toTheme);
        if (toTheme === 'dark') {
            document.body.classList.add('dark-theme');
        } else {
            document.body.classList.remove('dark-theme');
        }
        
        // Create transition overlay for smooth effect
        const overlay = document.createElement('div');
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: ${toTheme === 'dark' ? '#020617' : '#ffffff'};
            opacity: 0;
            pointer-events: none;
            z-index: 9999;
            transition: opacity ${this.transitionDuration}ms ease-in-out;
        `;
        
        document.body.appendChild(overlay);
        
        // Trigger transition
        requestAnimationFrame(() => {
            overlay.style.opacity = '0.3';
            
            setTimeout(() => {
                overlay.style.opacity = '0';
                
                setTimeout(() => {
                    document.body.removeChild(overlay);
                    document.body.classList.remove('theme-switching');
                }, this.transitionDuration);
            }, this.transitionDuration / 2);
        });
    }
    
    /**
     * Update theme toggle button appearance
     */
    updateToggleButton() {
        if (!this.themeToggleBtn) return;
        
        const sunIcon = this.themeToggleBtn.querySelector('.fa-sun');
        const moonIcon = this.themeToggleBtn.querySelector('.fa-moon');
        
        if (this.currentTheme === 'dark') {
            this.themeToggleBtn.setAttribute('aria-label', 'Switch to light theme');
            this.themeToggleBtn.title = 'Switch to light theme';
            
            if (sunIcon) sunIcon.style.opacity = '0';
            if (moonIcon) moonIcon.style.opacity = '1';
        } else {
            this.themeToggleBtn.setAttribute('aria-label', 'Switch to dark theme');
            this.themeToggleBtn.title = 'Switch to dark theme';
            
            if (sunIcon) sunIcon.style.opacity = '1';
            if (moonIcon) moonIcon.style.opacity = '0';
        }
    }
    
    /**
     * Update meta theme-color for mobile browsers
     * @param {string} theme - Current theme
     */
    updateMetaThemeColor(theme) {
        let metaThemeColor = document.querySelector('meta[name="theme-color"]');
        
        if (!metaThemeColor) {
            metaThemeColor = document.createElement('meta');
            metaThemeColor.name = 'theme-color';
            document.head.appendChild(metaThemeColor);
        }
        
        const colors = {
            light: '#ffffff',
            dark: '#111827'
        };
        
        metaThemeColor.content = colors[theme];
    }
    
    /**
     * Dispatch theme change event
     * @param {string} newTheme - New theme
     * @param {string} previousTheme - Previous theme
     */
    dispatchThemeChangeEvent(newTheme, previousTheme) {
        const event = new CustomEvent('themechange', {
            detail: {
                theme: newTheme,
                previousTheme: previousTheme,
                timestamp: Date.now()
            }
        });
        
        document.dispatchEvent(event);
    }
    
    /**
     * Announce theme change for screen readers
     * @param {string} theme - New theme
     */
    announceThemeChange(theme) {
        const announcement = document.createElement('div');
        announcement.setAttribute('aria-live', 'polite');
        announcement.setAttribute('aria-atomic', 'true');
        announcement.style.cssText = `
            position: absolute;
            left: -10000px;
            width: 1px;
            height: 1px;
            overflow: hidden;
        `;
        announcement.textContent = `Theme switched to ${theme} mode`;
        
        document.body.appendChild(announcement);
        
        setTimeout(() => {
            document.body.removeChild(announcement);
        }, 1000);
    }
    
    /**
     * Get current theme
     * @returns {string} Current theme ('light' or 'dark')
     */
    getCurrentTheme() {
        return this.currentTheme;
    }
    
    /**
     * Set theme programmatically
     * @param {string} theme - Theme to set
     * @param {boolean} animate - Whether to animate transition
     */
    setTheme(theme, animate = true) {
        this.applyTheme(theme, animate);
    }
    
    /**
     * Check if dark theme is active
     * @returns {boolean} True if dark theme is active
     */
    isDarkTheme() {
        return this.currentTheme === 'dark';
    }
    
    /**
     * Get theme-aware color value
     * @param {string} lightColor - Color for light theme
     * @param {string} darkColor - Color for dark theme
     * @returns {string} Appropriate color for current theme
     */
    getThemeColor(lightColor, darkColor) {
        return this.currentTheme === 'dark' ? darkColor : lightColor;
    }
    
    /**
     * Add theme change listener
     * @param {Function} callback - Callback function
     */
    onThemeChange(callback) {
        document.addEventListener('themechange', callback);
    }
    
    /**
     * Remove theme change listener
     * @param {Function} callback - Callback function
     */
    offThemeChange(callback) {
        document.removeEventListener('themechange', callback);
    }
    
    /**
     * Destroy theme manager
     */
    destroy() {
        if (this.themeToggleBtn) {
            this.themeToggleBtn.removeEventListener('click', this.toggleTheme);
        }
        
        this.prefersDarkScheme.removeEventListener('change', this.setupSystemThemeListener);
    }
}

// Theme-aware utility functions
const ThemeUtils = {
    /**
     * Get CSS custom property value
     * @param {string} property - CSS custom property name
     * @returns {string} Property value
     */
    getCSSProperty(property) {
        return getComputedStyle(document.documentElement)
            .getPropertyValue(property)
            .trim();
    },
    
    /**
     * Set CSS custom property value
     * @param {string} property - CSS custom property name
     * @param {string} value - Property value
     */
    setCSSProperty(property, value) {
        document.documentElement.style.setProperty(property, value);
    },
    
    /**
     * Create theme-aware gradient
     * @param {string} direction - Gradient direction
     * @param {Array} colors - Array of color stops
     * @returns {string} CSS gradient string
     */
    createGradient(direction, colors) {
        const themeManager = window.themeManager;
        if (!themeManager) return '';
        
        const themeColors = colors.map(color => {
            if (typeof color === 'object') {
                return themeManager.getThemeColor(color.light, color.dark);
            }
            return color;
        });
        
        return `linear-gradient(${direction}, ${themeColors.join(', ')})`;
    },
    
    /**
     * Apply theme-aware styles to element
     * @param {HTMLElement} element - Target element
     * @param {Object} styles - Style object with light/dark variants
     */
    applyThemeStyles(element, styles) {
        const themeManager = window.themeManager;
        if (!themeManager || !element) return;
        
        Object.entries(styles).forEach(([property, value]) => {
            if (typeof value === 'object' && value.light && value.dark) {
                const themeValue = themeManager.getThemeColor(value.light, value.dark);
                element.style[property] = themeValue;
            } else {
                element.style[property] = value;
            }
        });
    }
};

// Initialize theme manager when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.themeManager = new ThemeManager();
    window.ThemeUtils = ThemeUtils;

    // Enable transitions after initial paint to prevent flash on load
    requestAnimationFrame(() => {
        requestAnimationFrame(() => {
            document.body.classList.add('theme-ready');
        });
    });
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ThemeManager, ThemeUtils };
}