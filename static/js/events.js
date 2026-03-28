// Initialize events variables
let events = [];
let venues = [];

// Import predefined locations from script.js
// This needs to be defined here since it's used in populateVenueDropdown
const predefinedLocations = {
    "Academic Block": [13.263018, 80.027427],
    "Library": [13.262621, 80.026525],
    "Canteen": [13.262856, 80.028401],
    "Pond": [13.262198, 80.027673],
    "AVV Gym for Girls": [13.262141, 80.026830],
    "Chennai": [13.080917019874969, 80.26358605588356],
    "Delhi": [28.675015901626473, 77.21675859763418],
    "Mumbai": [19.07598369140625, 72.877685546875],
    "Kolkata": [22.5726455078125, 88.3638671875],
    "Hyderabad": [17.432607421875, 78.4736328125],
    "Bengaluru": [12.971593933105469, 77.5945263671875],
    "Junior Girls Hostel": [13.261993, 80.026421],
    "Junior Boys Hostel": [13.261805, 80.028076],
    "Lab Block": [13.262768, 80.028147],
    "Mechanical Lab": [13.261205, 80.027488],
    "Volley Ball Court": [13.261009, 80.027530],
    "Basket Ball Court": [13.260909, 80.027256],
    "Senior Girls Hostel": [13.260658, 80.028184],
    "Senior Boys Hostel": [13.260550, 80.027272],
    "2nd Year Boys Hostel": [13.259570, 80.026694],
    "Amrita Indoor Stadium": [13.259880, 80.025990],
    "AVV Gym for Boys": [13.260146, 80.026143],
    "AVV Ground": [13.259708, 80.025416],
    "Amrita Vishwa Vidyapeetham": [13.2630, 80.0274],
    // Additional campuses / colleges
    "Amrita Coimbatore Campus": [11.0168, 76.9558],
    "Amrita Bengaluru Campus": [12.9663, 77.6069],
    "Amrita Amritapuri Campus": [9.0884, 76.4890]
};

// Initialize events when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    fetchEvents();
    setupEventListeners();
    
    // Initialize AOS animation library
    if (typeof AOS !== 'undefined') {
        AOS.init({
            duration: 800,
            easing: 'ease-in-out',
            once: true
        });
    }
    
    // Auto-refresh events every 5 minutes to check for expired events
    setInterval(() => {
        fetchEvents();
    }, 5 * 60 * 1000); // 5 minutes
    
    // Check for expired events every minute and update display
    setInterval(() => {
        displayEvents();
    }, 60 * 1000); // 1 minute
});

// Fetch events from the API
async function fetchEvents() {
    try {
        // Show loading state
        document.getElementById('events-list').innerHTML = '<div class="loading-spinner"><i class="fas fa-circle-notch fa-spin"></i> Loading events...</div>';
        document.getElementById('expiring-events-list').innerHTML = '<div class="loading-spinner"><i class="fas fa-circle-notch fa-spin"></i> Loading events...</div>';
        
        // Fetch all events
        const eventsResponse = await fetch('/api/events');
        events = await eventsResponse.json();
        
        // Fetch locations for venue selection
        const locationsResponse = await fetch('/api/locations');
        venues = await locationsResponse.json();
        
        // Populate venue dropdown
        populateVenueDropdown();
        
        // Display events
        displayEvents();
    } catch (error) {
        console.error('Error fetching events:', error);
        showNotification('Failed to load events. Please try again later.', 'error');
    }
}

// Populate venue dropdown
function populateVenueDropdown() {
    const venueSelect = document.getElementById('event-venue');
    
    // Clear existing options except the first one
    while (venueSelect.options.length > 1) {
        venueSelect.remove(1);
    }
    
    // Add options from predefined locations
    if (typeof predefinedLocations !== 'undefined') {
        Object.keys(predefinedLocations).forEach(name => {
            const option = document.createElement('option');
            option.value = name;
            option.textContent = name;
            venueSelect.appendChild(option);
        });
    }
}

// Display events in the events list
function displayEvents() {
    const now = new Date();
    
    // 1. Display upcoming events (sorted by creation time - newest first)
    const upcomingEventsList = document.getElementById('events-list');
    upcomingEventsList.innerHTML = '';
    
    if (events.length === 0) {
        upcomingEventsList.innerHTML = '<p class="no-events">No events found.</p>';
    } else {
        // Filter for future and current events only (not expired)
        const upcomingEvents = events.filter(event => {
            const eventDate = new Date(`${event.date}T${event.time}`);
            // Show events that haven't started yet OR are currently happening
            const eventEndTime = event.end_time ? new Date(`${event.date}T${event.end_time}`) : eventDate;
            return eventEndTime > now;
        });
        
        // Sort events by creation time (newest first)
        const sortedByCreation = [...upcomingEvents].sort((a, b) => {
            return new Date(b.created_at) - new Date(a.created_at);
        });
        
        if (sortedByCreation.length === 0) {
            upcomingEventsList.innerHTML = '<p class="no-events">No upcoming events found.</p>';
        } else {
            // Add events with staggered animation delay
            sortedByCreation.forEach((event, index) => {
                setTimeout(() => {
                    const eventCard = createEventCard(event);
                    upcomingEventsList.appendChild(eventCard);
                }, index * 100); // Stagger by 100ms
            });
        }
    }
    
    // 2. Display expiring soon events (sorted by date/time - soonest first)
    const expiringEventsList = document.getElementById('expiring-events-list');
    expiringEventsList.innerHTML = '';
    
    if (events.length === 0) {
        expiringEventsList.innerHTML = '<p class="no-events">No events found.</p>';
    } else {
        // Filter for future and current events only (not expired)
        const upcomingEvents = events.filter(event => {
            const eventDate = new Date(`${event.date}T${event.time}`);
            // Show events that haven't started yet OR are currently happening
            const eventEndTime = event.end_time ? new Date(`${event.date}T${event.end_time}`) : eventDate;
            return eventEndTime > now;
        });
        
        // Sort events by expiry time (soonest first)
        const sortedByExpiry = [...upcomingEvents].sort((a, b) => {
            const aDate = new Date(`${a.date}T${a.time}`);
            const bDate = new Date(`${b.date}T${b.time}`);
            return aDate - bDate;
        });
        
        if (sortedByExpiry.length === 0) {
            expiringEventsList.innerHTML = '<p class="no-events">No upcoming events found.</p>';
        } else {
            // Add events with staggered animation delay
            sortedByExpiry.forEach((event, index) => {
                setTimeout(() => {
                    const eventCard = createEventCard(event);
                    expiringEventsList.appendChild(eventCard);
                }, index * 100); // Stagger by 100ms
            });
        }
    }
}

// Create an event card
function createEventCard(event) {
    const eventDate = new Date(`${event.date}T${event.time}`);
    const now = new Date();
    const timeLeft = eventDate - now;
    
    // Format date and time
    const formattedDate = new Date(event.date).toLocaleDateString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
    
    const formattedTime = new Date(`${event.date}T${event.time}`).toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit'
    });
    
    // Format end time if available
    let formattedEndTime = '';
    if (event.end_time) {
        formattedEndTime = new Date(`${event.date}T${event.end_time}`).toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit'
        });
    }
    
    // Calculate time remaining
    let timeRemaining = '';
    if (timeLeft > 0) {
        const days = Math.floor(timeLeft / (1000 * 60 * 60 * 24));
        const hours = Math.floor((timeLeft % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((timeLeft % (1000 * 60 * 60)) / (1000 * 60));
        
        if (days > 0) {
            timeRemaining = `${days} day${days !== 1 ? 's' : ''} ${hours} hour${hours !== 1 ? 's' : ''}`;
        } else if (hours > 0) {
            timeRemaining = `${hours} hour${hours !== 1 ? 's' : ''} ${minutes} minute${minutes !== 1 ? 's' : ''}`;
        } else {
            timeRemaining = `${minutes} minute${minutes !== 1 ? 's' : ''}`;
        }
    } else {
        timeRemaining = 'Event has passed';
    }
    
    // Create event card element
    const eventCard = document.createElement('div');
    eventCard.className = 'event-card';
    eventCard.setAttribute('data-aos', 'fade-up');
    eventCard.setAttribute('data-event-id', event.id);
    
    // Create event card content
    eventCard.innerHTML = `
        <div class="event-header">
            <h3>${event.name}</h3>
            ${window.currentUserIsPrivileged ? `
            <div class="event-actions">
                <button class="delete-btn" title="Delete Event"><i class="fas fa-trash-alt"></i></button>
            </div>` : ''}
        </div>
        <div class="event-details">
            <p><i class="fas fa-map-marker-alt"></i> ${event.venue_name}</p>
            <p><i class="fas fa-calendar-alt"></i> ${formattedDate}</p>
            <p><i class="fas fa-clock"></i> ${formattedTime}${formattedEndTime ? ` - ${formattedEndTime}` : ''}</p>
            <p><i class="fas fa-hourglass-half"></i> ${timeRemaining}</p>
        </div>
        <div class="event-body">
            <p>${event.description || 'No description available.'}</p>
            <button class="btn primary-btn navigate-btn" data-venue-name="${event.venue_name}">
                <i class="fas fa-directions"></i> Navigate to Venue
            </button>
        </div>
    `;
    
    // Add event listener to navigate button
    eventCard.querySelector('.navigate-btn').addEventListener('click', (e) => {
        const venueName = e.target.getAttribute('data-venue-name') || 
                        e.target.closest('.navigate-btn').getAttribute('data-venue-name');
        navigateToVenue(venueName);
    });
    
    // Only add delete listener for privileged users
    if (window.currentUserIsPrivileged) {
        const deleteBtn = eventCard.querySelector('.delete-btn');
        if (deleteBtn) {
            deleteBtn.addEventListener('click', () => {
                deleteEvent(event.id);
            });
        }
    }
    
    return eventCard;
}

// Delete an event
async function deleteEvent(eventId) {
    try {
        // Find the event card
        const eventCard = document.querySelector(`.event-card[data-event-id="${eventId}"]`);
        if (!eventCard) {
            showNotification('Event not found.', 'error');
            return;
        }
        
        // Add a shake animation to confirm deletion intent
        eventCard.classList.add('shake-animation');
        
        // Confirm deletion
        const confirmed = await new Promise(resolve => {
            // Create a custom confirmation dialog
            const confirmDialog = document.createElement('div');
            confirmDialog.className = 'confirm-dialog';
            confirmDialog.innerHTML = `
                <div class="confirm-dialog-content">
                    <div class="confirm-dialog-header">
                        <i class="fas fa-trash-alt"></i>
                        <h4>Confirm Deletion</h4>
                    </div>
                    <p>Are you sure you want to delete this event?</p>
                    <div class="confirm-buttons">
                        <button class="btn cancel-btn">
                            <i class="fas fa-times"></i> Cancel
                        </button>
                        <button class="btn delete-confirm-btn">
                            <i class="fas fa-trash-alt"></i> Delete
                        </button>
                    </div>
                </div>
            `;
            
            document.body.appendChild(confirmDialog);
            
            // Animate dialog appearance
            setTimeout(() => {
                confirmDialog.classList.add('show');
                
                // Add event listeners to buttons
                confirmDialog.querySelector('.cancel-btn').addEventListener('click', () => {
                    confirmDialog.classList.remove('show');
                    setTimeout(() => confirmDialog.remove(), 300);
                    resolve(false);
                    // Remove shake animation
                    eventCard.classList.remove('shake-animation');
                });
                
                confirmDialog.querySelector('.delete-confirm-btn').addEventListener('click', () => {
                    confirmDialog.classList.remove('show');
                    setTimeout(() => confirmDialog.remove(), 300);
                    resolve(true);
                });
            }, 10);
        });
        
        if (!confirmed) {
            return;
        }
        
        // Store event position for confetti effect
        const rect = eventCard.getBoundingClientRect();
        
        // Apply deletion animation with fade out and slide up
        eventCard.classList.add('delete-animation');
        
        // Make the API request while the animation is running
        const response = await fetch(`/api/events/${eventId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Wait for animation to complete (500ms for animation + 100ms buffer)
            await new Promise(resolve => setTimeout(resolve, 600));
            
            // Add confetti effect for successful deletion
            createConfettiEffect(rect);
            
            // Remove event from the events array
            events = events.filter(event => event.id !== eventId);
            
            // Update the display
            displayEvents();
            
            // Show success notification with animation
            showNotification(data.message || 'Event deleted successfully!', 'success');
        } else {
            // If deletion failed, remove animation classes
            eventCard.classList.remove('delete-animation', 'shake-animation');
            showNotification(data.error || 'Failed to delete event.', 'error');
        }
    } catch (error) {
        console.error('Error deleting event:', error);
        
        // Reset any animations on error
        const eventCard = document.querySelector(`.event-card[data-event-id="${eventId}"]`);
        if (eventCard) {
            eventCard.classList.remove('delete-animation', 'shake-animation');
        }
        
        showNotification('Failed to delete event. Please try again later.', 'error');
    }
}

// Create confetti effect when an event is deleted
function createConfettiEffect(rect) {
    const confettiContainer = document.createElement('div');
    confettiContainer.className = 'confetti-container';
    confettiContainer.style.position = 'fixed';
    confettiContainer.style.top = `${rect.top}px`;
    confettiContainer.style.left = `${rect.left}px`;
    confettiContainer.style.width = `${rect.width}px`;
    confettiContainer.style.height = `${rect.height}px`;
    confettiContainer.style.pointerEvents = 'none';
    confettiContainer.style.zIndex = '9999';
    
    // Create confetti pieces with different shapes
    const colors = ['#4285f4', '#34a853', '#fbbc05', '#ea4335'];
    const shapes = ['circle', 'square', 'triangle'];
    
    for (let i = 0; i < 100; i++) {
        const confetti = document.createElement('div');
        confetti.className = 'confetti';
        
        // Randomly select shape
        const shape = shapes[Math.floor(Math.random() * shapes.length)];
        confetti.classList.add(`confetti-${shape}`);
        
        // Random color
        const color = colors[Math.floor(Math.random() * colors.length)];
        confetti.style.backgroundColor = color;
        
        // Random position
        confetti.style.left = `${Math.random() * 100}%`;
        confetti.style.top = `${Math.random() * 50}%`;
        
        // Random size
        const size = Math.random() * 8 + 5;
        confetti.style.width = `${size}px`;
        confetti.style.height = `${size}px`;
        
        // Random rotation and initial transform
        const rotation = Math.random() * 360;
        confetti.style.transform = `rotate(${rotation}deg)`;
        
        // Random animation duration and delay
        const duration = Math.random() * 2 + 1;
        const delay = Math.random() * 0.5;
        confetti.style.animation = `confetti-fall ${duration}s ${delay}s ease-out forwards, confetti-rotate ${duration * 0.5}s ${delay}s linear infinite`;
        
        confettiContainer.appendChild(confetti);
    }
    
    document.body.appendChild(confettiContainer);
    
    // Remove confetti after animation
    setTimeout(() => {
        confettiContainer.remove();
    }, 3000);
}

// Set up event listeners
function setupEventListeners() {
    // ✅ TAB SWITCHING FIX
    const upcomingTab = document.getElementById('upcoming-tab');
    const expiringTab = document.getElementById('expiring-tab');
    const addTab = document.getElementById('add-tab');

    const upcomingPane = document.getElementById('upcoming-events');
    const expiringPane = document.getElementById('expiring-events');
    const addPane = document.getElementById('add-event');

    function switchTab(activeTab, activePane) {
        // remove active styles
        document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
        document.querySelectorAll('.tab-pane').forEach(pane => pane.style.display = 'none');

        // set active
        activeTab.classList.add('active');
        activePane.style.display = 'block';
        
        // Update tabs container attribute for sliding animation
        const tabsContainer = activeTab.closest('.tabs');
        if (tabsContainer) {
            if (activeTab.id === 'upcoming-tab') tabsContainer.setAttribute('data-active-tab', 'upcoming-events');
            if (activeTab.id === 'expiring-tab') tabsContainer.setAttribute('data-active-tab', 'expiring-events');
            if (activeTab.id === 'add-tab') tabsContainer.setAttribute('data-active-tab', 'add-event');
        }
    }

    // listeners
    if (upcomingTab) {
        upcomingTab.addEventListener('click', () => {
            switchTab(upcomingTab, upcomingPane);
        });
    }

    if (expiringTab) {
        expiringTab.addEventListener('click', () => {
            switchTab(expiringTab, expiringPane);
        });
    }

    if (addTab && addPane) {
        addTab.addEventListener('click', () => {
            switchTab(addTab, addPane);
        });
    }

    // Event form submission
    const eventForm = document.getElementById('event-form');
    if (eventForm) {
        eventForm.addEventListener('submit', addEvent);
    }
    
    initializeEventForm();
    initializeTimePickers();
}

// Initialize time pickers with Flatpickr
function initializeTimePickers() {
    if (typeof flatpickr === 'undefined') {
        console.error('Flatpickr library not loaded');
        return;
    }
    
    // Get current time and round to nearest 30 minutes
    const now = new Date();
    const roundedMinutes = Math.ceil(now.getMinutes() / 30) * 30;
    now.setMinutes(roundedMinutes);
    now.setSeconds(0);
    
    // Default start time (1 hour from now)
    const startTime = new Date(now);
    startTime.setHours(startTime.getHours() + 1);
    
    // Default end time (2 hours from now)
    const endTime = new Date(now);
    endTime.setHours(endTime.getHours() + 2);
    
    // Initialize start time picker
    const startTimePicker = flatpickr('#event-start-time', {
        enableTime: true,
        noCalendar: true,
        dateFormat: 'H:i',
        time_24hr: true,
        minuteIncrement: 15,
        defaultHour: startTime.getHours(),
        defaultMinute: startTime.getMinutes(),
        onChange: function(selectedDates, dateStr) {
            // Update end time to be at least 30 minutes after start time
            const selectedTime = selectedDates[0];
            const minEndTime = new Date(selectedTime);
            minEndTime.setMinutes(minEndTime.getMinutes() + 30);
            
            const currentEndTime = endTimePicker.selectedDates[0];
            if (!currentEndTime || currentEndTime <= selectedTime) {
                endTimePicker.setDate(minEndTime);
            }
        }
    });
    
    // Initialize end time picker
    const endTimePicker = flatpickr('#event-end-time', {
        enableTime: true,
        noCalendar: true,
        dateFormat: 'H:i',
        time_24hr: true,
        minuteIncrement: 15,
        defaultHour: endTime.getHours(),
        defaultMinute: endTime.getMinutes()
    });
    
    // Store references to pickers for later use
    window.startTimePicker = startTimePicker;
    window.endTimePicker = endTimePicker;
}

// Initialize event form with default values
function initializeEventForm() {
    // Set min date for event date input to today
    const dateInput = document.getElementById('event-date');
    const today = new Date().toISOString().split('T')[0];
    dateInput.setAttribute('min', today);
    dateInput.value = today; // Set default to today
    
    // Clear name and description fields
    document.getElementById('event-name').value = '';
    document.getElementById('event-description').value = '';
    
    // Reset venue selection
    const venueSelect = document.getElementById('event-venue');
    venueSelect.selectedIndex = 0;
    
    // Reset time pickers if they exist
    if (window.startTimePicker && window.endTimePicker) {
        // Get current time and round to nearest 30 minutes
        const now = new Date();
        const roundedMinutes = Math.ceil(now.getMinutes() / 30) * 30;
        now.setMinutes(roundedMinutes);
        now.setSeconds(0);
        
        // Default start time (1 hour from now)
        const startTime = new Date(now);
        startTime.setHours(startTime.getHours() + 1);
        
        // Default end time (2 hours from now)
        const endTime = new Date(now);
        endTime.setHours(endTime.getHours() + 2);
        
        window.startTimePicker.setDate(startTime);
        window.endTimePicker.setDate(endTime);
    }
}

// Add a new event
async function addEvent(e) {
    e.preventDefault();
    
    // Get form values
    const name = document.getElementById('event-name').value;
    const venueName = document.getElementById('event-venue').value;
    const date = document.getElementById('event-date').value;
    const startTime = document.getElementById('event-start-time').value;
    const endTime = document.getElementById('event-end-time').value;
    const description = document.getElementById('event-description').value;
    
    // Validate form
    if (!name || !venueName || !date || !startTime || !endTime) {
        showNotification('Please fill in all required fields.', 'error');
        return;
    }
    
    // Validate that end time is after start time
    if (endTime <= startTime) {
        showNotification('End time must be after start time.', 'error');
        return;
    }
    
    // Create event object (using start time as the main time for compatibility)
    const eventData = {
        name,
        venue_name: venueName,
        date,
        time: startTime,
        end_time: endTime,
        description
    };
    
    try {
        // Show loading indicator
        const submitBtn = document.querySelector('#event-form button[type="submit"]');
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Adding event...';
        submitBtn.disabled = true;
        
        // Send POST request to add event
        const response = await fetch('/api/events', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(eventData)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Add new event to events array
            events.push(data);
            
            // Show success notification
            showNotification('Event added successfully!', 'success');
            
            // Reset form for next event
            initializeEventForm();
            
            // Update the display
            displayEvents();
            
            // Ask user if they want to add another event or view events
            const addAnother = confirm('Event added successfully! Would you like to add another event?');
            
            if (!addAnother) {
                // Switch to upcoming events tab with animation
                setTimeout(() => {
                    const upcomingBtn = document.getElementById('upcoming-tab');
                    if (upcomingBtn) upcomingBtn.click();
                }, 300);
            }
        } else {
            showNotification(data.error || 'Failed to add event.', 'error');
        }
    } catch (error) {
        console.error('Error adding event:', error);
        showNotification('Failed to add event. Please try again later.', 'error');
    } finally {
        // Reset button
        const submitBtn = document.querySelector('#event-form button[type="submit"]');
        submitBtn.innerHTML = '<i class="fas fa-plus-circle"></i> Add Event';
        submitBtn.disabled = false;
    }
}

// Show notification
function showNotification(message, type = 'info') {
    // Check if notification container exists
    let notificationContainer = document.querySelector('.notification-container');
    
    // Create container if it doesn't exist
    if (!notificationContainer) {
        notificationContainer = document.createElement('div');
        notificationContainer.className = 'notification-container';
        document.body.appendChild(notificationContainer);
    }
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    
    // Add icon based on notification type
    let icon = 'info-circle';
    if (type === 'success') icon = 'check-circle';
    if (type === 'error') icon = 'exclamation-circle';
    
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas fa-${icon}"></i>
            <p>${message}</p>
        </div>
        <button class="notification-close">&times;</button>
    `;
    
    // Add notification to container
    notificationContainer.appendChild(notification);
    
    // Add event listener to close button
    notification.querySelector('.notification-close').addEventListener('click', () => {
        notification.classList.add('fade-out');
        setTimeout(() => {
            notification.remove();
        }, 300);
    });
    
    // Auto-remove notification after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.classList.add('fade-out');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.remove();
                }
            }, 300);
        }
    }, 5000);
}

// Function to navigate to a venue on the map
function navigateToVenue(venueName) {
    // Check if global navigateToVenue function exists from map.js
    if (window.navigateToVenue && window.navigateToVenue !== navigateToVenue) {
        // Call the global function from map.js
        window.navigateToVenue(venueName);
        return;
    }
    
    // Fallback implementation if global function doesn't exist
    // Make sure map is visible
    const mapElement = document.getElementById('map');
    if (mapElement) {
        mapElement.style.display = 'block';
    }
    
    // Scroll to map section
    document.getElementById('map-section').scrollIntoView({ behavior: 'smooth' });
    
    // Use the predefined locations from script.js
    if (typeof predefinedLocations !== 'undefined' && predefinedLocations[venueName]) {
        const coordinates = predefinedLocations[venueName];
        
        // Initialize map if it doesn't exist
        if (typeof map === 'undefined' || map === null) {
            initMap();
        }
        
        // Center map on venue location
        map.setView(coordinates, 16);
        
        // Add marker for the venue
        if (venueMarker) {
            map.removeLayer(venueMarker);
        }
        
        venueMarker = L.marker(coordinates, {
            icon: L.divIcon({
                className: 'custom-marker',
                html: '<i class="fas fa-map-marker-alt"></i>',
                iconSize: [30, 30],
                iconAnchor: [15, 30]
            })
        }).addTo(map);
        
        // Add popup with venue name
        venueMarker.bindPopup(`<b>${venueName}</b>`).openPopup();
        
        // Show success notification
        showNotification(`Navigating to ${venueName}`, 'info');
    } else {
        console.error(`Venue location not found: ${venueName}`);
        showNotification(`Venue location not found: ${venueName}`, 'error');
    }
} 