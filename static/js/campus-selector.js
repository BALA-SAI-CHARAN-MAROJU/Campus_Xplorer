/**
 * Enhanced Campus Selector for Campus Explorer
 * Manages campus selection, state persistence, and dynamic data loading
 */

class CampusSelector {
    constructor() {
        this.campusSelect = document.getElementById('campus-select');
        this.campusInfo = document.getElementById('campus-info');
        this.currentCampus = null;
        this.campusData = {};
        this.eventCounts = {};
        
        this.init();
    }
    
    async init() {
        if (!this.campusSelect) {
            console.warn('Campus selector element not found');
            return;
        }
        
        await this.loadCampusData();
        this.setupEventListeners();
        this.loadSavedCampus();
        this.setupCampusChangeHandlers();
    }
    
    async loadCampusData() {
        try {
            // Load campus data from API
            const response = await fetch('/api/campuses');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            this.campusData = {};
            
            // Populate campus selector
            this.campusSelect.innerHTML = '<option value="">Select a campus...</option>';
            
            data.campuses.forEach(campus => {
                this.campusData[campus.id] = campus;
                
                const option = document.createElement('option');
                option.value = campus.id;
                option.textContent = campus.display_name;
                option.dataset.locations = Object.keys(campus.locations || {}).length;
                
                this.campusSelect.appendChild(option);
            });
            
            // Load event counts for each campus
            await this.loadEventCounts();
            
        } catch (error) {
            console.error('Error loading campus data:', error);
            this.showFallbackCampuses();
        }
    }
    
    async loadEventCounts() {
        try {
            const response = await fetch('/api/events/counts');
            if (response.ok) {
                const data = await response.json();
                this.eventCounts = data.counts || {};
            }
        } catch (error) {
            console.error('Error loading event counts:', error);
        }
    }
    
    showFallbackCampuses() {
        // Fallback campus data if API fails
        const fallbackCampuses = [
            { id: 'amrita-chennai', name: 'Amrita Chennai Campus', locations: 16 },
            { id: 'amrita-coimbatore', name: 'Amrita Coimbatore Campus', locations: 12 },
            { id: 'amrita-bengaluru', name: 'Amrita Bengaluru Campus', locations: 10 },
            { id: 'amrita-amritapuri', name: 'Amrita Amritapuri Campus', locations: 14 }
        ];
        
        this.campusSelect.innerHTML = '<option value="">Select a campus...</option>';
        
        fallbackCampuses.forEach(campus => {
            const option = document.createElement('option');
            option.value = campus.id;
            option.textContent = campus.name;
            option.dataset.locations = campus.locations;
            
            this.campusSelect.appendChild(option);
        });
    }
    
    setupEventListeners() {
        // Campus selection change
        this.campusSelect.addEventListener('change', (e) => {
            this.handleCampusChange(e.target.value);
        });
        
        // Enhanced styling on focus/blur
        this.campusSelect.addEventListener('focus', () => {
            this.campusSelect.style.borderColor = 'var(--primary-color)';
            this.campusSelect.style.boxShadow = '0 0 0 3px rgba(79, 70, 229, 0.1)';
            this.campusSelect.style.transform = 'translateY(-2px)';
        });
        
        this.campusSelect.addEventListener('blur', () => {
            this.campusSelect.style.borderColor = 'var(--border-color)';
            this.campusSelect.style.boxShadow = 'none';
            this.campusSelect.style.transform = 'translateY(0)';
        });
    }
    
    handleCampusChange(campusId) {
        if (!campusId) {
            this.hideCampusInfo();
            this.currentCampus = null;
            this.saveCampusPreference('');
            return;
        }
        
        this.currentCampus = campusId;
        this.saveCampusPreference(campusId);
        this.showCampusInfo(campusId);
        this.notifyCampusChange(campusId);
        
        // Update all campus-dependent components
        this.updateLocationDropdowns(campusId);
        this.updateEventFilters(campusId);
        this.updateMapView(campusId);
        this.updateChatContext(campusId);
    }
    
    showCampusInfo(campusId) {
        const campus = this.campusData[campusId];
        if (!campus) return;
        
        const campusInfo = this.campusInfo;
        const details = campusInfo.querySelector('.campus-details');
        
        // Update campus information
        const title = details.querySelector('h4');
        const description = details.querySelector('p');
        const locationCount = details.querySelector('.location-count');
        const eventCount = details.querySelector('.event-count');
        
        title.textContent = campus.display_name;
        description.textContent = `Explore ${campus.display_name} with interactive maps, events, and AI assistance.`;
        locationCount.textContent = Object.keys(campus.locations || {}).length;
        eventCount.textContent = this.eventCounts[campusId] || 0;
        
        // Show with animation
        campusInfo.style.display = 'block';
        campusInfo.style.opacity = '0';
        campusInfo.style.transform = 'translateY(10px)';
        
        setTimeout(() => {
            campusInfo.style.transition = 'all 0.3s ease';
            campusInfo.style.opacity = '1';
            campusInfo.style.transform = 'translateY(0)';
        }, 10);
    }
    
    hideCampusInfo() {
        if (this.campusInfo) {
            this.campusInfo.style.opacity = '0';
            this.campusInfo.style.transform = 'translateY(-10px)';
            
            setTimeout(() => {
                this.campusInfo.style.display = 'none';
            }, 300);
        }
    }
    
    updateLocationDropdowns(campusId) {
        const campus = this.campusData[campusId];
        if (!campus) return;
        
        // Update route form dropdowns
        const startLocation = document.getElementById('start-location');
        const endLocation = document.getElementById('end-location');
        const eventVenue = document.getElementById('event-venue');
        
        if (startLocation && endLocation) {
            const locations = Object.keys(campus.locations || {});
            
            // Clear existing options
            startLocation.innerHTML = '<option value="">Select start location</option>';
            endLocation.innerHTML = '<option value="">Select destination</option>';
            
            // Add campus-specific locations
            locations.forEach(location => {
                const startOption = document.createElement('option');
                startOption.value = location;
                startOption.textContent = location;
                startLocation.appendChild(startOption);
                
                const endOption = document.createElement('option');
                endOption.value = location;
                endOption.textContent = location;
                endLocation.appendChild(endOption);
            });
        }
        
        // Update event venue dropdown
        if (eventVenue) {
            const locations = Object.keys(campus.locations || {});
            
            eventVenue.innerHTML = '<option value="">Select venue</option>';
            locations.forEach(location => {
                const option = document.createElement('option');
                option.value = location;
                option.textContent = location;
                eventVenue.appendChild(option);
            });
        }
    }
    
    updateEventFilters(campusId) {
        // Trigger event list refresh with campus filter
        if (window.eventsManager) {
            window.eventsManager.filterByCampus(campusId);
        }
        
        // Update event form campus context
        const eventForm = document.getElementById('event-form');
        if (eventForm) {
            eventForm.dataset.campus = campusId;
        }
    }
    
    updateMapView(campusId) {
        // Update the legacy map.js currentCampus variable
        if (typeof currentCampus !== 'undefined') {
            // eslint-disable-next-line no-global-assign
            window._mapCurrentCampus = campusId;
        }
        // Trigger via the enhanced map manager if available
        if (window.enhancedMapManager) {
            window.enhancedMapManager.switchToCampus(campusId);
        }
        if (window.mapManager) {
            window.mapManager.switchToCampus(campusId);
        }
    }
    
    updateChatContext(campusId) {
        // Update chat context for AI assistant
        if (window.enhancedChat) {
            window.enhancedChat.currentContext.campus = campusId;
        }
    }
    
    notifyCampusChange(campusId) {
        // Dispatch custom event for other components
        const event = new CustomEvent('campusChanged', {
            detail: {
                campusId: campusId,
                campusData: this.campusData[campusId]
            }
        });
        
        document.dispatchEvent(event);
        
        // Show notification
        this.showNotification(`Switched to ${this.campusData[campusId]?.display_name}`, 'success');
    }
    
    saveCampusPreference(campusId) {
        try {
            localStorage.setItem('selectedCampus', campusId);
            
            // Also save to user preferences if authenticated
            if (window.userManager && window.userManager.isAuthenticated()) {
                window.userManager.updatePreference('preferred_campus', campusId);
            }
        } catch (error) {
            console.error('Error saving campus preference:', error);
        }
    }
    
    loadSavedCampus() {
        try {
            // Try to load from user preferences first
            let savedCampus = null;
            
            if (window.userManager && window.userManager.isAuthenticated()) {
                savedCampus = window.userManager.getPreference('preferred_campus');
            }
            
            // Fallback to localStorage
            if (!savedCampus) {
                savedCampus = localStorage.getItem('selectedCampus');
            }
            
            // Default to Chennai if nothing saved
            if (!savedCampus) {
                savedCampus = 'amrita-chennai';
            }
            
            // Set the campus if it exists in options
            if (savedCampus && this.campusSelect.querySelector(`option[value="${savedCampus}"]`)) {
                this.campusSelect.value = savedCampus;
                this.handleCampusChange(savedCampus);
            }
        } catch (error) {
            console.error('Error loading saved campus:', error);
            // Default to Chennai
            this.campusSelect.value = 'amrita-chennai';
            this.handleCampusChange('amrita-chennai');
        }
    }
    
    setupCampusChangeHandlers() {
        // Listen for campus changes from other components
        document.addEventListener('requestCampusChange', (e) => {
            const campusId = e.detail.campusId;
            if (campusId && this.campusSelect.querySelector(`option[value="${campusId}"]`)) {
                this.campusSelect.value = campusId;
                this.handleCampusChange(campusId);
            }
        });

        // Refresh campus data when a manager adds/edits/deletes a location in another tab
        window.addEventListener('storage', async (e) => {
            if (e.key !== 'locationsUpdated') return;
            try {
                const payload = JSON.parse(e.newValue);
                await this._refreshAfterLocationChange(payload.campusId);
            } catch (err) {
                console.warn('CampusSelector: failed to refresh after location update:', err);
            }
        });

        // Same-tab: CustomEvent dispatched by locations.html
        window.addEventListener('locationsUpdated', async (e) => {
            try {
                await this._refreshAfterLocationChange(e.detail.campusId);
            } catch (err) {
                console.warn('CampusSelector: locationsUpdated event error:', err);
            }
        });

        // Same-tab: BroadcastChannel (modern browsers)
        try {
            const bc = new BroadcastChannel('campus_locations');
            bc.onmessage = async (e) => {
                try {
                    await this._refreshAfterLocationChange(e.data.campusId);
                } catch (err) {
                    console.warn('CampusSelector: BroadcastChannel error:', err);
                }
            };
        } catch (e) { /* BroadcastChannel not supported */ }
    }
    
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle'}"></i>
                <span>${message}</span>
            </div>
            <button class="close-btn" onclick="this.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.classList.add('fade-out');
                setTimeout(() => {
                    notification.remove();
                }, 300);
            }
        }, 3000);
    }
    
    /**
     * Reload campus data from API and refresh map + dropdowns for the given campus.
     * Called whenever a location is added, edited, or deleted.
     */
    async _refreshAfterLocationChange(campusId) {
        await this.loadCampusData();
        if (this.currentCampus === campusId) {
            this.showCampusInfo(this.currentCampus);
            this.updateLocationDropdowns(this.currentCampus);
        }
        // Refresh the map markers with the new location data
        if (window.enhancedMapManager && window.enhancedMapManager.isInitialized()) {
            await window.enhancedMapManager.loadCampusData();
            if (window.enhancedMapManager.getCurrentCampus() === campusId) {
                window.enhancedMapManager.addCampusMarkers();
            }
        }
    }

    // Public methods
    getCurrentCampus() {
        return this.currentCampus;
    }
    
    getCampusData(campusId = null) {
        return campusId ? this.campusData[campusId] : this.campusData;
    }
    
    switchToCampus(campusId) {
        if (this.campusSelect.querySelector(`option[value="${campusId}"]`)) {
            this.campusSelect.value = campusId;
            this.handleCampusChange(campusId);
        }
    }
    
    refreshCampusData() {
        return this.loadCampusData();
    }
}

// Initialize campus selector when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.campusSelector = new CampusSelector();
});

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CampusSelector;
}