/**
 * Admin Dashboard JavaScript
 * Handles all admin panel functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize admin dashboard
    initializeAdminDashboard();
    
    // Load initial data
    loadDashboardStats();
    loadRecentActivity();
    
    // Set up navigation
    setupNavigation();
    
    // Set up form handlers
    setupFormHandlers();
    
    // Set up sidebar toggle
    setupSidebarToggle();
});

/**
 * Initialize the admin dashboard
 */
function initializeAdminDashboard() {
    console.log('Admin Dashboard initialized');
}



/**
 * Set up navigation between sections
 */
function setupNavigation() {
    const navLinks = document.querySelectorAll('.nav-link[data-section]');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            const sectionName = this.getAttribute('data-section');
            showSection(sectionName);
            
            // Update active nav link
            navLinks.forEach(l => l.classList.remove('active'));
            this.classList.add('active');
            
            // Update page title
            const pageTitle = document.getElementById('page-title');
            if (pageTitle) {
                pageTitle.textContent = this.textContent.trim();
            }
        });
    });
}

/**
 * Show specific section and hide others
 */
function showSection(sectionName) {
    // Hide all sections
    const sections = document.querySelectorAll('.section');
    sections.forEach(section => {
        section.style.display = 'none';
    });
    
    // Show target section
    const targetSection = document.getElementById(`${sectionName}-section`);
    if (targetSection) {
        targetSection.style.display = 'block';
        
        // Load section-specific data
        switch(sectionName) {
            case 'users':
                loadUsers();
                break;
            case 'events':
                loadEvents();
                break;
            case 'campuses':
                loadCampuses();
                break;
            case 'conversations':
                loadConversations();
                break;
            case 'dashboard':
                loadDashboardStats();
                loadRecentActivity();
                break;
        }
    }
}

/**
 * Load dashboard statistics
 */
async function loadDashboardStats() {
    try {
        // Load users count
        const usersResponse = await fetch('/admin/api/users');
        if (usersResponse.ok) {
            const users = await usersResponse.json();
            document.getElementById('total-users').textContent = users.length;
        }
        
        // Load events count
        const eventsResponse = await fetch('/api/events');
        if (eventsResponse.ok) {
            const events = await eventsResponse.json();
            document.getElementById('total-events').textContent = events.length;
        }
        
        // Load conversations count
        const conversationsResponse = await fetch('/admin/api/conversations');
        if (conversationsResponse.ok) {
            const conversations = await conversationsResponse.json();
            document.getElementById('total-conversations').textContent = conversations.length;
        }
        
    } catch (error) {
        console.error('Error loading dashboard stats:', error);
    }
}

/**
 * Load recent activity
 */
async function loadRecentActivity() {
    try {
        const response = await fetch('/admin/api/recent-activity');
        const activityContainer = document.getElementById('recent-activity');
        
        if (response.ok) {
            const activities = await response.json();
            
            if (activities.length === 0) {
                activityContainer.innerHTML = '<p style="color: var(--gray-color); text-align: center; padding: 20px;">No recent activity found.</p>';
                return;
            }
            
            const activityHTML = activities.map(activity => `
                <div style="padding: 10px 0; border-bottom: 1px solid var(--border-color); display: flex; align-items: center; gap: 12px;">
                    <div style="width: 8px; height: 8px; border-radius: 50%; background: var(--primary-color);"></div>
                    <div>
                        <div style="font-weight: 500;">${activity.description}</div>
                        <div style="font-size: 0.8rem; color: var(--gray-color);">${formatDate(activity.timestamp)}</div>
                    </div>
                </div>
            `).join('');
            
            activityContainer.innerHTML = activityHTML;
        } else {
            activityContainer.innerHTML = '<p style="color: var(--danger-color); text-align: center; padding: 20px;">Failed to load recent activity.</p>';
        }
    } catch (error) {
        console.error('Error loading recent activity:', error);
        document.getElementById('recent-activity').innerHTML = '<p style="color: var(--danger-color); text-align: center; padding: 20px;">Error loading recent activity.</p>';
    }
}

/**
 * Load users data
 */
async function loadUsers() {
    try {
        const response = await fetch('/admin/api/users');
        const usersTable = document.getElementById('users-table');
        
        if (response.ok) {
            const users = await response.json();
            
            if (users.length === 0) {
                usersTable.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 20px; color: var(--gray-color);">No users found.</td></tr>';
                return;
            }
            
            const usersHTML = users.map(user => `
                <tr>
                    <td>
                        <div style="display: flex; align-items: center; gap: 10px;">
                            ${user.profile_picture ? 
                                `<img src="${user.profile_picture}" alt="${user.name}" style="width: 32px; height: 32px; border-radius: 50%;">` :
                                `<div style="width: 32px; height: 32px; border-radius: 50%; background: var(--primary-color); display: flex; align-items: center; justify-content: center; color: white; font-weight: 600; font-size: 0.8rem;">${user.name[0].toUpperCase()}</div>`
                            }
                            ${user.name}
                        </div>
                    </td>
                    <td>${user.email}</td>
                    <td>
                        <span class="badge ${user.is_admin ? 'badge-admin' : user.is_manager ? 'badge-manager' : 'badge-user'}">
                            ${user.is_admin ? 'Admin' : user.is_manager ? 'Manager' : 'User'}
                        </span>
                    </td>
                    <td>${user.preferred_campus ? user.preferred_campus.replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase()) : 'Not set'}</td>
                    <td>${user.last_login ? formatDate(user.last_login) : 'Never'}</td>
                    <td>
                        <div class="actions">
                            <button class="btn btn-sm btn-primary" onclick="editUser('${user.id}')">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn btn-sm btn-danger" onclick="deleteUser('${user.id}', '${user.name}')">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `).join('');
            
            usersTable.innerHTML = usersHTML;
        } else {
            usersTable.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 20px; color: var(--danger-color);">Failed to load users.</td></tr>';
        }
    } catch (error) {
        console.error('Error loading users:', error);
        document.getElementById('users-table').innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 20px; color: var(--danger-color);">Error loading users.</td></tr>';
    }
}

/**
 * Load events data
 */
async function loadEvents() {
    try {
        const response = await fetch('/admin/api/events');
        const eventsTable = document.getElementById('events-table');
        
        if (response.ok) {
            const events = await response.json();
            
            if (events.length === 0) {
                eventsTable.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 20px; color: var(--gray-color);">No events found.</td></tr>';
                return;
            }
            
            const eventsHTML = events.map(event => `
                <tr>
                    <td>${event.name}</td>
                    <td>${event.venue_name}</td>
                    <td>${formatDate(event.date)}</td>
                    <td>${event.start_time}${event.end_time ? ' - ' + event.end_time : ''}</td>
                    <td>${event.campus_id ? event.campus_id.replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase()) : 'Not set'}</td>
                    <td>${event.creator_name || 'Unknown'}</td>
                    <td>
                        <div class="actions">
                            <button class="btn btn-sm btn-primary" onclick="editEvent('${event.id}')">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn btn-sm btn-danger" onclick="deleteEvent('${event.id}', '${event.name}')">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `).join('');
            
            eventsTable.innerHTML = eventsHTML;
        } else {
            eventsTable.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 20px; color: var(--danger-color);">Failed to load events.</td></tr>';
        }
    } catch (error) {
        console.error('Error loading events:', error);
        document.getElementById('events-table').innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 20px; color: var(--danger-color);">Error loading events.</td></tr>';
    }
}

/**
 * Load campuses data
 */
async function loadCampuses() {
    try {
        const response = await fetch('/admin/api/campuses');
        const campusesTable = document.getElementById('campuses-table');
        
        if (response.ok) {
            const campuses = await response.json();
            
            if (campuses.length === 0) {
                campusesTable.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 20px; color: var(--gray-color);">No campuses found.</td></tr>';
                return;
            }
            
            const campusesHTML = campuses.map(campus => `
                <tr>
                    <td>${campus.name}</td>
                    <td>${campus.display_name}</td>
                    <td>${campus.center_coordinates ? campus.center_coordinates.join(', ') : 'Not set'}</td>
                    <td>${campus.timezone}</td>
                    <td>
                        <span class="badge ${campus.is_active ? 'badge-active' : 'badge-inactive'}">
                            ${campus.is_active ? 'Active' : 'Inactive'}
                        </span>
                    </td>
                    <td>
                        <div class="actions">
                            <button class="btn btn-sm btn-primary" onclick="editCampus('${campus.id}')">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn btn-sm btn-danger" onclick="deleteCampus('${campus.id}', '${campus.name}')">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `).join('');
            
            campusesTable.innerHTML = campusesHTML;
        } else {
            campusesTable.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 20px; color: var(--danger-color);">Failed to load campuses.</td></tr>';
        }
    } catch (error) {
        console.error('Error loading campuses:', error);
        document.getElementById('campuses-table').innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 20px; color: var(--danger-color);">Error loading campuses.</td></tr>';
    }
}

/**
 * Load conversations data
 */
async function loadConversations() {
    try {
        const response = await fetch('/admin/api/conversations');
        const conversationsTable = document.getElementById('conversations-table');
        
        if (response.ok) {
            const conversations = await response.json();
            
            if (conversations.length === 0) {
                conversationsTable.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 20px; color: var(--gray-color);">No conversations found.</td></tr>';
                return;
            }
            
            const conversationsHTML = conversations.map(conversation => `
                <tr>
                    <td>${conversation.user_name || 'Unknown User'}</td>
                    <td>${conversation.campus_context || 'Not set'}</td>
                    <td>${conversation.message_count || 0} messages</td>
                    <td>${formatDate(conversation.created_at)}</td>
                    <td>${formatDate(conversation.updated_at)}</td>
                    <td>
                        <div class="actions">
                            <button class="btn btn-sm btn-primary" onclick="viewConversation('${conversation.id}')">
                                <i class="fas fa-eye"></i>
                            </button>
                            <button class="btn btn-sm btn-danger" onclick="deleteConversation('${conversation.id}')">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `).join('');
            
            conversationsTable.innerHTML = conversationsHTML;
        } else {
            conversationsTable.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 20px; color: var(--danger-color);">Failed to load conversations.</td></tr>';
        }
    } catch (error) {
        console.error('Error loading conversations:', error);
        document.getElementById('conversations-table').innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 20px; color: var(--danger-color);">Error loading conversations.</td></tr>';
    }
}

/**
 * Set up form handlers
 */
function setupFormHandlers() {
    // User form
    const userForm = document.getElementById('user-form');
    if (userForm) {
        userForm.addEventListener('submit', handleUserSubmit);
    }
    
    // Event form
    const eventForm = document.getElementById('event-form');
    if (eventForm) {
        eventForm.addEventListener('submit', handleEventSubmit);
    }
    
    // Campus form
    const campusForm = document.getElementById('campus-form');
    if (campusForm) {
        campusForm.addEventListener('submit', handleCampusSubmit);
    }
}

/**
 * Handle user form submission
 */
async function handleUserSubmit(e) {
    e.preventDefault();
    
    const formData = {
        name: document.getElementById('user-name').value,
        email: document.getElementById('user-email').value,
        preferred_campus: document.getElementById('user-campus').value
    };
    
    try {
        const response = await fetch('/admin/api/users', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        if (response.ok) {
            const user = await response.json();
            // Assign role if not default 'user'
            const roleVal = document.getElementById('user-role').value;
            if (roleVal !== 'user') {
                await fetch(`/api/users/${user.id}/role`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ role: roleVal })
                });
            }
            showNotification('User created successfully!', 'success');
            closeUserModal();
            loadUsers();
            loadDashboardStats();
        } else {
            const error = await response.json();
            showNotification(error.error || 'Failed to create user', 'error');
        }
    } catch (error) {
        console.error('Error creating user:', error);
        showNotification('Error creating user', 'error');
    }
}

/**
 * Handle event form submission
 */
async function handleEventSubmit(e) {
    e.preventDefault();
    
    const formData = {
        name: document.getElementById('event-name').value,
        venue_name: document.getElementById('event-venue').value,
        date: document.getElementById('event-date').value,
        time: document.getElementById('event-start-time').value,
        end_time: document.getElementById('event-end-time').value,
        campus_id: document.getElementById('event-campus').value,
        description: document.getElementById('event-description').value
    };
    
    try {
        const response = await fetch('/api/events', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        if (response.ok) {
            showNotification('Event created successfully!', 'success');
            closeEventModal();
            loadEvents();
            loadDashboardStats();
        } else {
            const error = await response.json();
            showNotification(error.message || 'Failed to create event', 'error');
        }
    } catch (error) {
        console.error('Error creating event:', error);
        showNotification('Error creating event', 'error');
    }
}

/**
 * Handle campus form submission
 */
async function handleCampusSubmit(e) {
    e.preventDefault();
    
    const formData = {
        id: document.getElementById('campus-id').value,
        name: document.getElementById('campus-name').value,
        display_name: document.getElementById('campus-display-name').value,
        center_latitude: parseFloat(document.getElementById('campus-lat').value),
        center_longitude: parseFloat(document.getElementById('campus-lng').value),
        timezone: document.getElementById('campus-timezone').value
    };
    
    try {
        const response = await fetch('/admin/api/campuses', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        if (response.ok) {
            showNotification('Campus created successfully!', 'success');
            closeCampusModal();
            loadCampuses();
            loadDashboardStats();
        } else {
            const error = await response.json();
            showNotification(error.message || 'Failed to create campus', 'error');
        }
    } catch (error) {
        console.error('Error creating campus:', error);
        showNotification('Error creating campus', 'error');
    }
}

/**
 * Modal functions
 */
function openUserModal() {
    document.querySelector('#user-modal .modal-title').textContent = 'Add User';
    document.getElementById('user-modal').style.display = 'block';
}

function closeUserModal() {
    document.getElementById('user-modal').style.display = 'none';
    document.getElementById('user-form').reset();
    const idField = document.getElementById('campus-id');
    if (idField) idField.disabled = false;
}

function openEventModal() {
    document.querySelector('#event-modal .modal-title').textContent = 'Add Event';
    document.getElementById('event-modal').style.display = 'block';
}

function closeEventModal() {
    document.getElementById('event-modal').style.display = 'none';
    document.getElementById('event-form').reset();
}

function openCampusModal() {
    document.querySelector('#campus-modal .modal-title').textContent = 'Add Campus';
    document.getElementById('campus-modal').style.display = 'block';
}

function closeCampusModal() {
    document.getElementById('campus-modal').style.display = 'none';
    document.getElementById('campus-form').reset();
    const idField = document.getElementById('campus-id');
    if (idField) idField.disabled = false;
}

/**
 * Delete functions
 */
async function deleteUser(userId, userName) {
    if (!confirm(`Are you sure you want to delete user "${userName}"?`)) {
        return;
    }
    
    try {
        const response = await fetch(`/admin/api/users/${userId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showNotification('User deleted successfully!', 'success');
            loadUsers();
            loadDashboardStats();
        } else {
            const error = await response.json();
            showNotification(error.message || 'Failed to delete user', 'error');
        }
    } catch (error) {
        console.error('Error deleting user:', error);
        showNotification('Error deleting user', 'error');
    }
}

async function deleteEvent(eventId, eventName) {
    if (!confirm(`Are you sure you want to delete event "${eventName}"?`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/events/${eventId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showNotification('Event deleted successfully!', 'success');
            loadEvents();
            loadDashboardStats();
        } else {
            const error = await response.json();
            showNotification(error.message || 'Failed to delete event', 'error');
        }
    } catch (error) {
        console.error('Error deleting event:', error);
        showNotification('Error deleting event', 'error');
    }
}

async function deleteCampus(campusId, campusName) {
    if (!confirm(`Are you sure you want to delete campus "${campusName}"?`)) {
        return;
    }
    
    try {
        const response = await fetch(`/admin/api/campuses/${campusId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showNotification('Campus deleted successfully!', 'success');
            loadCampuses();
            loadDashboardStats();
        } else {
            const error = await response.json();
            showNotification(error.message || 'Failed to delete campus', 'error');
        }
    } catch (error) {
        console.error('Error deleting campus:', error);
        showNotification('Error deleting campus', 'error');
    }
}

async function deleteConversation(conversationId) {
    if (!confirm('Are you sure you want to delete this conversation?')) {
        return;
    }
    
    try {
        const response = await fetch(`/admin/api/conversations/${conversationId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showNotification('Conversation deleted successfully!', 'success');
            loadConversations();
            loadDashboardStats();
        } else {
            const error = await response.json();
            showNotification(error.message || 'Failed to delete conversation', 'error');
        }
    } catch (error) {
        console.error('Error deleting conversation:', error);
        showNotification('Error deleting conversation', 'error');
    }
}

/**
 * Edit functions — fetch current record, populate modal, switch submit to PUT
 */
async function editUser(userId) {
    try {
        const res = await fetch(`/admin/api/users/${userId}`);
        if (!res.ok) { showNotification('Failed to load user data', 'error'); return; }
        const user = await res.json();

        document.getElementById('user-name').value = user.name || '';
        document.getElementById('user-email').value = user.email || '';
        document.getElementById('user-role').value = user.role === 'admin' ? 'admin' : (user.role === 'manager' ? 'manager' : 'user');
        document.getElementById('user-campus').value = user.preferred_campus || 'amrita-chennai';

        const form = document.getElementById('user-form');
        const newForm = form.cloneNode(true);
        form.parentNode.replaceChild(newForm, form);
        newForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const data = {
                name: document.getElementById('user-name').value,
                preferred_campus: document.getElementById('user-campus').value
            };
            const roleVal = document.getElementById('user-role').value;
            const roleRes = await fetch(`/api/users/${userId}/role`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ role: roleVal })
            });
            const updateRes = await fetch(`/admin/api/users/${userId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            if (roleRes.ok || updateRes.ok) {
                showNotification('User updated successfully!', 'success');
                closeUserModal();
                loadUsers();
            } else {
                const err = await updateRes.json().catch(() => ({}));
                showNotification(err.error || 'Failed to update user', 'error');
            }
        });

        document.querySelector('#user-modal .modal-title').textContent = 'Edit User';
        openUserModal();
    } catch (err) {
        console.error('editUser error:', err);
        showNotification('Error loading user', 'error');
    }
}

async function editEvent(eventId) {
    try {
        const res = await fetch(`/api/events/${eventId}`);
        if (!res.ok) { showNotification('Failed to load event data', 'error'); return; }
        const event = await res.json();

        document.getElementById('event-name').value = event.name || '';
        document.getElementById('event-venue').value = event.venue_name || '';
        document.getElementById('event-date').value = event.date || '';
        document.getElementById('event-start-time').value = event.start_time || '';
        document.getElementById('event-end-time').value = event.end_time || '';
        document.getElementById('event-campus').value = event.campus_id || 'amrita-chennai';
        document.getElementById('event-description').value = event.description || '';

        const form = document.getElementById('event-form');
        const newForm = form.cloneNode(true);
        form.parentNode.replaceChild(newForm, form);
        newForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const data = {
                name: document.getElementById('event-name').value,
                venue_name: document.getElementById('event-venue').value,
                date: document.getElementById('event-date').value,
                time: document.getElementById('event-start-time').value,
                end_time: document.getElementById('event-end-time').value,
                campus_id: document.getElementById('event-campus').value,
                description: document.getElementById('event-description').value
            };
            const updateRes = await fetch(`/api/events/${eventId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            if (updateRes.ok) {
                showNotification('Event updated successfully!', 'success');
                closeEventModal();
                loadEvents();
            } else {
                const err = await updateRes.json().catch(() => ({}));
                showNotification(err.error || 'Failed to update event', 'error');
            }
        });

        document.querySelector('#event-modal .modal-title').textContent = 'Edit Event';
        openEventModal();
    } catch (err) {
        console.error('editEvent error:', err);
        showNotification('Error loading event', 'error');
    }
}

async function editCampus(campusId) {
    try {
        const res = await fetch(`/admin/api/campuses/${campusId}`);
        if (!res.ok) { showNotification('Failed to load campus data', 'error'); return; }
        const campus = await res.json();

        document.getElementById('campus-id').value = campus.id || '';
        document.getElementById('campus-id').disabled = true;
        document.getElementById('campus-name').value = campus.name || '';
        document.getElementById('campus-display-name').value = campus.display_name || '';
        const coords = campus.center_coordinates || [0, 0];
        document.getElementById('campus-lat').value = coords[0];
        document.getElementById('campus-lng').value = coords[1];
        document.getElementById('campus-timezone').value = campus.timezone || 'UTC';

        const form = document.getElementById('campus-form');
        const newForm = form.cloneNode(true);
        form.parentNode.replaceChild(newForm, form);
        newForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const data = {
                name: document.getElementById('campus-name').value,
                display_name: document.getElementById('campus-display-name').value,
                center_latitude: parseFloat(document.getElementById('campus-lat').value),
                center_longitude: parseFloat(document.getElementById('campus-lng').value),
                timezone: document.getElementById('campus-timezone').value
            };
            const updateRes = await fetch(`/admin/api/campuses/${campusId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            if (updateRes.ok) {
                showNotification('Campus updated successfully!', 'success');
                closeCampusModal();
                loadCampuses();
            } else {
                const err = await updateRes.json().catch(() => ({}));
                showNotification(err.error || 'Failed to update campus', 'error');
            }
        });

        document.querySelector('#campus-modal .modal-title').textContent = 'Edit Campus';
        openCampusModal();
    } catch (err) {
        console.error('editCampus error:', err);
        showNotification('Error loading campus', 'error');
    }
}

function viewConversation(conversationId) {
    showNotification('View conversation functionality coming soon!', 'info');
}

/**
 * Utility functions
 */
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function showNotification(message, type = 'info') {
    // Remove existing notifications
    const existingNotifications = document.querySelectorAll('.notification');
    existingNotifications.forEach(notification => notification.remove());
    
    // Create new notification
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (document.body.contains(notification)) {
            notification.remove();
        }
    }, 5000);
}

// Close modals when clicking outside
window.addEventListener('click', function(e) {
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });
});

/**
 * Setup mobile sidebar toggle
 */
function setupSidebarToggle() {
    const sidebarToggle = document.getElementById('admin-menu-toggle');
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.getElementById('admin-sidebar-overlay');
    const navLinks = document.querySelectorAll('.nav-link');

    if (!sidebarToggle || !sidebar || !overlay) return;

    function openSidebar() {
        sidebar.classList.add('open');
        overlay.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    function closeSidebar() {
        sidebar.classList.remove('open');
        overlay.classList.remove('active');
        document.body.style.overflow = '';
    }

    sidebarToggle.addEventListener('click', openSidebar);
    overlay.addEventListener('click', closeSidebar);

    // Close sidebar when clicking a navigation link on mobile
    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            if (window.innerWidth <= 768) {
                closeSidebar();
            }
        });
    });
}