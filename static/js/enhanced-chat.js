/**
 * Enhanced Chat Widget for Campus Explorer AI Assistant
 * Provides intelligent chat interface with typing indicators, message history, and context awareness
 */

class EnhancedChatWidget {
    constructor() {
        this.chatToggle = document.getElementById('chat-toggle');
        this.chatWidget = document.getElementById('chat-widget');
        this.chatClose = document.getElementById('chat-close');
        this.chatForm = document.getElementById('chat-form');
        this.chatInput = document.getElementById('chat-input');
        this.chatMessages = document.getElementById('chat-messages');
        
        this.isOpen = false;
        this.isTyping = false;
        this.messageHistory = [];
        this.currentContext = this.getUserContext();
        
        this.init();
    }
    
    init() {
        if (!this.chatToggle || !this.chatWidget) {
            console.warn('Chat widget elements not found');
            return;
        }
        
        this.setupEventListeners();
        this.loadWelcomeMessage();
        this.setupKeyboardShortcuts();
    }
    
    setupEventListeners() {
        // Toggle chat widget
        this.chatToggle.addEventListener('click', () => {
            this.toggleChat();
        });
        
        // Close chat widget
        if (this.chatClose) {
            this.chatClose.addEventListener('click', () => {
                this.closeChat();
            });
        }
        
        // Handle form submission
        if (this.chatForm) {
            this.chatForm.addEventListener('submit', (e) => {
                this.handleSubmit(e);
            });
        }
        
        // Handle input events
        if (this.chatInput) {
            this.chatInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.handleSubmit(e);
                }
            });
            
            // Auto-resize input
            this.chatInput.addEventListener('input', () => {
                this.adjustInputHeight();
            });
        }
        
        // Close on outside click
        document.addEventListener('click', (e) => {
            if (this.isOpen && !this.chatWidget.contains(e.target) && !this.chatToggle.contains(e.target)) {
                this.closeChat();
            }
        });
    }
    
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + K to open chat
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                this.openChat();
                this.chatInput.focus();
            }
            
            // Escape to close chat
            if (e.key === 'Escape' && this.isOpen) {
                this.closeChat();
            }
        });
    }
    
    getUserContext() {
        // Get user context from page or localStorage
        const context = {
            campus: this.getCampusFromSelector() || 'amrita-chennai',
            timestamp: new Date().toISOString()
        };
        
        // Add user info if available
        const userInfo = this.getUserInfo();
        if (userInfo) {
            context.user_name = userInfo.name;
            context.user_id = userInfo.id;
        }
        
        return context;
    }
    
    getCampusFromSelector() {
        const campusSelect = document.getElementById('campus-select');
        return campusSelect ? campusSelect.value : null;
    }
    
    getUserInfo() {
        // Try to get user info from page elements
        const userInfoElement = document.querySelector('.user-info');
        if (userInfoElement) {
            const nameElement = userInfoElement.querySelector('[data-user-name]');
            const idElement = userInfoElement.querySelector('[data-user-id]');
            
            if (nameElement || idElement) {
                return {
                    name: nameElement ? nameElement.textContent.trim() : 'User',
                    id: idElement ? idElement.dataset.userId : null
                };
            }
        }
        
        return null;
    }
    
    loadWelcomeMessage() {
        const welcomeMessage = this.getWelcomeMessage();
        this.addMessage(welcomeMessage, 'bot');
    }
    
    getWelcomeMessage() {
        const campus = this.currentContext.campus.replace('-', ' ').replace(/\b\w/g, l => l.toUpperCase());
        const userName = this.currentContext.user_name || 'there';
        
        return `Hi ${userName}! I'm your enhanced Campus Explorer AI assistant for ${campus}. I can help you with:

🗺️ **Navigation** - "How do I get to the library?"
📅 **Events** - "What's happening today?"
🏢 **Facilities** - "Where is the canteen?"
🎓 **Campus Info** - "Tell me about this campus"

Just ask me anything in natural language!`;
    }
    
    toggleChat() {
        if (this.isOpen) {
            this.closeChat();
        } else {
            this.openChat();
        }
    }
    
    openChat() {
        this.chatWidget.style.display = 'flex';
        this.isOpen = true;
        this.chatToggle.style.transform = 'scale(0.9)';
        
        // Focus input after animation
        setTimeout(() => {
            if (this.chatInput) {
                this.chatInput.focus();
            }
        }, 100);
        
        // Update context when opening
        this.currentContext = this.getUserContext();
    }
    
    closeChat() {
        this.chatWidget.style.display = 'none';
        this.isOpen = false;
        this.chatToggle.style.transform = 'scale(1)';
    }
    
    async handleSubmit(e) {
        e.preventDefault();
        
        const text = this.chatInput.value.trim();
        if (!text || this.isTyping) return;
        
        // Add user message
        this.addMessage(text, 'user');
        this.messageHistory.push({ role: 'user', content: text });
        
        // Clear input
        this.chatInput.value = '';
        this.adjustInputHeight();
        
        // Show typing indicator
        this.showTypingIndicator();
        
        try {
            // Send to AI assistant
            const response = await this.sendToAI(text);
            
            // Hide typing indicator
            this.hideTypingIndicator();
            
            // Add AI response
            this.addMessage(response, 'bot');
            this.messageHistory.push({ role: 'assistant', content: response });
            
        } catch (error) {
            console.error('Chat error:', error);
            this.hideTypingIndicator();
            
            const errorMessage = 'I apologize, but I\'m experiencing some technical difficulties. Please try again in a moment.';
            this.addMessage(errorMessage, 'bot');
        }
    }
    
    async sendToAI(message) {
        // Send the last 10 messages as history for multi-turn context
        const history = this.messageHistory.slice(-10);

        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                context: this.currentContext,
                history: history
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        return data.reply || "I apologize, but I couldn't process your request.";
    }
    
    addMessage(text, from = 'bot') {
        const wrapper = document.createElement('div');
        wrapper.style.marginBottom = '12px';
        wrapper.style.animation = 'fadeInUp 0.3s ease-out';
        
        const bubble = document.createElement('div');
        bubble.style.maxWidth = '85%';
        bubble.style.padding = '10px 12px';
        bubble.style.borderRadius = '12px';
        bubble.style.display = 'inline-block';
        bubble.style.wordWrap = 'break-word';
        bubble.style.lineHeight = '1.4';
        
        if (from === 'user') {
            wrapper.style.textAlign = 'right';
            bubble.style.background = 'var(--primary-color)';
            bubble.style.color = '#ffffff';
            bubble.style.borderBottomRightRadius = '4px';
            bubble.textContent = text;
        } else {
            wrapper.style.textAlign = 'left';
            bubble.style.background = '#e5e7eb';
            bubble.style.color = '#111827';
            bubble.style.borderBottomLeftRadius = '4px';
            
            // Support markdown-like formatting for bot messages
            bubble.innerHTML = this.formatBotMessage(text);
        }
        
        wrapper.appendChild(bubble);
        this.chatMessages.appendChild(wrapper);
        this.scrollToBottom();
    }
    
    formatBotMessage(text) {
        // Simple markdown-like formatting
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') // Bold
            .replace(/\*(.*?)\*/g, '<em>$1</em>') // Italic
            .replace(/🗺️|📅|🏢|🎓/g, '<span style="font-size: 1.1em;">$&</span>') // Emojis
            .replace(/\n/g, '<br>'); // Line breaks
    }
    
    showTypingIndicator() {
        if (this.isTyping) return;
        
        this.isTyping = true;
        
        const wrapper = document.createElement('div');
        wrapper.id = 'typing-indicator';
        wrapper.style.marginBottom = '12px';
        wrapper.style.textAlign = 'left';
        
        const bubble = document.createElement('div');
        bubble.style.maxWidth = '85%';
        bubble.style.padding = '10px 12px';
        bubble.style.borderRadius = '12px';
        bubble.style.background = '#e5e7eb';
        bubble.style.color = '#6b7280';
        bubble.style.display = 'inline-block';
        bubble.style.borderBottomLeftRadius = '4px';
        
        // Typing animation
        bubble.innerHTML = `
            <div style="display: flex; align-items: center; gap: 4px;">
                <span>AI is typing</span>
                <div style="display: flex; gap: 2px;">
                    <div style="width: 4px; height: 4px; border-radius: 50%; background: #6b7280; animation: typing-dot 1.4s infinite ease-in-out;"></div>
                    <div style="width: 4px; height: 4px; border-radius: 50%; background: #6b7280; animation: typing-dot 1.4s infinite ease-in-out 0.2s;"></div>
                    <div style="width: 4px; height: 4px; border-radius: 50%; background: #6b7280; animation: typing-dot 1.4s infinite ease-in-out 0.4s;"></div>
                </div>
            </div>
        `;
        
        wrapper.appendChild(bubble);
        this.chatMessages.appendChild(wrapper);
        this.scrollToBottom();
    }
    
    hideTypingIndicator() {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) {
            indicator.remove();
        }
        this.isTyping = false;
    }
    
    adjustInputHeight() {
        if (!this.chatInput) return;
        
        this.chatInput.style.height = 'auto';
        const maxHeight = 100; // Max height in pixels
        const newHeight = Math.min(this.chatInput.scrollHeight, maxHeight);
        this.chatInput.style.height = newHeight + 'px';
    }
    
    scrollToBottom() {
        if (this.chatMessages) {
            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        }
    }
    
    // Public methods for external use
    sendMessage(message) {
        if (this.chatInput) {
            this.chatInput.value = message;
            this.handleSubmit(new Event('submit'));
        }
    }
    
    clearChat() {
        if (this.chatMessages) {
            this.chatMessages.innerHTML = '';
            this.messageHistory = [];
            this.loadWelcomeMessage();
        }
    }
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes typing-dot {
        0%, 60%, 100% {
            transform: scale(1);
            opacity: 0.5;
        }
        30% {
            transform: scale(1.2);
            opacity: 1;
        }
    }
    
    #chat-input {
        resize: none;
        overflow-y: auto;
        min-height: 20px;
        max-height: 100px;
    }
    
    #chat-messages {
        scroll-behavior: smooth;
    }
    
    .chat-message-link {
        color: var(--primary-color);
        text-decoration: underline;
        cursor: pointer;
    }
    
    .chat-message-link:hover {
        color: var(--secondary-color);
    }
`;
document.head.appendChild(style);

// Initialize enhanced chat widget when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize if chat elements exist
    if (document.getElementById('chat-toggle')) {
        window.enhancedChat = new EnhancedChatWidget();
        
        // Global function to send messages programmatically
        window.sendChatMessage = function(message) {
            if (window.enhancedChat) {
                window.enhancedChat.openChat();
                setTimeout(() => {
                    window.enhancedChat.sendMessage(message);
                }, 300);
            }
        };
        
        // Global function to clear chat
        window.clearChat = function() {
            if (window.enhancedChat) {
                window.enhancedChat.clearChat();
            }
        };
    }
});