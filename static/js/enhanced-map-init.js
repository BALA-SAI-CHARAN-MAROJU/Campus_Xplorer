/**
 * Enhanced Map System Initialization
 * Integrates the new enhanced mapping system with existing Campus Explorer functionality
 */

// Initialize enhanced mapping system when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize enhanced map manager
    window.enhancedMapManager = new EnhancedMapManager();
    
    // Set up integration with existing systems
    setupMapIntegration();
    
    // Override existing map functions with enhanced versions
    overrideExistingMapFunctions();
    
    // Set up enhanced event listeners
    setupEnhancedEventListeners();
});

function setupMapIntegration() {
    // Listen for campus changes from campus selector
    document.addEventListener('campusChanged', function(e) {
        if (window.enhancedMapManager) {
            window.enhancedMapManager.switchToCampus(e.detail.campusId);
        }
    });
    
    // Listen for navigation requests from events
    document.addEventListener('click', function(e) {
        if (e.target && e.target.classList.contains('navigate-btn')) {
            const venueName = e.target.getAttribute('data-venue-name');
            if (venueName && window.enhancedMapManager) {
                // Show map first
                const mapElement = document.getElementById('map');
                if (mapElement) {
                    mapElement.style.display = 'block';
                }
                
                // Navigate to location
                window.enhancedMapManager.navigateToLocation(venueName);
                
                // Scroll to map section
                const mapSection = document.getElementById('map-section');
                if (mapSection) {
                    mapSection.scrollIntoView({ behavior: 'smooth' });
                }
            }
        }
    });
}

function overrideExistingMapFunctions() {
    // Override the global navigateToVenue function
    if (typeof window.navigateToVenue !== 'undefined') {
        const originalNavigateToVenue = window.navigateToVenue;
        
        window.navigateToVenue = function(venueName) {
            if (window.enhancedMapManager && window.enhancedMapManager.isInitialized()) {
                // Use enhanced navigation
                window.enhancedMapManager.navigateToLocation(venueName);
            } else {
                // Fallback to original function
                originalNavigateToVenue(venueName);
            }
        };
    }
    
    // Override map initialization if needed
    if (typeof window.initMap !== 'undefined') {
        const originalInitMap = window.initMap;
        
        window.initMap = function() {
            if (window.enhancedMapManager) {
                // Use enhanced map initialization
                window.enhancedMapManager.initializeMapIfNeeded();
            } else {
                // Fallback to original function
                originalInitMap();
            }
        };
    }
}

function setupEnhancedEventListeners() {
    // Enhanced explore button functionality
    const exploreBtn = document.getElementById('explore-btn');
    if (exploreBtn) {
        exploreBtn.addEventListener('click', function() {
            const mapElement = document.getElementById('map');
            if (mapElement) {
                mapElement.style.display = 'block';
            }
            
            if (window.enhancedMapManager) {
                if (!window.enhancedMapManager.isInitialized()) {
                    window.enhancedMapManager.initializeMapIfNeeded();
                }
                
                // Show all campus locations
                setTimeout(() => {
                    if (window.enhancedMapManager.getMap()) {
                        window.enhancedMapManager.getMap().invalidateSize();
                    }
                }, 300);
            }
            
            // Scroll to map section
            const mapSection = document.getElementById('map-section');
            if (mapSection) {
                mapSection.scrollIntoView({ behavior: 'smooth' });
            }
        });
    }
    
    // Enhanced locate button functionality
    const locateBtn = document.getElementById('locate-btn');
    if (locateBtn) {
        locateBtn.addEventListener('click', function() {
            const mapElement = document.getElementById('map');
            if (mapElement) {
                mapElement.style.display = 'block';
            }
            
            if (window.enhancedMapManager) {
                if (!window.enhancedMapManager.isInitialized()) {
                    window.enhancedMapManager.initializeMapIfNeeded();
                }
                
                // Focus on main campus location
                setTimeout(() => {
                    const campusData = window.enhancedMapManager.getCampusData();
                    const currentCampus = window.enhancedMapManager.getCurrentCampus();
                    
                    if (campusData[currentCampus]) {
                        const map = window.enhancedMapManager.getMap();
                        if (map) {
                            map.invalidateSize();
                            map.setView(campusData[currentCampus].center_coordinates, 17);
                        }
                    }
                }, 300);
            }
        });
    }
    
    // Enhanced route finding — delegates to EnhancedMapManager.navigateToLocation
    const findRouteBtn = document.getElementById('findRouteBtn');
    if (findRouteBtn) {
        findRouteBtn.addEventListener('click', function() {
            const startLocation = document.getElementById('start-location').value;
            const endLocation   = document.getElementById('end-location').value;

            if (!startLocation || !endLocation) {
                showNotification('Please select both start and destination locations.', 'error');
                return;
            }
            if (startLocation === endLocation) {
                showNotification('Start and destination cannot be the same.', 'error');
                return;
            }

            // Show the map div before routing
            const mapEl = document.getElementById('map');
            if (mapEl) mapEl.style.display = 'block';

            if (window.enhancedMapManager) {
                window.enhancedMapManager.navigateToLocation(endLocation, startLocation);
            }
        });
    }
}

// Enhanced notification function with better styling
function showNotification(message, type = 'info') {
    // Remove existing notifications
    const existingNotifications = document.querySelectorAll('.enhanced-notification');
    existingNotifications.forEach(notification => notification.remove());
    
    // Create enhanced notification
    const notification = document.createElement('div');
    notification.className = `enhanced-notification ${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <div class="notification-icon">
                <i class="fas ${getNotificationIcon(type)}"></i>
            </div>
            <div class="notification-message">${message}</div>
            <button class="notification-close">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
    
    // Add styles
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: white;
        border-radius: 12px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
        z-index: 10000;
        max-width: 400px;
        animation: slideInRight 0.3s ease-out;
        border-left: 4px solid ${getNotificationColor(type)};
    `;
    
    // Add to document
    document.body.appendChild(notification);
    
    // Add close functionality
    const closeBtn = notification.querySelector('.notification-close');
    closeBtn.addEventListener('click', () => {
        notification.style.animation = 'slideOutRight 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    });
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (document.body.contains(notification)) {
            notification.style.animation = 'slideOutRight 0.3s ease-out';
            setTimeout(() => notification.remove(), 300);
        }
    }, 5000);
}

function getNotificationIcon(type) {
    const icons = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };
    return icons[type] || icons.info;
}

function getNotificationColor(type) {
    const colors = {
        success: '#10b981',
        error: '#ef4444',
        warning: '#f59e0b',
        info: '#3b82f6'
    };
    return colors[type] || colors.info;
}

// Add enhanced notification styles
const notificationStyles = document.createElement('style');
notificationStyles.textContent = `
    .enhanced-notification {
        font-family: 'Poppins', sans-serif;
    }
    
    .notification-content {
        display: flex;
        align-items: center;
        padding: 16px;
        gap: 12px;
    }
    
    .notification-icon {
        width: 24px;
        height: 24px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: var(--primary-color);
    }
    
    .notification-message {
        flex: 1;
        font-size: 14px;
        line-height: 1.4;
        color: var(--dark-color);
    }
    
    .notification-close {
        background: none;
        border: none;
        color: var(--gray-color);
        cursor: pointer;
        padding: 4px;
        border-radius: 4px;
        transition: all 0.2s ease;
    }
    
    .notification-close:hover {
        background: var(--light-color);
        color: var(--dark-color);
    }
    
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(notificationStyles);

// Make enhanced notification function globally available
window.showNotification = showNotification;